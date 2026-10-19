---
description: Best times to post per network from Metricool, then place scheduled posts on those slots
---
Find the best times to post and schedule around them: $ARGUMENTS

1. If the Metricool connector tools are available in this session (`mcp__Metricool_Social_Media_Management__getBrandSettings`, `mcp__Metricool_Social_Media_Management__getBestTimeToPostByNetwork`):
   - Call `getBrandSettings` for the brand id and timezone. If it says no social network is connected, tell the owner to connect one at the link it gives and stop.
   - For each network the owner uses (default: instagram, tiktok, youtube; add twitter, linkedin, facebook if asked), call `getBestTimeToPostByNetwork` for the next 7 days with that brand id and timezone.
   - Report the top three slots per network as a table (network, day, hour, score).
2. If the tools are not available: say so, and tell the owner that the Agent HQ page has a "Best times" button on the Calendar tab that asks Metricool directly, or that they can add the Metricool connector in claude.ai.
3. Then put the undated or past-due posts on the board (`python3 office/tasks.py list --status todo`, items with `"type": "post"`) onto the best upcoming slots: `python3 office/tasks.py move` is not needed; update their dates with `python3 office/tasks.py add` for new ones or edit `office/tasks.json` for existing ones (the `date` field, plus the time in `notes`). Keep one post per slot, best slot first.
4. Report what was scheduled. Nothing is posted; the Social team drafts, the owner approves.
