import time
import requests
import json
import os

model_name = "gemma4:latest"
url = "http://localhost:11434/api/generate"
payload = {
    "model": model_name,
    "prompt": "Explain the concept of local context assembly in AI agent architectures in 100 words.",
    "stream": False
}

print(f"Benchmarking local model '{model_name}' via Ollama...")
start_time = time.time()
try:
    response = requests.post(url, json=payload, timeout=60)
    elapsed = time.time() - start_time
    if response.status_code == 200:
        res_data = response.json()
        response_text = res_data.get("response", "")
        eval_count = res_data.get("eval_count", 0)  # number of tokens generated
        prompt_eval_count = res_data.get("prompt_eval_count", 0)
        
        # Calculate tokens per second
        tps = eval_count / elapsed if elapsed > 0 else 0
        
        report = f"""# Local AI Benchmark: {model_name}

* **Date:** 2026-06-11
* **Engine:** Ollama (Local)
* **Model:** {model_name}

## Latency & Throughput Metrics
* **Total Elapsed Time:** {elapsed:.2f} seconds
* **Prompt Tokens Evaluated:** {prompt_eval_count} tokens
* **Output Tokens Generated:** {eval_count} tokens
* **Tokens Per Second (TPS):** {tps:.2f} t/s

## Model Response Sample
\"\"\"{response_text}\"\"\"
"""
        os.makedirs("docs/research", exist_ok=True)
        report_path = "docs/research/local_benchmarks.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Benchmark completed successfully. Report saved to {report_path}")
        print(f"Tokens/sec: {tps:.2f} t/s, Latency: {elapsed:.2f}s")
    else:
        print(f"Ollama returned error status: {response.status_code}")
except Exception as e:
    print(f"Failed to benchmark Ollama: {e}")
