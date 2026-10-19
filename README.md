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
| Commands | `.claude/commands/` | `/brief`, `/edit-clips`, `/standup`, `/research`, `/campaign`, `/hire`, `/office`, `/tasks`, `/best-time`, `/competitors`, `/deck` |
| Approvals | `.claude/settings.json` | What agents may do alone, what asks you, what is never allowed |
| Shared brain | `.mcp.json` + `brain/memory.jsonl` | Memory MCP server with the **Company** and **Brand rules** entities |
| Video tools | `tools/` | `cut.py`, `captions.py`, `thumbnail.py`, `frames.py` for the creative pipeline |
| 3D office | `office/` | Agent HQ, a Three.js page: the Brain in the middle, one room per team, one character per agent, and characters light up while their sub-agent runs |

Teams: Research, Inbox, Scripts, Dev, TBX Shop, Social, Creative, Analytics. See `docs/office.md`.

## See the office in 3D

```bash
python3 office/serve.py        # then open http://localhost:8787
```

Drag to orbit, wheel to zoom, click a character for its job, tools and model, click a room to fly to it. The top bar has the Office, Tasks, Calendar and Brain tabs and the "31 agents · N running" counter; the minimap is bottom right. **Tasks** is a board (to do, doing, review, done) plus who is running right now and the live log. **Calendar** is a month view of tasks, scheduled posts and meetings by date. Every task has a Run button (and a new task runs as soon as you add it): the team head plans and splits the work, the workers run in parallel with their characters lit up, a reviewer checks it, and the deliverables land on the task, which moves to review. On the published page the agents run through your own Claude; locally, Run points you to `/brief` in Claude Code, where the hooks light the same characters up. Both read and write `office/tasks.json`, the same file the agents update with `python3 office/tasks.py` (see `/tasks`), so what the office does and what you add by hand land in one place. **Brain** shows the shared memory. The Calendar tab's **Best times** button asks your Metricool connector for the best posting slots per network and can place undated posts on them; `/best-time` does the same from Claude Code. The **Competitors** tab pulls your Instagram competitors from Metricool (followers, posts, reels, average likes, engagement, their top posts) next to your own numbers, and one button hands the gap to the Research team as a task, and "Find for me" asks Claude for accounts to benchmark when you have none yet; `/competitors` does the same from Claude Code and searches the web for candidates.

**Posting with your approval.** A post task has "Send to Metricool for my approval": it schedules the post in Metricool's review flow with you as the reviewer, Metricool emails you (and its app notifies you), and nothing publishes until you approve it there. Instagram needs a public image or video link. **Golf clips.** The Tasks tab has a Golf clips section: upload a swing video (under 20 MB on the web page) and the Creative team looks at three stills, describes the swing, and writes the title, hooks, caption, tags, cover text and alt text, which the brand-checker reviews. The cut and captioned video itself is produced by `/edit-clips` in Claude Code from `inbox/`. **Account menu.** The avatar top right opens your name and email, the office name and logo (rename it), the Metricool brand, where the board saves, device alerts, page permissions and backup. **Phone alerts.** A scheduled check-in on your claude.ai account reads the board four times a day and pushes a notification to the Claude app when anything is waiting for your OK; Metricool also notifies you about posts sent for approval. **Voice.** The mic buttons on the task box and the ask box dictate with the browser's speech recognition. **Auto team.** Leave the team on "Auto" and the chief of staff routes the task. **Backup.** Export and Import on the Tasks tab save and restore the board as a file you can keep or email yourself. `/deck <topic>` builds a .pptx presentation in Claude Code. **Ask any agent…** in the top bar opens a chat with any of the 31 agents, in character, using its own definition and the brain; it works when the page is published as a claude.ai artifact (it asks Claude as the viewer), and locally it points you to Claude Code. Moving around: drag to orbit, right-drag (or arrow keys / WASD) to pan, wheel to zoom toward the cursor, double-click to dive in, Q/E to rotate, 1 to 8 to jump to a room, O for the overview, click the minimap to jump. Press "Demo" to see what it looks like when agents are busy. Idle agents live their office life: they stroll their room, walk the walkways to the Brain or another team, meet a colleague and talk in speech bubbles about real items on the board and rules from the brain, then head back to their desk. An agent that starts real work goes straight home and stays there until it finishes.

It is live: hooks in `.claude/settings.json` append every sub-agent start and stop to `office/events.jsonl`, and the page polls that file. Run Claude Code in this repo in another terminal, give it a task, and watch the characters work. After `/hire`, run `/office` (or `python3 office/build.py`) to regenerate `office/agents.json`.

## Sharing it with family or a team

One claude.ai login can hold several people. The page has its own sign-in: each person creates a profile with their name, email and a password, gets their own board, clips and results, and can stay signed in on their device. The account menu (avatar, top right) has Switch person and Change password. The password is a lock inside the page, keyed to the shared claude.ai account, so it keeps people's work apart rather than guarding secrets from each other. The first profile created owns Metricool: only the profile whose email matches the Metricool account (or the first profile) can send posts for approval, read best times or competitors; others are told whose it is. People on their own claude.ai accounts get their own separate set of profiles. To let someone save work, share the link as a Contributor (or higher) from the page's Share menu.

## The website

The claude.ai link is the full office: agents answer, tasks run, the board saves to your account, Metricool works. Every push to `main` also publishes the `office/` folder to GitHub Pages (`.github/workflows/pages.yml`), which gives a public, read-only version of the 3D office with the starter board and no AI features, at `https://<owner>.github.io/Ai-Agents/`.

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
