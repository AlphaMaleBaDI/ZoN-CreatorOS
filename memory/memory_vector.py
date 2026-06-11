import os
import json
import numpy as np
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from PIL import Image # type: ignore
import torch
from transformers.models.clip import CLIPProcessor, CLIPModel
import traceback
import logging

logger = logging.getLogger(__name__)

# --- Models & Paths ---
FAISS_PATH = os.path.join(os.path.dirname(__file__), "faiss_index")
VISUAL_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "visual_registry.json")
EMBEDDINGS_DIR = os.path.join(os.path.dirname(__file__), "visual_embeddings")

os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

_embedding_model = None
_clip_model = None
_clip_processor = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        logger.info("📡 Loading Embedding Model (MiniLM)...")
        _embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return _embedding_model

def get_clip_models():
    global _clip_model, _clip_processor
    if _clip_model is None or _clip_processor is None:
        logger.info("🔭 Loading CLIP Models (Text + Visual)...")
        _clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        _clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    return _clip_model, _clip_processor

def get_visual_registry():
    if os.path.exists(VISUAL_REGISTRY_PATH):
        try:
            if os.path.getsize(VISUAL_REGISTRY_PATH) == 0:
                return {}
            with open(VISUAL_REGISTRY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, EOFError) as e:
            logger.warning(f"⚠️ Corrupt visual registry, resetting. Reason: {e}")
            return {}
    return {}

def save_visual_registry(registry):
    with open(VISUAL_REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=4)
        _clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch16")
        res = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch16")
        _clip_processor = res[0] if isinstance(res, tuple) else res
    return _clip_model, _clip_processor


def get_vector_store():
    if os.path.exists(FAISS_PATH):
        return FAISS.load_local(FAISS_PATH, get_embedding_model(), allow_dangerous_deserialization=True)
    return None

def embed_image(image_path):
    model, processor = get_clip_models()
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    pixel_values = inputs["pixel_values"] if isinstance(inputs, dict) else getattr(inputs, "pixel_values", None)
    if pixel_values is None:
        raise ValueError("Could not extract pixel_values tensor from processor output.")
    with torch.no_grad():
        image_features = model.get_image_features(pixel_values=pixel_values)
    return image_features[0].cpu().numpy()

def add_to_memory(texts, image_paths=None):
    if not texts and not image_paths:
        return

    try:
        db = None
        if os.path.exists(FAISS_PATH):
            logger.info(f"🧠 Loading existing Vector Store from {FAISS_PATH}...")
            db = FAISS.load_local(FAISS_PATH, get_embedding_model(), allow_dangerous_deserialization=True)
            if texts:
                logger.info(f"➕ Adding {len(texts)} texts...")
                db.add_texts(texts)
        else:
            if texts:
                logger.info(f"🆕 Creating new Vector Store with {len(texts)} texts...")
                db = FAISS.from_texts(texts, get_embedding_model())
            else:
                logger.warning("⚠️ No texts provided to create a new Vector Store.")
                return

        if db:
            logger.info(f"💾 Saving FAISS index to: {FAISS_PATH}")
            db.save_local(FAISS_PATH)
            logger.info("✅ FAISS index saved successfully.")
            
    except Exception as e:
        logger.error(f"❌ Failed to add to vector store: {e}")
        traceback.print_exc()

    # Multimodal Ingestion
    if image_paths:
        registry = get_visual_registry()
        for img_path in image_paths:
            try:
                img_path_abs = os.path.abspath(img_path)
                logger.info(f"🎨 Embedding image: {img_path_abs}")
                img_emb = embed_image(img_path_abs)
                
                # Save embedding to a separate file
                safe_name = "".join([c if c.isalnum() else "_" for c in img_path_abs])
                emb_path = os.path.join(EMBEDDINGS_DIR, f"{safe_name}.npy")
                np.save(emb_path, img_emb)
                
                # Update registry
                registry[img_path_abs] = emb_path
            except Exception as e:
                logger.error(f"❌ Failed to embed image {img_path}: {e}")
        
        save_visual_registry(registry)

def query_memory(query, k=5):
    db = get_vector_store()
    if not db:
        logger.warning("⚠️ Vector store does not exist yet. Run ingestion first.")
        return []
    return db.similarity_search(query, k=k)

def query_visual_memory(query, k=3):
    """
    Multimodal search: find images that match a text query using CLIP.
    """
    try:
        registry = get_visual_registry()
        if not registry:
            return []
            
        model, processor = get_clip_models()
        logger.info(f"🔭 Searching visual memory for: '{query}'")
        
        # Embed query text
        inputs = processor(text=[query], return_tensors="pt", padding=True)
        with torch.no_grad():
            text_features = model.get_text_features(**inputs)
        text_emb = text_features[0].cpu().numpy()
        
        # Normalize
        text_emb = text_emb / np.linalg.norm(text_emb)
        
        results = []
        for img_path, emb_file in registry.items():
            if not os.path.exists(emb_file):
                continue
            img_emb = np.load(emb_file)
            img_emb = img_emb / np.linalg.norm(img_emb)
            
            score = float(np.dot(text_emb, img_emb))
            results.append({"path": img_path, "score": score})
            
        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]
    except Exception as e:
        logger.error(f"❌ Visual search failed: {e}")
        traceback.print_exc()
        return []

# Add this function for pinpointed error logging
def safe_open(path, mode, *args, **kwargs):
    logger.debug(f"[DEBUG] Attempting to open: {path} with mode: {mode}")
    try:
        return open(path, mode, *args, **kwargs)
    except Exception as e:
        logger.error(f"[ERROR] Exception opening {path} with mode {mode}: {e}")
        traceback.print_exc()
        raise