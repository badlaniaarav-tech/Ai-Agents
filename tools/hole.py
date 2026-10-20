"""Play a hole with me: every shot on one hole in order, real speed, hard cuts, a two-line white caps label on each
("512 YARDS / PAR 5" on the tee shot, "170 YARDS / 9 IRON" on the next, "22 YARDS / 60 WEDGE" at the green), the real
sound kept, music low. Optional result line at the end ("PAR", "BIRDIE").

usage: python3 tools/hole.py <out.mp4> "<clip>|<line 1>|<line 2>[|<seconds after the key moment>]" ... [--card "hole 15|par 3"] [--intro "come play|1 hole with me"] [--result "par"]
       [--pre 1.3] [--post 3.5] [--zoom 1.12] [--focus 0.5,0.55] [--impacts 3.1,6.6,...] [--mood chill | --track x.mp3] [--music-volume 0.3]
       [--label-pos top|mid]   --card is the hole card at the top of the first shot; every shot's own label sits mid-right. Without --card the first shot's label is the card.
Each shot runs from --pre seconds before its key moment (the strike, found from the loudest sound or --impacts) to --post seconds
after it, or to the end of the clip if shorter, so the ball flight stays in. Prints one JSON line.
"""
import argparse, json, os, random, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from media import FFMPEG, report, run

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("shots", nargs="+", help='"clip|line 1|line 2"')
ap.add_argument("--result", default=""); ap.add_argument("--card", default="", help="hole card on the first shot: \"hole 15|par 3\" or \"512 yards|par 5\""); ap.add_argument("--pre", type=float, default=1.3); ap.add_argument("--post", type=float, default=3.5)
ap.add_argument("--zoom", type=float, default=1.12); ap.add_argument("--focus", default="0.5,0.55"); ap.add_argument("--impacts", default="")
ap.add_argument("--mood", default="chill"); ap.add_argument("--track"); ap.add_argument("--music-volume", type=float, default=0.3); ap.add_argument("--label-pos", choices=["top", "mid"], default="mid")
ap.add_argument("--font", default="Poppins-ExtraBold.ttf", help="file in tools/fonts; Poppins ExtraBold matches the Instagram Strong look of the owner's example"); ap.add_argument("--shadow", type=int, default=8, help="hard shadow offset in px, like the example"); ap.add_argument("--tracking", type=float, default=0.06, help="letter spacing as a fraction of the font size"); ap.add_argument("--size", type=int, default=60, help="shot label size (the example's side label is about a quarter of the frame wide)"); ap.add_argument("--card-size", type=int, default=136); ap.add_argument("--label-x", type=float, default=0.70); ap.add_argument("--label-y", type=float, default=0.55)
ap.add_argument("--intro", default="", help='title card over the tee shot address: "come play|1 hole with me" (big line | small line)'); ap.add_argument("--intro-size", type=int, default=150); ap.add_argument("--intro-seconds", type=float, default=1.2); ap.add_argument("--intro-y", type=float, default=0.22, help="center of the title card as a fraction of the height; 0.22 sits above the golfer")
a = ap.parse_args()
ROOT = os.path.dirname(HERE); FONT = os.path.join(HERE, "fonts", a.font); fx, fy = [float(x) for x in a.focus.split(",")]
IMPS = [float(x) for x in a.impacts.split(",") if x.strip()]

def pcm(path, sr=16000):
    raw = subprocess.run([FFMPEG, "-v", "error", "-i", path, "-map", "0:a:0", "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32)
def info(path):
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,duration:stream_side_data=rotation", "-of", "json", path], capture_output=True, text=True).stdout)["streams"][0]
    w, h = int(pr["width"]), int(pr["height"]); rot = next((abs(int(sd.get("rotation", 0))) for sd in pr.get("side_data_list", []) if "rotation" in sd), 0)
    if rot in (90, 270): w, h = h, w
    s = pcm(path); win = 320; env = np.array([np.abs(s[i:i + win]).max() for i in range(0, len(s) - win, win)]) if len(s) > win else np.zeros(1)
    return w, h, float(pr.get("duration") or 0), float(np.argmax(env) * win / 16000)
def crop(w, h):
    cw, ch = int(w / a.zoom) // 2 * 2, int(h / a.zoom) // 2 * 2; x = min(max(0, int(w * fx - cw / 2)), w - cw); y = min(max(0, int(h * fy - ch / 2)), h - ch)
    return f"crop={cw}:{ch}:{x}:{y},scale=1080:1920:flags=lanczos"
def esc(t): return t.replace("\\", "\\\\").replace("'", r"\'").replace(":", r"\:").replace(",", r"\,")
from PIL import Image, ImageDraw, ImageFont
overlays = []  # (png path, x expr, y expr, start, end)
def make_png(lines, size, sizes=None):
    """Lines of heavy white caps, letter-spaced, with a hard dark shadow offset down-right, like the example. sizes: one size per line."""
    lines = [l.strip().upper() for l in lines if l.strip()]; sizes = sizes or [size] * len(lines); sh = a.shadow
    fonts = [ImageFont.truetype(FONT, z) for z in sizes]; trs = [int(z * a.tracking) for z in sizes]; lhs = [int(z * 1.22) for z in sizes]
    def width(t, f, tr): return sum(int(f.getlength(ch)) + tr for ch in t) - tr
    W_ = max(width(l, f, tr) for l, f, tr in zip(lines, fonts, trs)) + sh + 20; H_ = sum(lhs) + sh + 20
    im = Image.new("RGBA", (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(im); y = 0
    for line, f, tr, lh in zip(lines, fonts, trs, lhs):
        x0 = (W_ - sh - width(line, f, tr)) // 2
        for col, dx, dy in (((26, 31, 43, 220), sh, sh), ((255, 255, 255, 255), 0, 0)):
            x = x0
            for ch in line: d.text((x + dx, y + dy), ch, font=f, fill=col); x += int(f.getlength(ch)) + tr
        y += lh
    return im
def label(lines, pos, start, end, size=None, sizes=None):
    size = size or a.size; im = make_png(lines, size, sizes)
    while im.width > 1080 * 0.92:  # never wider than the frame: shrink every line a step
        sizes = [int(z * 0.94) for z in (sizes or [size] * len(lines))]; im = make_png(lines, size, sizes)
    path = f"{a.out}.label{len(overlays)}.png"; im.save(path)
    x = "(W-w)/2" if pos in ("top", "center") else f"W*{a.label_x}-w/2"; y = "H*0.09" if pos == "top" else (f"H*{a.intro_y}-h/2" if pos == "center" else f"H*{a.label_y}-h/2")
    overlays.append((path, x, y, start, end)); return ""

shots = []
for i, spec in enumerate(a.shots):
    parts = [p.strip() for p in spec.split("|")]; clip = parts[0]; lines = (parts[1:3] + ["", ""])[:2]; post = float(parts[3]) if len(parts) > 3 and parts[3] else a.post
    w, h, dur, imp = info(clip)
    if i < len(IMPS): imp = IMPS[i]
    s0, s1 = max(0.0, imp - a.pre), min(dur, imp + post); shots.append({"clip": clip, "lines": lines, "w": w, "h": h, "s0": s0, "s1": s1, "impact": imp})
inputs, vparts, aparts, t, segs = [], [], [], 0.0, []
for n, sh in enumerate(shots):
    inputs += ["-i", sh["clip"]]; length = sh["s1"] - sh["s0"]
    vparts.append(f"[{n}:v]trim={sh['s0']:.3f}:{sh['s1']:.3f},setpts=PTS-STARTPTS,{crop(sh['w'], sh['h'])},fps=30[v{n}]")
    aparts.append(f"[{n}:a:0]atrim={sh['s0']:.3f}:{sh['s1']:.3f},asetpts=PTS-STARTPTS,volume=1.2[a{n}]")
    segs.append({"clip": os.path.basename(sh["clip"]), "label": " / ".join(l for l in sh["lines"] if l), "impact": round(sh["impact"], 2), "starts_at": round(t, 2), "seconds": round(length, 2)}); t += length
total = t; n = len(shots)
card = [c.strip() for c in a.card.split("|") if c.strip()]
intro = [c.strip() for c in a.intro.split("|") if c.strip()]; intro_end = 0.0
if intro:  # title card centered over the address of the tee shot; the hole card and the first label come in when it leaves
    intro_end = min(a.intro_seconds, max(0.4, shots[0]["impact"] - shots[0]["s0"] - 0.7))
    label(intro, "center", 0.0, intro_end, sizes=[a.intro_size] + [int(a.intro_size * 0.5)] * (len(intro) - 1))
for i, (sh, sg) in enumerate(zip(shots, segs)):
    end = (segs[i + 1]["starts_at"] - 0.04) if i + 1 < n else total + 1  # stop one frame before the next shot so labels never overlap
    start = sg["starts_at"] + (intro_end + 0.04 if i == 0 else 0)
    if i == 0 and card: label(card, "top", start, end, size=a.card_size); label(sh["lines"], a.label_pos, start, end)
    else: label(sh["lines"], "top" if (i == 0 and not card) else a.label_pos, start, end, size=a.card_size if (i == 0 and not card) else None)
if a.result.strip(): label([a.result], "top", max(0.0, total - 1.6), total + 1, size=a.card_size + 20)
vf = ";".join(vparts) + ";" + "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[base]"; prev = "base"
for k, (path, x, y, start, end) in enumerate(overlays):
    vf += f";[{n + k}:v]format=rgba,setpts=PTS-STARTPTS[l{k}];[{prev}][l{k}]overlay=x={x}:y={y}:enable='between(t,{start:.3f},{end:.3f})':format=auto[o{k}]"; prev = f"o{k}"
vf += f";[{prev}]format=yuv420p[v]"
af = ";".join(aparts) + ";" + "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1,alimiter=limit=0.95[clip]"
track = a.track
if not track and a.music_volume > 0:
    folder = os.path.join(ROOT, "music"); files = [f for f in (os.listdir(folder) if os.path.isdir(folder) else []) if f.lower().endswith((".mp3", ".wav", ".m4a"))]
    tagged = [f for f in files if f.lower().startswith(a.mood.lower() + "-")]; files = tagged or files; track = os.path.join(folder, random.choice(files)) if files else None
if track and a.music_volume > 0:
    inputs += ["-i", track]; af += f";[{n}:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,volume={a.music_volume},afade=t=in:d=0.6,afade=t=out:st={max(0, total - 1.5):.3f}:d=1.5[m];[clip][m]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]"
else: af += ";[clip]anull[a]"
os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True); tmpv, tmpa = a.out + ".video.mp4", a.out + ".audio.m4a"
vin = inputs[: 2 * n]
for path, *_ in overlays: vin += ["-loop", "1", "-t", f"{total:.3f}", "-i", path]
run([*vin, "-filter_complex", vf, "-map", "[v]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-profile:v", "high", "-level", "4.0", "-an", tmpv])
run([*inputs, "-filter_complex", af, "-map", "[a]", "-vn", "-c:a", "aac", "-b:a", "160k", tmpa])
run(["-i", tmpv, "-i", tmpa, "-map", "0:v", "-map", "1:a", "-c", "copy", "-movflags", "+faststart", a.out])
for f in [tmpv, tmpa] + [o[0] for o in overlays]:
    try: os.remove(f)
    except OSError: pass
report(tool="hole", out=a.out, seconds=round(total, 2), shots=segs, card=" / ".join(card), intro=" / ".join(intro), result=a.result.strip(), track=os.path.basename(track) if track else "", music_volume=a.music_volume if track else 0)
