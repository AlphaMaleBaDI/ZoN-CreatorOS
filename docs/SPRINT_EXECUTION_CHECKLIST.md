# ZoN CreatorOS - Sprint Execution Checklist

This document serves as the absolute target list of deliverables for the build sprint starting July 6. Every day must focus exclusively on checking off these execution milestones.

---

## 📦 Phase 1.2: Memory Engine
- [ ] Implement isolated workspace scoping (`WorkspaceScope`, `ProjectScope`, `MemoryScope` filters)
- [ ] Save profile
- [ ] Load profile
- [ ] Update profile
- [ ] Profile retrieval tests
- [ ] Implement FAISS vector storage (embedding indexing & search retrieval)
- [ ] Add unit tests for workspace memory query insulation

---

## 🧠 Phase 1.3: Context Assembly
- [ ] Implement `ContextObject` instantiations
- [ ] Aggregate vector search memories based on tags & tags relations
- [ ] Aggregate profile settings (brand voice, style preferences)
- [ ] Integrate Vibra state history calculations
- [ ] Add unit tests for context output fidelity

---

## 🤖 Phase 1.4: Orchestrator Agent
- [ ] Implement master router mapping intent to specialized execution logic
- [ ] Set up Planner Agent contract routing (roadmaps, timelines)
- [ ] Set up Research Agent contract routing (lookups)
- [ ] Set up Artifact Agent contract routing (save/load output JSON structures)
- [ ] Add agent integration tests
- [ ] End-to-end demo pipeline test (Upload Notes -> Upload Lyrics -> Release Objective -> Context Assembly -> Orchestrator -> Artifact -> Confidence Score)

---

## 🎯 Demo Scenario Validation
- [ ] Upload notes file successfully
- [ ] Upload lyrics file successfully
- [ ] Accept release objective text inputs
- [ ] Generate parsed JSON deliverables (Artifacts Layer)
- [ ] Display references to original memory nodes
- [ ] Chart creative state (Vibra) history shifts
- [ ] Verify confidence score outputs
