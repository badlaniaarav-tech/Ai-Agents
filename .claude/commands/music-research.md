---
description: The Music team refreshes music/brief.md (what viral videos in our niche sound like this week) and swaps in fresh Creative Commons tracks per mood, with credits
---
Refresh the music for our edits. Topic: $ARGUMENTS (default: the company's niche; for Aarav, golf swing reels and shorts).

1. Put it on the board: `python3 office/tasks.py add "Weekly music refresh" --team Music --agent music-director`, move it to doing.
2. Start the **music-director** sub-agent with the topic. It runs sound-scout (the brief), then one track-curator per mood in parallel (3 fresh tracks each, last week's removed, credits updated), then checks the folder.
3. Move the task to review and report to the owner: the moods, tracks in and out (title, artist, license), the five in-app sounds, and anything to decide. The office downloads tracks only from Creative Commons sources and never posts anything.
