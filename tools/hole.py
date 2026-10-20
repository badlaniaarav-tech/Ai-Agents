"""Play a hole with me: every shot on one hole in order, real speed, hard cuts, a two-line white caps label on each
("512 YARDS / PAR 5" on the tee shot, "170 YARDS / 9 IRON" on the next, "22 YARDS / 60 WEDGE" at the green), the real
sound kept, music low. Optional result line at the end ("PAR", "BIRDIE").

usage: python3 tools/hole.py <out.mp4> "<clip>|<line 1>|<line 2>[|<seconds after the key moment>]" ... [--card "hole 15|par 3"] [--result "par"]
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
a = ap.parse_args()
ROOT = os.path.dirname(HERE); FONT = os.path.join(HERE, "fonts", "Geist.ttf"); fx, fy = [float(x) for x in a.focus.split(",")]
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
def label(lines, pos, start, end, size=96):
    """Two lines of bold white caps with a soft shadow. top: centred near the top (the hole card). mid: right of centre, mid height."""
    out = ""; en = f":enable='between(t,{start:.3f},{end:.3f})'"; bw = max(2, size // 14)
    for i, line in enumerate([l for l in lines if l.strip()]):
        txt = esc(line.strip().upper()); y = (f"h*0.11+{i * size * 1.1}" if pos == "top" else f"h*0.47+{i * size * 1.1}"); x = "(w-text_w)/2" if pos == "top" else f"w*0.73-text_w/2"
        out += f",drawtext=fontfile={FONT}:text='{txt}':fontsize={size}:fontcolor=black@0.45:borderw={bw}:bordercolor=black@0.45:x={x}+6:y={y}+8{en}"
        out += f",drawtext=fontfile={FONT}:text='{txt}':fontsize={size}:fontcolor=white:borderw={bw}:bordercolor=white:x={x}:y={y}{en}"
    return out

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
labels = ""
card = [c.strip() for c in a.card.split("|") if c.strip()]
for i, (sh, sg) in enumerate(zip(shots, segs)):
    end = (segs[i + 1]["starts_at"] - 0.04) if i + 1 < n else total + 1  # stop one frame before the next shot so labels never overlap
    if i == 0 and card: labels += label(card, "top", sg["starts_at"], end, size=104) + label(sh["lines"], a.label_pos, sg["starts_at"], end, size=88)
    else: labels += label(sh["lines"], "top" if (i == 0 and not card) else a.label_pos, sg["starts_at"], end, size=104 if (i == 0 and not card) else 88)
if a.result.strip(): labels += label([a.result], "top", max(0.0, total - 1.6), total + 1, size=120)
vf = ";".join(vparts) + ";" + "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0{labels},format=yuv420p[v]"
af = ";".join(aparts) + ";" + "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1,alimiter=limit=0.95[clip]"
track = a.track
if not track and a.music_volume > 0:
    folder = os.path.join(ROOT, "music"); files = [f for f in (os.listdir(folder) if os.path.isdir(folder) else []) if f.lower().endswith((".mp3", ".wav", ".m4a"))]
    tagged = [f for f in files if f.lower().startswith(a.mood.lower() + "-")]; files = tagged or files; track = os.path.join(folder, random.choice(files)) if files else None
if track and a.music_volume > 0:
    inputs += ["-i", track]; af += f";[{n}:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,volume={a.music_volume},afade=t=in:d=0.6,afade=t=out:st={max(0, total - 1.5):.3f}:d=1.5[m];[clip][m]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]"
else: af += ";[clip]anull[a]"
os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True); tmpv, tmpa = a.out + ".video.mp4", a.out + ".audio.m4a"
run([*inputs[: 2 * n], "-filter_complex", vf, "-map", "[v]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-profile:v", "high", "-level", "4.0", "-an", tmpv])
run([*inputs, "-filter_complex", af, "-map", "[a]", "-vn", "-c:a", "aac", "-b:a", "160k", tmpa])
run(["-i", tmpv, "-i", tmpa, "-map", "0:v", "-map", "1:a", "-c", "copy", "-movflags", "+faststart", a.out])
for f in (tmpv, tmpa):
    try: os.remove(f)
    except OSError: pass
report(tool="hole", out=a.out, seconds=round(total, 2), shots=segs, card=" / ".join(card), result=a.result.strip(), track=os.path.basename(track) if track else "", music_volume=a.music_volume if track else 0)
