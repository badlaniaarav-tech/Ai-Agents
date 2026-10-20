---
description: Edit every new clip in inbox/ in parallel, check the results, and report to the owner
---
Edit the new clips in `inbox/`.

1. List the clips: `ls inbox` (mp4, mov, m4v).
   If `music/brief.md` is missing or older than 14 days, run `/music-research` first (the **music-director** sub-agent) so the music matches what is working right now.
2. Start one **clip-editor** sub-agent per clip. Start them all in the same message so they work in parallel. Tell each one its file name.
3. When all of them are done, run the **brand-checker** on `out/`.
4. If the brand-checker flags something, send that clip back to a clip-editor with the exact fix, then check again.
5. Move each finished raw clip: `mv inbox/<file> done/`
6. Report to the owner: a short table (clip, edit length, title, cover text, music track and mood) and the paths; a clip with a launch-monitor photo has two reels, `reel.mp4` (dark tiles) and `reel-screen.mp4` (the real screen), both are for the owner; `reel.mp4` is the one to post for a swing clip (`final.mp4` is the long version), `edit.mp4` is the same without music for adding a trending sound in the Instagram app. If the brief names tracks that are not in `music/` yet, list them with their download links. End with: "Nothing is published. Reply OK to approve."

$ARGUMENTS

Style: if $ARGUMENTS names a format from `ideas/formats.json` (by id or name), every clip-editor builds that one; otherwise each picks the best fit and lists two alternatives in the report.
