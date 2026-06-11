# Local AI Benchmark: gemma4:latest

* **Date:** 2026-06-11
* **Engine:** Ollama (Local)
* **Model:** gemma4:latest (9.6 GB)

## Latency & Setup Observations
* **Model Loading Timeout:** The first model load requested via `/api/generate` exceeded the 60-second execution threshold (resulting in a ReadTimeout). 
* **TCO Implication:** Large models (e.g., 9GB+) running purely locally on standard CPU/GPU cores suffer from heavy first-token latency (time-to-first-token) due to memory loading bottlenecks.
* **Hybrid Architecture Justification (ADR-003):** This latency bottleneck validates our hybrid decision:
  * Lightweight models (e.g., 1B–4B parameters) should run locally on the **Ryzen AI NPU** to keep note retrieval/summarization fast.
  * Larger reasoning jobs (e.g., multi-agent orchestrations, project artifact generation) must be routed to **AMD Instinct GPUs** (via our cloud compute path) to maintain interactive speeds.
