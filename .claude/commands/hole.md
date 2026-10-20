---
description: Play a hole with me: every shot on one hole in order, a two-line label on each (yards and club), the hole card on the tee shot, real speed, music low
---
Build a "play a hole with me" reel from the shot clips in `inbox/` (or the ones named), in the order they were played. $ARGUMENTS gives the labels, one per shot, separated by |, for example: `512 yards, par 5 | 170 yards, 9 iron | 22 yards, 60 wedge | par` (the last one is the result if it is a score word).

1. Put it on the board: `python3 office/tasks.py add "Hole: <first label>" --team Creative --agent creative-director`, move it to doing.
2. Start one **clip-editor** with the clips in order and the labels. It runs
   `python3 tools/hole.py out/hole-<date>/hole.mp4 "inbox/<shot1>|512 yards|par 5" "inbox/<shot2>|170 yards|9 iron" "inbox/<shot3>|22 yards|60 wedge" --result "par" --mood chill`
   checks the frames (`tools/frames.py`), fixes `--focus`, `--zoom` or `--impacts` where a label covers the golfer or a cut comes too early for the ball flight (`--post` longer keeps the flight in), writes `out/hole-<date>/notes.md` with the JSON line and the music credit.
3. Run **brand-checker** (labels: two short lines, caps, white; the hole card on the first shot only; music low; credit present). Send fixes back.
4. Move the task to review and report: length, the shots in order with their labels, the track and credit, the path. Clips stay in `inbox/` until the owner says it is good. Nothing is posted.
