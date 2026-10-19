---
description: Rebuild office/agents.json from the agent files and tell the owner how to open the 3D office
---
Refresh the 3D office.

1. Run `python3 office/build.py`. It reads the department table in `CLAUDE.md` and every file in `.claude/agents/` and writes `office/agents.json`. Fix any warning it prints (an agent missing from the table, or a table entry without a file).
2. Tell the owner: start it with `python3 office/serve.py` and open http://localhost:8787. Each room is a department, each character is an agent, and a character lights up while its sub-agent is running (events come from the hooks in `.claude/settings.json`).

$ARGUMENTS
