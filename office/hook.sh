#!/usr/bin/env bash
# Claude Code hook: appends the event it receives on stdin to office/events.jsonl, so the 3D office can show who is working.
# Wired up in .claude/settings.json for UserPromptSubmit, SubagentStart, SubagentStop and Stop. Never fails the tool call.
dir="$(cd "$(dirname "$0")" && pwd)"
HOOK_JSON="$(cat)" HOOK_OUT="$dir/events.jsonl" python3 -c '
import json, os, time
try:
    data = json.loads(os.environ.get("HOOK_JSON") or "{}")
except Exception:
    data = {}
event = {"ts": time.time(), "event": data.get("hook_event_name", ""), "agent": data.get("agent_type") or data.get("agent_name") or "", "id": data.get("agent_id", ""), "session": data.get("session_id", "")}
with open(os.environ["HOOK_OUT"], "a") as f:
    f.write(json.dumps(event) + "\n")
' 2>/dev/null || true
exit 0
