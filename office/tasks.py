#!/usr/bin/env python3
"""The office task board and calendar, stored in office/tasks.json. The Agent HQ page shows and edits the same file.

usage:
  python3 office/tasks.py list [--status todo|doing|review|done] [--team NAME]
  python3 office/tasks.py add "title" --team "TBX Shop" [--agent shop-manager] [--date 2026-10-24] [--type task|post|meeting] [--notes "..."]
  python3 office/tasks.py move <id> <todo|doing|review|done>
  python3 office/tasks.py remove <id>
Every command prints one JSON line with the result.
"""
import argparse, datetime, json, os, uuid

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")
STATUSES = ["todo", "doing", "review", "done"]


def load():
    if not os.path.exists(PATH):
        return {"items": []}
    with open(PATH, encoding="utf-8") as f:
        return json.load(f)


def save(d):
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)
    os.replace(tmp, PATH)


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    l = sub.add_parser("list"); l.add_argument("--status", choices=STATUSES); l.add_argument("--team")
    a = sub.add_parser("add"); a.add_argument("title"); a.add_argument("--team", required=True); a.add_argument("--agent", default="")
    a.add_argument("--date", default=datetime.date.today().isoformat()); a.add_argument("--type", default="task", choices=["task", "post", "meeting"]); a.add_argument("--notes", default="")
    m = sub.add_parser("move"); m.add_argument("id"); m.add_argument("status", choices=STATUSES)
    r = sub.add_parser("remove"); r.add_argument("id")
    x = ap.parse_args(); d = load()
    if x.cmd == "list":
        items = [i for i in d["items"] if (not x.status or i["status"] == x.status) and (not x.team or i["team"].lower() == x.team.lower())]
        print(json.dumps({"count": len(items), "items": items}))
    elif x.cmd == "add":
        item = {"id": uuid.uuid4().hex[:8], "type": x.type, "title": x.title, "team": x.team, "agent": x.agent, "status": "todo", "date": x.date, "notes": x.notes, "created": datetime.datetime.now().isoformat(timespec="seconds")}
        d["items"].append(item); save(d); print(json.dumps({"added": item}))
    elif x.cmd == "move":
        for i in d["items"]:
            if i["id"] == x.id:
                i["status"] = x.status; save(d); print(json.dumps({"moved": i})); return
        raise SystemExit(json.dumps({"error": f"no item {x.id}"}))
    elif x.cmd == "remove":
        before = len(d["items"]); d["items"] = [i for i in d["items"] if i["id"] != x.id]; save(d)
        print(json.dumps({"removed": before - len(d["items"])}))


if __name__ == "__main__":
    main()
