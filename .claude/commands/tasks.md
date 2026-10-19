---
description: Show or change the office task board and calendar (office/tasks.json), the same one the Agent HQ page shows
---
Task board request: $ARGUMENTS

Use `python3 office/tasks.py`:
- `list [--status todo|doing|review|done] [--team NAME]` to show the board
- `add "title" --team "TBX Shop" --agent shop-manager --date 2026-10-24 --type task|post|meeting --notes "..."` to add a task, a scheduled post, or a meeting (the calendar shows everything by date)
- `move <id> <status>` and `remove <id>`

If no arguments were given, list the open items grouped by status and the next seven days of the calendar, then ask what to change. When you route a request to a team, add it as a task for that team's head; move it to `doing` when the team starts, `review` when the deliverable is ready for the owner, `done` when the owner says OK.
