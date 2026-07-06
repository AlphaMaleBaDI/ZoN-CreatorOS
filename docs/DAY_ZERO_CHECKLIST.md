# ZoN CreatorOS Day Zero Checklist

## July 5 — AMD Credit Claim

- [ ] Claim the **$100 AMD Instinct Cloud hackathon credits**.
- [ ] Verify SSH/API access to AMD Instinct GPU clusters.
- [ ] Install/verify ROCm/HIP SDK if running on local AMD hardware (see `docs/ENVIRONMENT_STATUS.md`).

## July 6 — Sprint Launch

### Pre-Flight Verification

- [ ] Run test suite locally using `.venv\Scripts\python -m pytest` to verify 100% green status.
- [ ] Confirm local Ollama service is up and running.

### Repository Activation

- [ ] Create public GitHub repository for `ZoN-CreatorOS`.
- [ ] Add remote link to local git workspace.
- [ ] Push local `develop` branch to GitHub.
- [ ] Tag and push the preseason state: `git tag preseason-freeze-v1 && git push origin preseason-freeze-v1`

### Sprint Phase 1.2 Start

- [ ] Begin Vertical Slice 1 — Memory & Profile Foundation (see `docs/SPRINT_EXECUTION_CHECKLIST.md`).
