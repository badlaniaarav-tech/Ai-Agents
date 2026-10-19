# Agent HQ: a 31-agent AI office for Claude Code

A 31-agent AI office that runs inside [Claude Code](https://claude.com/claude-code). One lead (the chief of staff) routes your request to eight teams around a shared Brain. Team heads split the work across sub-agents that run in parallel, review the result, and hand it back for your OK. A shared brain (a memory MCP server) holds your company facts and brand rules, so every agent follows the same rules and remembers what you tell it.

Built from three Bekhruz AI videos:

| Video | What it contributed |
|---|---|
| [I Built an AI Agent Team From Scratch](https://youtu.be/-14NKNpWr1M) | The creative team: `clip-editor`, `brand-checker`, `/edit-clips`, the video `tools/`, and the permission rules. Taken from the creator's own repo, [bekhruztbx/ai-creative-team](https://github.com/bekhruztbx/ai-creative-team) (MIT). |
| [I Built an AI Office With 31 Agents](https://youtu.be/t0hGE-aaAds) | The office: eight teams (Research, Inbox, Scripts, Dev, TBX Shop, Social, Creative, Analytics) around the Brain, heads that orchestrate, workers that do one job, and the Three.js "Agent HQ" page where each room is a team and each character is an agent. |
| [I Gave My AI Agents One Brain](https://youtu.be/fZn-DftQYSo) | The shared brain: one memory MCP server in `brain/memory.jsonl` that every agent reads and the lead writes to. |

## What is in here

| Piece | Where | What it does |
|---|---|---|
| Office charter | `CLAUDE.md` | The chief of staff's instructions: teams, how work flows, the brain, the rules |
| 31 agents | `.claude/agents/*.md` | One file per agent: who it is, when to use it, its tools, its steps |
| Org chart | `docs/office.md` | Every agent and its job, plus how a request moves |
| Commands | `.claude/commands/` | `/brief`, `/edit-clips`, `/standup`, `/research`, `/campaign`, `/hire`, `/office`, `/tasks` |
| Approvals | `.claude/settings.json` | What agents may do alone, what asks you, what is never allowed |
| Shared brain | `.mcp.json` + `brain/memory.jsonl` | Memory MCP server with the **Company** and **Brand rules** entities |
| Video tools | `tools/` | `cut.py`, `captions.py`, `thumbnail.py`, `frames.py` for the creative pipeline |
| 3D office | `office/` | Agent HQ, a Three.js page: the Brain in the middle, one room per team, one character per agent, and characters light up while their sub-agent runs |

Teams: Research, Inbox, Scripts, Dev, TBX Shop, Social, Creative, Analytics. See `docs/office.md`.

## See the office in 3D

```bash
python3 office/serve.py        # then open http://localhost:8787
```

Drag to orbit, wheel to zoom, click a character for its job, tools and model, click a room to fly to it. The top bar has the Office, Tasks, Calendar and Brain tabs and the "31 agents · N running" counter; the minimap is bottom right. **Tasks** is a board (to do, doing, review, done) plus who is running right now and the live log. **Calendar** is a month view of tasks, scheduled posts and meetings by date. Both read and write `office/tasks.json`, the same file the agents update with `python3 office/tasks.py` (see `/tasks`), so what the office does and what you add by hand land in one place. **Brain** shows the shared memory. **Ask any agent…** in the top bar opens a chat with any of the 31 agents, in character, using its own definition and the brain; it works when the page is published as a claude.ai artifact (it asks Claude as the viewer), and locally it points you to Claude Code. Press "Demo" to see what it looks like when agents are busy.

It is live: hooks in `.claude/settings.json` append every sub-agent start and stop to `office/events.jsonl`, and the page polls that file. Run Claude Code in this repo in another terminal, give it a task, and watch the characters work. After `/hire`, run `/office` (or `python3 office/build.py`) to regenerate `office/agents.json`.

## Setup (once)

You need Claude Code, Node.js 18+ (runs the memory server), and for video editing also ffmpeg and Python 3.10+.

```bash
git clone https://github.com/badlaniaarav-tech/Ai-Agents
cd Ai-Agents
bash tools/setup.sh      # only needed for the video tools
claude
```

Then tell it about your company once, for example: *"We sell X to Y. Our voice is Z."* The chief of staff saves it to the brain.

## Use it

| You type | What happens |
|---|---|
| `/brief write the listing for the new hoodie` | Chief of staff routes to TBX Shop; `copywriter` writes, `brand-checker` reviews |
| `/research AI video editing tools market` | Market, competitor and trend agents run in parallel; one brief with sources |
| `/campaign launch of the October drop` | Social and TBX Shop heads plan; posts, replies, newsletter, ads and pricing run in parallel |
| `/edit-clips` | One `clip-editor` per clip in `inbox/`, then `brand-checker` |
| `/standup` | Every team head reports; status goes to `work/analytics/status.md` |
| `/tasks add "Hoodie drop" --team "TBX Shop" --date 2026-10-24` | Puts it on the board and the calendar in Agent HQ |
| `/hire podcast-producer: turns long recordings into episode outlines` | Adds a new agent file and updates the org chart |

Or just talk to it. Anything you say in plain words gets routed the same way as `/brief`.

Deliverables land in `work/<team>/<task>/` (and `out/<clip>/` for videos). Nothing is posted, sent, pushed or published by the office. You review and say OK.

## Teach it

Say *"From now on, cover text is red, not yellow"* or *"Never use the word 'leverage'"*. The rule goes into `brain/memory.jsonl` and every agent follows it from the next run. You can also edit that file directly.

## Safety

- Agents may run the four video tools, write under `work/`, `out/`, `done/` and `brain/`, search the web, and run tests. Editing source code or the agents themselves asks you first (`.claude/settings.json`).
- `rm`, `curl`, `wget`, force pushes and reading `.env` are blocked. `git push` asks.
- Every deliverable is reviewed by a checker agent or a team head before you see it.

## License

MIT. The video tools and the Geist font come from [bekhruztbx/ai-creative-team](https://github.com/bekhruztbx/ai-creative-team); Geist is under the SIL Open Font License (`tools/fonts/OFL.txt`).
