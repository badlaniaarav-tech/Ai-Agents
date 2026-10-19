#!/usr/bin/env python3
"""Reads CLAUDE.md (the team table) and .claude/agents/*.md, writes office/agents.json for the 3D office.

usage: python3 office/build.py        (run from the repo root, or anywhere: paths are relative to this file)
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS = os.path.join(ROOT, ".claude", "agents")
OUT = os.path.join(ROOT, "office", "agents.json")


def frontmatter(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2).strip()


def departments():
    """Parse the team table in CLAUDE.md: | Team | Head | Workers |  (a row without a backticked head is the lobby)"""
    deps = []
    for line in open(os.path.join(ROOT, "CLAUDE.md"), encoding="utf-8"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 3 or cells[0] in ("Team", "Department", "") or set(cells[0]) <= {"-"}:
            continue
        head = re.findall(r"`([a-z0-9-]+)`", cells[1])
        workers = re.findall(r"`([a-z0-9-]+)`", cells[2])
        deps.append({"name": cells[0], "head": head[0] if head else None, "workers": workers})
    return deps


def brain():
    """The shared memory, so the page can show it (and give it to agents) without the server."""
    path = os.path.join(ROOT, "brain", "memory.jsonl")
    ents = []
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            try:
                o = json.loads(line)
            except Exception:
                continue
            if o.get("type") == "entity":
                ents.append({"name": o.get("name"), "type": o.get("entityType"), "observations": o.get("observations", [])})
    return {"entities": ents, "notes": sum(len(e["observations"]) for e in ents)}


def main():
    files = {f[:-3]: os.path.join(AGENTS, f) for f in sorted(os.listdir(AGENTS)) if f.endswith(".md")}
    deps = departments()
    placed = set()
    out = {"departments": []}
    for d in deps:
        members = []
        if not d["head"]:
            charter = open(os.path.join(ROOT, "CLAUDE.md"), encoding="utf-8").read()
            members.append({"name": "chief-of-staff", "role": "head", "description": "Routes work to the right team, runs agents in parallel, reviews, reports.", "tools": "everything", "model": "the session", "prompt": charter})
        for name in ([d["head"]] if d["head"] else []) + d["workers"]:
            if name not in files:
                print(f"warning: {name} is in CLAUDE.md but has no file", file=sys.stderr)
                continue
            meta, body = frontmatter(files[name])
            members.append({"name": name, "role": "head" if name == d["head"] else "worker",
                            "description": meta.get("description", ""), "tools": meta.get("tools", ""),
                            "model": meta.get("model", "inherit"), "prompt": body})
            placed.add(name)
        out["departments"].append({"name": d["name"], "agents": members})
    missing = sorted(set(files) - placed)
    if missing:
        print(f"warning: not in any team, placed in the lobby: {missing}", file=sys.stderr)
        for name in missing:
            meta, _ = frontmatter(files[name])
            out["departments"][0]["agents"].append({"name": name, "role": "worker", "description": meta.get("description", ""), "tools": meta.get("tools", ""), "model": meta.get("model", "inherit")})
    out["count"] = sum(len(d["agents"]) for d in out["departments"])
    out["brain"] = brain()
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1)
    print(json.dumps({"agents": out["count"], "departments": len(out["departments"]), "out": os.path.relpath(OUT, ROOT)}))


if __name__ == "__main__":
    main()
