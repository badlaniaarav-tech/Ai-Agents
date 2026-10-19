---
description: Build a presentation (.pptx) for work: outline from the Scripts team, slides via the pptx skill, review, then the file for the owner
---
Presentation request: $ARGUMENTS

1. Add it to the board (`python3 office/tasks.py add "Deck: <topic>" --team Scripts --agent script-writer`).
2. Ask the owner, once, for anything missing: audience, length (slides), tone, and any source material (files, links, numbers). If they gave enough, go.
3. Outline: start **script-writer** for a slide-by-slide outline (title, one message per slide, speaker notes, what visual each slide needs) and **research-director** in the same message if facts or numbers are needed. Save to `work/scripts/deck-<topic>/outline.md`.
4. Build: use the `pptx` skill to produce `work/scripts/deck-<topic>/<topic>.pptx` from the outline. Keep slides to one idea each, big headlines, real numbers with sources in the notes.
5. Review: **brand-checker** reads the outline and a contact sheet or text export of the deck against the brand rules; fix what it flags.
6. Move the task to review and report: the file path, the slide list, and what the owner should check. Nothing is sent.
