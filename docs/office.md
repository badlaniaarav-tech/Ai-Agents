# Org chart

31 agents in 7 departments, led by the chief of staff (the Claude Code session itself, with its instructions in `CLAUDE.md`). Each of the 31 agents is a sub-agent file in `.claude/agents/`. Heads run on Opus and orchestrate; workers run on Sonnet and do one job each.

| # | Agent | Department | Job |
|---|---|---|---|
| lead | chief of staff | Leadership | Routes work, runs departments in parallel, reviews, reports (`CLAUDE.md`) |
| 1 | `strategist` | Leadership | Goal to options, recommendation, first three steps |
| 2 | `creative-director` | Creative | Splits video and content jobs, runs the workers, sends work to brand-checker |
| 3 | `script-writer` | Creative | Short-form video scripts: hook, three beats, close |
| 4 | `hook-writer` | Creative | Ten ranked opening lines for any piece |
| 5 | `copywriter` | Creative | Landing page, product and bio copy |
| 6 | `clip-editor` | Creative | One raw clip to a captioned vertical edit, cover and notes (`tools/`) |
| 7 | `brand-checker` | Creative | Reviews every creative deliverable against the brand rules; PASS or FIX |
| 8 | `thumbnail-designer` | Creative | Picks the frame, text and placement for covers |
| 9 | `marketing-director` | Marketing | Campaign plan, delegates per channel, reviews |
| 10 | `social-media-manager` | Marketing | Platform-ready posts and a calendar |
| 11 | `seo-specialist` | Marketing | Keywords, titles, descriptions, outlines |
| 12 | `email-marketer` | Marketing | Sequences, newsletters, subject lines |
| 13 | `ads-specialist` | Marketing | Paid ad variants, audiences, test plan |
| 14 | `community-manager` | Marketing | Replies to comments and DMs, flags what needs the owner |
| 15 | `sales-director` | Sales | Pipeline plan, delegates research, outreach, proposals |
| 16 | `lead-researcher` | Sales | Qualified leads for one segment, with fit reasons |
| 17 | `outreach-writer` | Sales | Personalised 3-step outreach sequences |
| 18 | `proposal-writer` | Sales | Proposals and quotes with scope, price, next step |
| 19 | `research-director` | Research | Splits a question three ways, merges into one brief |
| 20 | `market-analyst` | Research | Market size, customers, pricing benchmarks |
| 21 | `competitor-analyst` | Research | Competitor profiles and the gap we can own |
| 22 | `trend-scout` | Research | What changed in the last 30 to 90 days |
| 23 | `engineering-lead` | Engineering | Spec, delegates to devs, runs QA and review |
| 24 | `frontend-dev` | Engineering | UI code following the project's patterns |
| 25 | `backend-dev` | Engineering | Server, API, data and tooling code |
| 26 | `qa-tester` | Engineering | Tests per acceptance criterion, reproduces bugs |
| 27 | `code-reviewer` | Engineering | Ranked findings on the diff; PASS or FIX |
| 28 | `operations-manager` | Operations | Status, schedules, budgets, support; keeps `work/operations/status.md` |
| 29 | `project-manager` | Operations | Milestones, tasks, owners, dates, risks |
| 30 | `finance-analyst` | Operations | Budgets, forecasts, pricing math with assumptions |
| 31 | `customer-support` | Operations | Replies to customer messages, escalates money and legal |

## How a request moves

```
owner  ->  chief of staff  ->  department head  ->  workers (parallel)
                 ^                   |                    |
                 |                   v                    v
              report  <-------  review (brand-checker / code-reviewer / head)
```

## The shared brain

`.mcp.json` starts the memory MCP server with its file at `brain/memory.jsonl`. Two entities: **Company** and **Brand rules**. Every agent reads them before working. When the owner says "from now on…", the chief of staff writes it there, so every agent remembers it on the next run. Edit the JSONL by hand to seed it.

## Adding an agent

`/hire <name>: <job>` writes the file and updates this chart. Keep one job per agent, say when to use it in the description (that is how the chief of staff picks it), and give it only the tools it needs.
