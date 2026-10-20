---
description: Refresh ideas/formats.json with golf video formats that are getting views on YouTube and Instagram, each with how to build it
---
Refresh the video ideas. Topic: $ARGUMENTS (default: the owner's niche from the brain; say `/ideas workout reels` or `/ideas running` for another kind of clip).

1. Put it on the board: `python3 office/tasks.py add "Video ideas refresh" --team Creative --agent creative-director`, move it to doing.
2. Start the **idea-scout** sub-agent with the topic. It updates `ideas/formats.json`.
3. For every `needs` line it reports, say so to the owner and offer to route it to the Dev team (`engineering-lead`) to add the flag or tool.
4. Run `python3 office/build.py` so the office page's Style list picks up the new formats. Move the task to review and report: formats added (one line each), formats retired, what needs building. Nothing is posted.
