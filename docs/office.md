# Org chart

34 agents in 9 teams around the Brain, led by the chief of staff (the Claude Code session itself, with its instructions in `CLAUDE.md`). Each of the 34 agents is a sub-agent file in `.claude/agents/`. Team heads run on Opus and orchestrate; workers run on Sonnet and do one job each.

| # | Agent | Team | Job |
|---|---|---|---|
| lead | chief of staff | The Brain | Routes work, runs teams in parallel, reviews, reports (`CLAUDE.md`) |
| 1 | `research-director` | Research | Splits a question three ways, merges into one brief |
| 2 | `market-analyst` | Research | Market size, customers, pricing benchmarks |
| 3 | `competitor-analyst` | Research | Competitor profiles and the gap we can own |
| 4 | `trend-scout` | Research | What changed in the last 30 to 90 days |
| 5 | `inbox-manager` | Inbox | Triages email, DMs and requests; routes and drafts |
| 6 | `customer-support` | Inbox | Replies to customer messages, escalates money and legal |
| 7 | `proposal-writer` | Inbox | Proposals and quotes with scope, price, next step |
| 8 | `script-writer` | Scripts | Short-form video scripts: hook, three beats, close; runs the Scripts team |
| 9 | `hook-writer` | Scripts | Ten ranked opening lines for any piece |
| 10 | `seo-specialist` | Scripts | Keywords, titles, descriptions, outlines |
| 11 | `engineering-lead` | Dev | Spec, delegates to devs, runs QA and review |
| 12 | `frontend-dev` | Dev | UI code following the project's patterns |
| 13 | `backend-dev` | Dev | Server, API, data and tooling code |
| 14 | `qa-tester` | Dev | Tests per acceptance criterion, reproduces bugs |
| 15 | `code-reviewer` | Dev | Ranked findings on the diff; PASS or FIX |
| 16 | `shop-manager` | TBX Shop | Product drops and launches: plan, delegate, review |
| 17 | `copywriter` | TBX Shop | Product listings, landing page and bio copy |
| 18 | `ads-specialist` | TBX Shop | Paid ad variants, audiences, test plan |
| 19 | `finance-analyst` | TBX Shop | Pricing, margin, budgets with assumptions |
| 20 | `project-manager` | TBX Shop | Launch timeline: milestones, tasks, owners, dates |
| 21 | `social-media-manager` | Social | Posts and calendar; runs the Social team |
| 22 | `community-manager` | Social | Replies to comments and DMs, flags what needs the owner |
| 23 | `email-marketer` | Social | Newsletters and sequences with subject lines |
| 24 | `outreach-writer` | Social | Personalised outreach to partners, sponsors, collabs |
| 25 | `creative-director` | Creative | Splits video jobs, runs the workers, sends work to brand-checker |
| 26 | `clip-editor` | Creative | One raw clip to a captioned vertical edit, cover and notes (`tools/`) |
| 27 | `brand-checker` | Creative | Reviews every creative deliverable against the brand rules; PASS or FIX |
| 28 | `thumbnail-designer` | Creative | Picks the frame, text and placement for covers |
| 29 | `analytics-lead` | Analytics | The weekly report: what the numbers mean, what to change |
| 30 | `data-analyst` | Analytics | Cleans exports, computes metrics and trends, shows the work |
| 31 | `strategist` | Analytics | Goal to options, recommendation, first three steps |
| 32 | `music-director` | Music | Weekly: what viral videos sound like now, fresh tracks in `music/`, credits kept current |
| 33 | `sound-scout` | Music | This week's moods, tempo, search words and trending in-app sounds, in `music/brief.md` |
| 34 | `track-curator` | Music | One mood: downloads CC tracks with `tools/music_fetch.py`, removes last week's, updates credits |

## How a request moves

```
owner  ->  chief of staff (the Brain)  ->  team head  ->  workers (parallel)
                 ^                              |               |
                 |                              v               v
              report  <----------  review (brand-checker / code-reviewer / head)
```

## The shared brain

`.mcp.json` starts the memory MCP server with its file at `brain/memory.jsonl`. Two entities: **Company** and **Brand rules**. Every agent reads them before working. When the owner says "from now on…", the chief of staff writes it there, so every agent remembers it on the next run. Edit the JSONL by hand to seed it.

## The 3D office

`office/index.html` draws this chart as a 3D floor: the Brain in the middle, one room per team around it, one desk and character per agent, heads wear a hat. The top bar has Office, Tasks (the board: to do, doing, review, done, plus the live log), Calendar (tasks, scheduled posts and meetings by date) and Brain (the memory file) tabs, plus an "Ask any agent…" box that chats with any agent through the claude.ai sample capability when the page is published as an artifact, the running counter, and the model chips; the minimap sits bottom right. `office/build.py` turns the table in `CLAUDE.md` plus the agent files into `office/agents.json`; `office/serve.py` serves the page, streams `office/events.jsonl` (written by the hooks in `.claude/settings.json` on every sub-agent start and stop) exposes the brain at `/brain`, and reads and writes the board at `/tasks`. The board lives in `office/tasks.json`; agents change it with `python3 office/tasks.py add|move|remove|list`.

## Adding an agent

`/hire <name>: <job>` writes the file and updates this chart. Keep one job per agent, say when to use it in the description (that is how the chief of staff picks it), and give it only the tools it needs.
