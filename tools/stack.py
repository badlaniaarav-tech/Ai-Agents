"""Angles stacked: two or three clips of the same swing from different angles, stacked in horizontal strips that play
at once, synced on the strike. Several reps follow each other (every --rows clips form one rep). Like the "aesthetic
reps" reels: moody grade, calm music low, one small label or none.

usage: python3 tools/stack.py <out.mp4> <rep1-angleA> <rep1-angleB> <rep1-angleC> [<rep2-angleA> ...] [--rows 3]
       [--pre 1.4] [--post 1.6] [--slow 1.0] [--label "aesthetic reps"] [--grade moody|none] [--mood chill | --track x.mp3] [--music-volume 0.35]
       [--focus "0.5,0.52;0.5,0.5;0.5,0.4"]  (one x,y per row, where the golfer or the ball is in that angle)
Each clip's key moment is found from its loudest moment (or --impacts), so the rows line up on it. Prints one JSON line.
"""
import argparse, json, os, random, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from media import FFMPEG, report, run

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("clips", nargs="+")
ap.add_argument("--rows", type=int, default=3); ap.add_argument("--pre", type=float, default=1.4); ap.add_argument("--post", type=float, default=1.6); ap.add_argument("--slow", type=float, default=1.0)
ap.add_argument("--label", default=""); ap.add_argument("--grade", choices=["moody", "none"], default="moody"); ap.add_argument("--mood", default="chill"); ap.add_argument("--track"); ap.add_argument("--music-volume", type=float, default=0.35)
ap.add_argument("--impacts", default="", help="key moment per clip in seconds, comma separated, when the loudest sound is not it"); ap.add_argument("--focus", default="0.5,0.52;0.5,0.5;0.5,0.5"); ap.add_argument("--label-y", type=float, default=0.06)
a = ap.parse_args()
ROOT = os.path.dirname(HERE); FONT = os.path.join(HERE, "fonts", "Geist.ttf")
W, H = 1080, 1920; rows = max(2, min(3, a.rows)); RH = H // rows; RH -= RH % 2
focus = [[float(x) for x in f.split(",")] for f in a.focus.split(";")]; focus += [[0.5, 0.5]] * (rows - len(focus))
if len(a.clips) % rows: print(json.dumps({"tool": "stack", "error": f"give clips in groups of {rows} (one per angle); got {len(a.clips)}"})); sys.exit(1)

def pcm(path, sr=16000):
    raw = subprocess.run([FFMPEG, "-v", "error", "-i", path, "-map", "0:a:0", "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32)
def info(path):
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,duration:stream_side_data=rotation", "-of", "json", path], capture_output=True, text=True).stdout)["streams"][0]
    w, h = int(pr["width"]), int(pr["height"]); rot = next((abs(int(sd.get("rotation", 0))) for sd in pr.get("side_data_list", []) if "rotation" in sd), 0)
    if rot in (90, 270): w, h = h, w
    s = pcm(path); win = 320; env = np.array([np.abs(s[i:i + win]).max() for i in range(0, len(s) - win, win)]) if len(s) > win else np.zeros(1)
    return w, h, float(pr.get("duration") or 0), float(np.argmax(env) * win / 16000)
def strip(w, h, fx, fy):
    """Crop the biggest W:RH box around the focus point, then scale to the strip."""
    ar = W / RH
    if w / h > ar: ch, cw = h, int(h * ar)
    else: cw, ch = w, int(w / ar)
    cw -= cw % 2; ch -= ch % 2; x = min(max(0, int(w * fx - cw / 2)), w - cw); y = min(max(0, int(h * fy - ch / 2)), h - ch)
    return f"crop={cw}:{ch}:{x}:{y},scale={W}:{RH}:flags=lanczos"
grade = ",eq=contrast=1.08:saturation=0.8:brightness=-0.02,curves=preset=darker" if a.grade == "moody" else ""

IMPS = [float(x) for x in a.impacts.split(",") if x.strip()]
reps = [a.clips[i:i + rows] for i in range(0, len(a.clips), rows)]; inputs = []; vparts = []; aparts = []; segs = []; t = 0.0; n = 0
for r, group in enumerate(reps):
    infos = [info(c) for c in group]; infos = [(w, h, d, IMPS[r * rows + k]) if r * rows + k < len(IMPS) else (w, h, d, i) for k, (w, h, d, i) in enumerate(infos)]; pre = min([a.pre] + [i[3] for i in infos]); post = min([a.post] + [i[2] - i[3] for i in infos]); length = (pre + post) * a.slow
    row_labels = []
    for k, (clip, (w, h, dur, imp)) in enumerate(zip(group, infos)):
        inputs += ["-i", clip]; s0, s1 = imp - pre, imp + post
        vparts.append(f"[{n}:v]trim={s0:.3f}:{s1:.3f},setpts=(PTS-STARTPTS)*{a.slow},{strip(w, h, *focus[k])}{grade}[r{n}]"); row_labels.append(f"[r{n}]")
        if k == 0: aparts.append(f"[{n}:a:0]atrim={s0:.3f}:{s1:.3f},asetpts=PTS-STARTPTS{',atempo=' + format(max(0.5, 1 / a.slow), '.3f') if a.slow != 1 else ''},volume=1.2[a{r}]")
        n += 1
    vparts.append("".join(row_labels) + f"vstack=inputs={rows}[s{r}]"); segs.append({"rep": r + 1, "clips": [os.path.basename(c) for c in group], "impacts": [round(i[3], 2) for i in infos], "starts_at": round(t, 2), "seconds": round(length, 2)}); t += length
total = t
label = ""
if a.label.strip():
    esc = a.label.strip().replace("'", r"\'").replace(":", r"\:")
    label = f",drawtext=fontfile={FONT}:text='{esc}':fontsize=44:fontcolor=#16181f:box=1:boxcolor=white@0.96:boxborderw=20:x=(w-text_w)/2:y=h*{a.label_y}"
vf = ";".join(vparts) + ";" + "".join(f"[s{r}]" for r in range(len(reps))) + f"concat=n={len(reps)}:v=1:a=0{label},fps=30,format=yuv420p[v]"
af = ";".join(aparts) + ";" + "".join(f"[a{r}]" for r in range(len(reps))) + f"concat=n={len(reps)}:v=0:a=1,alimiter=limit=0.95[clip]"
track = a.track
if not track and a.music_volume > 0:
    folder = os.path.join(ROOT, "music"); files = [f for f in (os.listdir(folder) if os.path.isdir(folder) else []) if f.lower().endswith((".mp3", ".wav", ".m4a"))]
    tagged = [f for f in files if f.lower().startswith(a.mood.lower() + "-")]; files = tagged or files; track = os.path.join(folder, random.choice(files)) if files else None
if track and a.music_volume > 0:
    inputs += ["-i", track]; af += f";[{n}:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,volume={a.music_volume},afade=t=in:d=0.6,afade=t=out:st={max(0, total - 1.2):.3f}:d=1.2[m];[clip][m]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]"
else: af += ";[clip]anull[a]"
os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True); tmpv, tmpa = a.out + ".video.mp4", a.out + ".audio.m4a"
run([*inputs[: 2 * n], "-filter_complex", vf, "-map", "[v]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-profile:v", "high", "-level", "4.0", "-an", tmpv])
run([*inputs, "-filter_complex", af, "-map", "[a]", "-vn", "-c:a", "aac", "-b:a", "160k", tmpa])
run(["-i", tmpv, "-i", tmpa, "-map", "0:v", "-map", "1:a", "-c", "copy", "-movflags", "+faststart", a.out])
for f in (tmpv, tmpa):
    try: os.remove(f)
    except OSError: pass
report(tool="stack", out=a.out, seconds=round(total, 2), rows=rows, reps=segs, label=a.label.strip(), grade=a.grade, track=os.path.basename(track) if track else "", music_volume=a.music_volume if track else 0)
