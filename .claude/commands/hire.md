---
description: Add a new agent to the office: writes its .claude/agents/<name>.md and updates the org chart
---
Hire a new agent: $ARGUMENTS

1. Ask (or infer from the request): name (kebab-case), department, one-sentence job, when the chief of staff should use it, which tools it needs (Read/Write/Bash/WebSearch/memory), model (sonnet for workers, opus for heads).
2. Write `.claude/agents/<name>.md` in the same format as the existing agents: frontmatter (name, description with "Use when…", tools, model), then a short prompt: read the brain, numbered steps, where to write under `work/<department>/<task>/`, what to report, and the rule that nothing is sent or published.
3. Add it to the department table in `CLAUDE.md` and to `docs/office.md`.
4. Report the file path and a one-line example of how to call it.
