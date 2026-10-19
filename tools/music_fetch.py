"""Fetch Creative Commons tracks for one mood from the Free Music Archive into music/.

usage: python3 tools/music_fetch.py --mood hype --terms "phonk,trap,drill" [--count 3] [--replace] [--min 45] [--max 360]
Keeps only CC BY, CC BY-SA and CC0 tracks. --replace deletes that mood's existing tracks first (weekly rotation).
Rewrites music/credits.md from the files that remain. Prints one JSON line.
"""
import argparse, json, os, re, subprocess, sys, time, urllib.parse, urllib.request

ap = argparse.ArgumentParser()
ap.add_argument("--mood", required=True); ap.add_argument("--terms", required=True, help="comma separated search words")
ap.add_argument("--count", type=int, default=3); ap.add_argument("--replace", action="store_true")
ap.add_argument("--min", type=int, default=45); ap.add_argument("--max", type=int, default=360)
a = ap.parse_args()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, "music"); os.makedirs(OUT, exist_ok=True)
CRED = os.path.join(OUT, "credits.json")
H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
OK = {"by": "CC BY", "by-sa": "CC BY-SA", "zero": "CC0"}
mood = re.sub(r"[^a-z]", "", a.mood.lower())

def get(u, binary=False):
    r = urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=60); d = r.read(); return d if binary else d.decode("utf-8", "ignore")

credits = json.load(open(CRED)) if os.path.exists(CRED) else {}
removed = []
if a.replace:
    for f in sorted(os.listdir(OUT)):
        if f.startswith(mood + "-") and f.lower().endswith((".mp3", ".wav", ".m4a")):
            os.remove(os.path.join(OUT, f)); removed.append(f); credits.pop(f, None)
have = [f for f in os.listdir(OUT) if f.startswith(mood + "-") and f.lower().endswith(".mp3")]
added, seen, errors = [], set(), []
for term in [t.strip() for t in a.terms.split(",") if t.strip()]:
    if len(have) >= a.count: break
    for page in (1, 2):
        if len(have) >= a.count: break
        try: d = get("https://freemusicarchive.org/search/?quicksearch=" + urllib.parse.quote(term) + "&page=" + str(page))
        except Exception as e: errors.append(f"search {term}: {e}"); break
        for raw in re.findall(r"data-track-info='(.*?)'", d):
            if len(have) >= a.count: break
            try: it = json.loads(raw.replace("&quot;", '"'))
            except Exception: continue
            if it["id"] in seen: continue
            seen.add(it["id"])
            i = d.find("tid-" + it["id"]); m = re.search(r"(\d+):(\d\d)", re.sub(r"<[^>]+>", " ", d[i:i + 6000]))
            secs = int(m.group(1)) * 60 + int(m.group(2)) if m else 0
            if not (a.min <= secs <= a.max): continue
            try: page_html = get(it["url"])
            except Exception: continue
            lm = re.search(r"creativecommons\.org/(?:licenses|publicdomain)/([a-z-]+)/", page_html)
            lic = lm.group(1) if lm else None
            if lic not in OK: continue
            name = f"{mood}-{re.sub(r'[^a-z0-9]+', '-', it['handle'].lower()).strip('-')[:40]}.mp3"
            if name in have or any(c.get("id") == it["id"] for c in credits.values()): continue
            try:
                data = get(it["playbackUrl"], binary=True)
                if len(data) < 200000: continue
                path = os.path.join(OUT, name); open(path, "wb").write(data)
                dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
                if not dur: os.remove(path); continue
                credits[name] = {"id": it["id"], "mood": mood, "title": it["title"], "artist": it["artistName"], "license": OK[lic], "seconds": round(float(dur)), "source": it["url"], "added": time.strftime("%Y-%m-%d")}
                have.append(name); added.append(name)
            except Exception as e: errors.append(f"download {it['title']}: {e}")
            time.sleep(0.6)

# credits.md from what is on disk
credits = {f: c for f, c in credits.items() if os.path.exists(os.path.join(OUT, f))}
json.dump(credits, open(CRED, "w"), indent=1)
with open(os.path.join(OUT, "credits.md"), "w") as f:
    f.write("# Music credits\n\nTracks in this folder, from the Free Music Archive, kept fresh weekly by the Music team. CC BY and CC BY-SA need a credit line in the caption or description: \"Music: <title> by <artist>, <license>\".\n\n| mood | file | title | artist | license | seconds | added | source |\n|---|---|---|---|---|---|---|---|\n")
    for name, c in sorted(credits.items(), key=lambda x: (x[1]["mood"], x[0])):
        f.write(f"| {c['mood']} | `{name}` | {c['title']} | {c['artist']} | {c['license']} | {c['seconds']} | {c.get('added', '')} | {c['source']} |\n")
print(json.dumps({"tool": "music_fetch", "mood": mood, "added": [{"file": n, "title": credits[n]["title"], "artist": credits[n]["artist"], "license": credits[n]["license"]} for n in added], "removed": removed, "now": sorted(have), "errors": errors[:5]}))
sys.exit(0 if len(have) >= a.count else 1)
