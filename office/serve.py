#!/usr/bin/env python3
"""Serves the 3D office at http://localhost:8787, streams live agent events from office/events.jsonl, exposes the shared brain (brain/memory.jsonl) at /brain, and reads/writes the task board (office/tasks.json) at /tasks.

usage: python3 office/serve.py [port]
Open the URL in a browser, then run Claude Code in this repo: each sub-agent that starts lights up in its room.
"""
import json, os, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))
EVENTS = os.path.join(HERE, "events.jsonl")
BRAIN = os.path.join(os.path.dirname(HERE), "brain", "memory.jsonl")
TASKS = os.path.join(HERE, "tasks.json")
LOCK = __import__("threading").Lock()
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8787


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=HERE, **kw)

    def log_message(self, *a):
        pass

    def send_json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        """POST /tasks with {"op": "add"|"update"|"remove", "item": {...}} edits office/tasks.json (what tasks.py does on the command line)."""
        u = urlparse(self.path)
        if u.path != "/tasks":
            self.send_json({"error": "not found"}, 404); return
        try:
            req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0)) or b"{}"))
        except Exception:
            self.send_json({"error": "bad json"}, 400); return
        op, item = req.get("op"), req.get("item") or {}
        with LOCK:
            d = {"items": []}
            if os.path.exists(TASKS):
                with open(TASKS, encoding="utf-8") as f:
                    d = json.load(f)
            if op == "add":
                item = {"id": os.urandom(4).hex(), "type": item.get("type", "task"), "title": str(item.get("title", ""))[:200], "team": item.get("team", ""), "agent": item.get("agent", ""),
                        "status": item.get("status", "todo"), "date": item.get("date", ""), "notes": str(item.get("notes", ""))[:1000]}
                d["items"].append(item)
            elif op == "update":
                for i in d["items"]:
                    if i["id"] == item.get("id"):
                        for k in ("title", "team", "agent", "status", "date", "notes", "type"):
                            if k in item:
                                i[k] = item[k]
                        item = i
            elif op == "remove":
                d["items"] = [i for i in d["items"] if i["id"] != item.get("id")]
            else:
                self.send_json({"error": "unknown op"}, 400); return
            tmp = TASKS + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(d, f, indent=2)
            os.replace(tmp, TASKS)
        self.send_json({"ok": True, "item": item, "count": len(d["items"])})

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/tasks":
            d = {"items": []}
            if os.path.exists(TASKS):
                with open(TASKS, encoding="utf-8") as f:
                    d = json.load(f)
            self.send_json(d); return
        if u.path == "/events":
            since = int(parse_qs(u.query).get("since", ["0"])[0])
            lines = []
            if os.path.exists(EVENTS):
                with open(EVENTS, encoding="utf-8") as f:
                    lines = f.read().splitlines()
            body = json.dumps({"total": len(lines), "events": [json.loads(l) for l in lines[since:] if l.strip()]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if u.path == "/brain":
            ents = []
            if os.path.exists(BRAIN):
                for l in open(BRAIN, encoding="utf-8"):
                    try:
                        o = json.loads(l)
                    except Exception:
                        continue
                    if o.get("type") == "entity":
                        ents.append({"name": o.get("name"), "type": o.get("entityType"), "observations": o.get("observations", [])})
            body = json.dumps({"entities": ents, "notes": sum(len(e["observations"]) for e in ents)}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if u.path == "/":
            self.path = "/index.html"
        super().do_GET()


if __name__ == "__main__":
    print(f"AI office: http://localhost:{PORT}  (events from {os.path.relpath(EVENTS)})")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
