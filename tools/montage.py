"""Swing montage, like the golf reels the owner follows: one text line held the whole way, the first swing in slow
motion, then the other swings cut fast on the strike, the real crack of the ball as the sound, music low under it.

usage: python3 tools/montage.py <out.mp4> <clip1> <clip2> ... [--label "Addicted to this sound"] [--mood hype | --track x.mp3]
       [--music-volume 0.25] [--slow 2.0] [--pre-first 1.4] [--post-first 0.5] [--pre 0.9] [--post 0.35] [--zoom 1.3] [--focus 0.5,0.52] [--label-y 0.24]
The strike in each clip is found from its loudest moment. Prints one JSON line.
"""
import argparse, json, os, random, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from media import FFMPEG, report, run

ap = argparse.ArgumentParser()
ap.add_argument("out"); ap.add_argument("clips", nargs="+")
ap.add_argument("--label", default="Addicted to this sound"); ap.add_argument("--mood", default="hype"); ap.add_argument("--track"); ap.add_argument("--music-volume", type=float, default=0.25)
ap.add_argument("--slow", type=float, default=2.0); ap.add_argument("--pre-first", type=float, default=1.4); ap.add_argument("--post-first", type=float, default=0.5)
ap.add_argument("--pre", type=float, default=0.9); ap.add_argument("--post", type=float, default=0.35); ap.add_argument("--zoom", type=float, default=1.3); ap.add_argument("--focus", default="0.5,0.52"); ap.add_argument("--label-y", type=float, default=0.24, help="label height as a fraction of the frame; keep it above the golfer")
a = ap.parse_args()
ROOT = os.path.dirname(HERE); FONT = os.path.join(HERE, "fonts", "Geist.ttf")
fx, fy = [float(x) for x in a.focus.split(",")]

def pcm(path, sr=16000):
    raw = subprocess.run([FFMPEG, "-v", "error", "-i", path, "-map", "0:a:0", "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32)
def info(path):
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,duration:stream_side_data=rotation", "-of", "json", path], capture_output=True, text=True).stdout)["streams"][0]
    W, H = int(pr["width"]), int(pr["height"]); rot = next((abs(int(sd.get("rotation", 0))) for sd in pr.get("side_data_list", []) if "rotation" in sd), 0)
    if rot in (90, 270): W, H = H, W
    s = pcm(path); w = 320; env = np.array([np.abs(s[i:i + w]).max() for i in range(0, len(s) - w, w)])
    return W, H, float(pr.get("duration") or 0), float(np.argmax(env) * w / 16000)
def crop(W, H):
    cw, ch = int(W / a.zoom) // 2 * 2, int(H / a.zoom) // 2 * 2
    x = min(max(0, int(W * fx - cw / 2)), W - cw); y = min(max(0, int(H * fy - ch / 2)), H - ch)
    return f"crop={cw}:{ch}:{x}:{y},scale=1080:1920:flags=lanczos"

segs, vparts, aparts, inputs, t = [], [], [], [], 0.0
for n, clip in enumerate(a.clips):
    W, H, dur, imp = info(clip); inputs += ["-i", clip]
    first = n == 0; pre, post = (a.pre_first, a.post_first) if first else (a.pre, a.post); slow = a.slow if first else 1.0
    s0, s1 = max(0.0, imp - pre), min(dur, imp + post); length = (s1 - s0) * slow; imp_at = t + (imp - s0) * slow
    vparts.append(f"[{n}:v]trim={s0:.3f}:{s1:.3f},setpts=(PTS-STARTPTS)*{slow},{crop(W, H)},fps=30[v{n}]")
    if first and slow > 1:  # ambient slowed and low, the crack at full speed on the contact frame
        c0, c1 = max(0.0, imp - 0.04), min(dur, imp + 0.3); at = int(max(0, (imp - s0) * slow - 0.04 * slow) * 1000)
        aparts.append(f"[{n}:a:0]atrim={s0:.3f}:{s1:.3f},asetpts=PTS-STARTPTS,atempo={max(0.5, 1 / slow):.3f},volume=0.35[amb{n}];[{n}:a:0]atrim={c0:.3f}:{c1:.3f},asetpts=PTS-STARTPTS,volume=1.5,adelay={at}|{at}[cr{n}];[amb{n}][cr{n}]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a{n}]")
    else:
        aparts.append(f"[{n}:a:0]atrim={s0:.3f}:{s1:.3f},asetpts=PTS-STARTPTS,volume=1.3[a{n}]")
    segs.append({"clip": os.path.basename(clip), "impact": round(imp, 2), "from": round(s0, 2), "to": round(s1, 2), "slow": slow, "starts_at": round(t, 2)}); t += length
total = t; n = len(a.clips)
label = ""
if a.label.strip():
    esc = a.label.strip().replace("'", r"\'").replace(":", r"\:")
    label = f",drawtext=fontfile={FONT}:text='{esc}':fontsize=66:fontcolor=white:borderw=3:bordercolor=black@0.55:shadowcolor=black@0.5:shadowx=2:shadowy=3:x=(w-text_w)/2:y=h*{a.label_y}"
vf = ";".join(vparts) + ";" + "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0{label},format=yuv420p[v]"
af = ";".join(aparts) + ";" + "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1,alimiter=limit=0.95[clip]"
track = a.track
if not track and a.music_volume > 0:
    folder = os.path.join(ROOT, "music"); files = [f for f in (os.listdir(folder) if os.path.isdir(folder) else []) if f.lower().endswith((".mp3", ".wav", ".m4a"))]
    tagged = [f for f in files if f.lower().startswith(a.mood.lower() + "-")]; files = tagged or files
    track = os.path.join(folder, random.choice(files)) if files else None
if track and a.music_volume > 0:
    inputs += ["-i", track]
    af += f";[{n}:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,volume={a.music_volume},afade=t=in:d=0.5,afade=t=out:st={max(0, total - 1.2):.3f}:d=1.2[m];[clip][m]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]"
else:
    af += ";[clip]anull[a]"
os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
tmpv, tmpa = a.out + ".video.mp4", a.out + ".audio.m4a"
run([*inputs[: 2 * n], "-filter_complex", vf, "-map", "[v]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-profile:v", "high", "-level", "4.0", "-an", tmpv])
run([*inputs, "-filter_complex", af, "-map", "[a]", "-vn", "-c:a", "aac", "-b:a", "160k", tmpa])
run(["-i", tmpv, "-i", tmpa, "-map", "0:v", "-map", "1:a", "-c", "copy", "-movflags", "+faststart", a.out])
for f in (tmpv, tmpa):
    try: os.remove(f)
    except OSError: pass
report(tool="montage", out=a.out, seconds=round(total, 2), clips=len(a.clips), label=a.label.strip(), segments=segs, track=os.path.basename(track) if track else "", music_volume=a.music_volume if track else 0)
