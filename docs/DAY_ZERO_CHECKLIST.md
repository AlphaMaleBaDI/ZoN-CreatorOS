# ZoN CreatorOS Day Zero Checklist

This checklist defines the launch ritual to execute on **July 6** when the implementation sprint officially begins.

## Pre-Flight Verification

- [ ] Run test suite locally using `.venv\Scripts\python -m pytest` to verify 100% green status.
- [ ] Confirm local Ollama service is up and running.

## Cloud & Repository Activation

- [ ] Activate AMD Instinct Cloud hackathon credits.
- [ ] Verify SSH/API access to AMD Instinct GPU clusters.
- [ ] Create public GitHub repository for `ZoN-CreatorOS`.
- [ ] Add remote link to local git workspace.
- [ ] Push local `develop` branch to GitHub.
- [ ] Push the local `preseason-freeze-v1` tag.

## Sprint Phase 1.2 Start

- [ ] Begin Memory Engine Implementation (Workspace Scoping, Profile CRUD, FAISS integration).
