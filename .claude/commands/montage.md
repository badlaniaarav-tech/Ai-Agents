---
description: Swing montage from several clips in inbox/, like the golf reels the owner follows: one line of text, first swing slow, the rest cut fast on the strike
---
Build a swing montage from the clips in `inbox/` (or the ones named in $ARGUMENTS), the way the owner's example reels do it.

1. Put it on the board: `python3 office/tasks.py add "Montage: <label>" --team Creative --agent creative-director`, move it to doing.
2. Start one **clip-editor** with: the list of clips (best swing first, it gets the slow motion), the text line (from $ARGUMENTS, default "Addicted to this sound"), and the mood for the music (default hype, low).
   It runs `python3 tools/montage.py out/montage-<date>/montage.mp4 inbox/<clip1> inbox/<clip2> ... --label "<text>" --mood <mood>`, checks the frames (`tools/frames.py`), fixes `--focus` for any clip where the golfer is off-centre, writes `out/montage-<date>/notes.md` with the tool's JSON line and the music credit from `music/credits.md`.
3. Run **brand-checker** on the result (one line of text, strike on the cut, music low, credit present). Send fixes back.
4. Move the task to review and report: length, clips used in order, label, track and credit, path. Clips stay in `inbox/` until the owner says the montage is good. Nothing is posted.
