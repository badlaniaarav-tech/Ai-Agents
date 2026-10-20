"""YouTube research without a key, through the JSON endpoint the site itself uses.

usage: python3 tools/yt.py search "<query>" [--shorts] [--n 30]      -> one JSON line per video: id, title, views, channel, length, published, url
       python3 tools/yt.py sheet "<query>" <out.jpg> [--shorts] [--n 12] -> the top results' thumbnails tiled with title and views, to see the text and framing people use
The video pages and streams themselves are sign-in gated from a server, so titles, views, lengths and thumbnails are what we get.
Read-only research for the idea-scout. Nothing is uploaded or posted.
"""
import argparse, json, os, re, subprocess, sys, urllib.request
os.environ.setdefault("SSL_CERT_FILE", "/root/.ccr/ca-bundle.crt")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
def call(endpoint, body, client=("WEB", "2.20241010.01.00")):
    body = {"context": {"client": {"clientName": client[0], "clientVersion": client[1], "hl": "en", "gl": "US"}}, **body}
    req = urllib.request.Request(f"https://www.youtube.com/youtubei/v1/{endpoint}?prettyPrint=false", data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "User-Agent": UA})
    return json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
def text(o):
    if not o: return ""
    if isinstance(o, str): return o
    return o.get("simpleText") or "".join(r.get("text", "") for r in o.get("runs", [])) or o.get("content", "")
def walk(o, keys):
    if isinstance(o, dict):
        for k in keys:
            if k in o: yield k, o[k]
        for v in o.values(): yield from walk(v, keys)
    elif isinstance(o, list):
        for v in o: yield from walk(v, keys)
def views_num(s):
    m = re.search(r"([\d.,]+)\s*([KMB])?", s or ""); 
    if not m: return None
    n = float(m.group(1).replace(",", "")); return int(n * {"K": 1e3, "M": 1e6, "B": 1e9}.get(m.group(2), 1))

ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd")
s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("--shorts", action="store_true"); s.add_argument("--n", type=int, default=30)
t = sub.add_parser("sheet"); t.add_argument("query"); t.add_argument("out"); t.add_argument("--shorts", action="store_true"); t.add_argument("--n", type=int, default=12)
a = ap.parse_args()

def search(query, shorts, n):
    body = {"query": query}
    if shorts: body["params"] = "EgIYAQ%3D%3D"  # short videos filter
    d = call("search", body); out = []; seen = set()
    for k, v in walk(d, ["videoRenderer", "reelItemRenderer", "shortsLockupViewModel"]):
        vid = v.get("videoId") or ((v.get("onTap") or {}).get("innertubeCommand") or {}).get("reelWatchEndpoint", {}).get("videoId")
        if not vid or vid in seen: continue
        seen.add(vid)
        title = text(v.get("title")) or text((v.get("overlayMetadata") or {}).get("primaryText")) or text(v.get("headline"))
        views = text(v.get("viewCountText")) or text((v.get("overlayMetadata") or {}).get("secondaryText"))
        thumbs = ((v.get("thumbnail") or {}).get("thumbnails") or (((v.get("thumbnail") or {}).get("sources")) or [])) or []
        thumb = thumbs[-1].get("url") if thumbs else f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
        out.append({"id": vid, "title": title, "views": views_num(views), "views_text": views, "channel": text(v.get("ownerText")) or text(v.get("longBylineText")), "length": text(v.get("lengthText")), "published": text(v.get("publishedTimeText")), "url": f"https://www.youtube.com/watch?v={vid}", "thumb": thumb})
        if len(out) >= n: break
    return out

if a.cmd == "search":
    for o in search(a.query, a.shorts, a.n): print(json.dumps(o))
elif a.cmd == "sheet":
    from PIL import Image, ImageDraw, ImageFont
    items = search(a.query, a.shorts, a.n); tiles = []
    font = ImageFont.truetype(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Geist.ttf"), 13)
    for it in items:
        try:
            raw = urllib.request.urlopen(urllib.request.Request(it["thumb"], headers={"User-Agent": UA}), timeout=30).read()
            im = Image.open(__import__("io").BytesIO(raw)).convert("RGB")
        except Exception: continue
        im.thumbnail((240, 240)); tile = Image.new("RGB", (240, 240 + 48), (10, 12, 18)); tile.paste(im, ((240 - im.width) // 2, 0)); d = ImageDraw.Draw(tile)
        d.text((4, 242), (it["title"] or "")[:34], font=font, fill=(235, 235, 235)); d.text((4, 258), f"{it['views_text'] or '?'} · {it['length'] or ''} · {(it['channel'] or '')[:18]}", font=font, fill=(160, 170, 190)); tiles.append(tile)
    if not tiles: print(json.dumps({"tool": "yt", "error": "no thumbnails"})); sys.exit(1)
    cols = min(4, len(tiles)); rows = (len(tiles) + cols - 1) // cols; sheet = Image.new("RGB", (cols * 244, rows * 292), (10, 12, 18))
    for i, t in enumerate(tiles): sheet.paste(t, ((i % cols) * 244, (i // cols) * 292))
    sheet.save(a.out, quality=85); print(json.dumps({"tool": "yt", "out": a.out, "query": a.query, "videos": len(tiles), "top": [{"title": x["title"], "views": x["views_text"], "url": x["url"]} for x in items[:5]]}))
