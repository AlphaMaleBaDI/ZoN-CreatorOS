# Killer Demo Script

## Setup

1. Open the dashboard at `http://localhost:8501`.
2. Start a fresh project scope: `afrovbra-spring-release`.
3. Upload three assets:
   - `song.wav` (one song demo)
   - `lyrics.md` (final lyrics)
   - `goal.txt` (one-line release goal)

## Conversation

User: "Plan the release of this song."

ZoN returns a single JSON artifact with the following shape:

```json
{
  "audience_profile": "...",
  "release_strategy": "...",
  "marketing_angles": ["...", "...", "..."],
  "next_actions": [
    {"action": "...", "why": "..."},
    {"action": "...", "why": "..."},
    {"action": "...", "why": "..."}
  ],
  "vibra_state": {
    "name": "...",
    "color": "..."
  },
  "memory_references": [
    {"topic": "...", "info": "..."}
  ]
}
```

## Why this wins

- It is an **artifact**, not a chat.
- It is **grounded in memory**: every "why" cites a stored memory entry
  the artist can click through to.
- It is **stateful**: the next session opens with the artifact, not
  blank.
- It is **mood-aware**: the Vibra state colors the dashboard and the
  next-action tone.
- It is **multimodal**: the song file and lyrics are both in scope and
  both influence the output.

## Stretch

A second pass: artist says "make it more hopeful." ZoN re-runs the plan,
shifts the Vibra, and updates the artifact in place. The agent framework
applies the edit with the `dryRun` / `confirmApply` flow already defined
in `schemas.PromptRequest`.
