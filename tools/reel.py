"""Viral-style swing reel: tight framing, a hook line, slow-motion punch-in with a flash at impact,
a music drop on the strike, and the finish held with cover-style text.

usage: python3 tools/reel.py <in.mov> <out.mp4> [--impact 6.64] [--hook "LAST SWING|BEFORE DARK"] [--end "HOLD THE|FINISH"]
       [--mood hype | --track music/x.mp3] [--music-volume 0.5] [--focus 0.53,0.52] [--zoom 1.3] [--punch 1.6] [--slow 3.3]
       [--lead 1.6] [--pre 1.2] [--post 0.3] [--hold 2.8]
--impact defaults to the loudest 20 ms in the clip (the ball strike). The music drop is found automatically (biggest jump
in loudness in the first 45 s) and lined up with the impact. Text uses the brand style: all caps, last line yellow.
Prints one JSON line.
"""
import argparse, json, os, random, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from media import FFMPEG, report, run

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--impact", type=float); ap.add_argument("--hook", default="LAST SWING|BEFORE DARK"); ap.add_argument("--end", default="HOLD THE|FINISH")
ap.add_argument("--mood", default="hype"); ap.add_argument("--track"); ap.add_argument("--music-volume", type=float, default=0.5)
ap.add_argument("--focus", default="0.53,0.52", help="where the golfer is, as fractions of width,height"); ap.add_argument("--zoom", type=float, default=1.3); ap.add_argument("--punch", type=float, default=1.6)
ap.add_argument("--slow", type=float, default=3.3, help="slow-motion factor at impact"); ap.add_argument("--lead", type=float, default=1.6, help="seconds of address shown first (the hook)")
ap.add_argument("--pre", type=float, default=1.2, help="seconds before impact at normal speed"); ap.add_argument("--post", type=float, default=0.3, help="seconds after impact in slow motion")
ap.add_argument("--hold", type=float, default=2.8, help="seconds of finish after the slow motion"); ap.add_argument("--color", default="#FFD400")
a = ap.parse_args()
ROOT = os.path.dirname(HERE); FONT = os.path.join(HERE, "fonts", "Geist.ttf")

def pcm(path, sr=16000, extra=()):
    raw = subprocess.run([FFMPEG, "-v", "error", "-i", path, *extra, "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32)

# dimensions after the phone's rotation flag
pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,duration:stream_side_data=rotation", "-of", "json", a.src], capture_output=True, text=True).stdout)["streams"][0]
W, H = int(pr["width"]), int(pr["height"]); rot = next((abs(int(sd.get("rotation", 0))) for sd in pr.get("side_data_list", []) if "rotation" in sd), 0)
if rot in (90, 270): W, H = H, W
dur = float(pr.get("duration") or 0)

# impact = loudest 20 ms
clip = pcm(a.src, extra=("-map", "0:a:0")); w = 320
env = np.array([np.abs(clip[i:i + w]).max() for i in range(0, len(clip) - w, w)])
impact = a.impact if a.impact is not None else float(np.argmax(env) * w / 16000)

# segments in the source
A0, A1 = 0.0, min(a.lead, max(0.3, impact - a.pre - 0.2))
B0, B1 = max(A1, impact - a.pre), impact - 0.12
C0, C1 = B1, impact + a.post
D0, D1 = C1, min(dur, C1 + a.hold)
tA, tB, tC, tD = A1 - A0, B1 - B0, (C1 - C0) * a.slow, D1 - D0
impact_at = tA + tB + 0.12 * a.slow  # where the strike lands in the edit
total = tA + tB + tC + tD

# music: pick a track, find its drop, line it up with the impact
track = a.track
if not track:
    folder = os.path.join(ROOT, "music"); files = [f for f in (os.listdir(folder) if os.path.isdir(folder) else []) if f.lower().endswith((".mp3", ".wav", ".m4a"))]
    tagged = [f for f in files if f.lower().startswith(a.mood.lower() + "-")]; files = tagged or files
    track = os.path.join(folder, random.choice(files)) if files else None
drop = 0.0
if track:
    m = pcm(track); hop = 800  # 50 ms
    rms = np.array([np.sqrt(np.mean(m[i:i + hop] ** 2)) for i in range(0, min(len(m), 16000 * 45) - hop, hop)])
    if len(rms) > 20:
        before = np.array([rms[max(0, i - 10):i].mean() for i in range(len(rms))]); after = np.array([rms[i:i + 10].mean() for i in range(len(rms))])
        jump = after - before; jump[:4] = 0; drop = float(np.argmax(jump) * hop / 16000)
music_offset = max(0.0, drop - impact_at)

fx, fy = [float(x) for x in a.focus.split(",")]
def crop(z):
    cw, ch = int(W / z) // 2 * 2, int(H / z) // 2 * 2
    x = min(max(0, int(W * fx - cw / 2)), W - cw); y = min(max(0, int(H * fy - ch / 2)), H - ch)
    return f"crop={cw}:{ch}:{x}:{y},scale=1080:1920:flags=lanczos"
def text(lines, y0, size=150, start=0.0, end=None):
    out = []; y = y0
    for i, line in enumerate(lines):
        col = a.color if i == len(lines) - 1 else "white"; en = f":enable='between(t,{start},{end})'" if end else f":enable='gte(t,{start})'"
        esc = line.replace("'", r"\'").replace(":", r"\:")
        out.append(f"drawtext=fontfile={FONT}:text='{esc}':fontsize={size}:fontcolor=black@0.75:borderw=7:bordercolor=black@0.75:x=(w-text_w)/2+7:y={y + 9}{en}")
        out.append(f"drawtext=fontfile={FONT}:text='{esc}':fontsize={size}:fontcolor={col}:borderw=7:bordercolor={col}:x=(w-text_w)/2:y={y}{en}")
        y += int(size * 1.05)
    return "," + ",".join(out) if out else ""
hook = [s.strip().upper() for s in a.hook.split("|") if s.strip()]; endt = [s.strip().upper() for s in a.end.split("|") if s.strip()]
vf = (f"[0:v]trim={A0}:{A1},setpts=PTS-STARTPTS,{crop(a.zoom)}{text(hook, 180, start=0.15)}[va];"
      f"[0:v]trim={B0}:{B1},setpts=PTS-STARTPTS,{crop(a.zoom)}[vb];"
      f"[0:v]trim={C0}:{C1},setpts=(PTS-STARTPTS)*{a.slow},{crop(a.punch)},minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:vsbmc=1,fade=t=in:st=0:d=0.12:color=white[vc];"
      f"[0:v]trim={D0}:{D1},setpts=PTS-STARTPTS,{crop(a.zoom)}{text(endt, 180, start=0.5)}[vd];"
      f"[va][vb][vc][vd]concat=n=4:v=1:a=0,fps=30,format=yuv420p[v]")
# clip sound: normal for A, B, D; the strike stretched for C
af = (f"[0:a:0]atrim={A0}:{A1},asetpts=PTS-STARTPTS[aa];[0:a:0]atrim={B0}:{B1},asetpts=PTS-STARTPTS[ab];"
      f"[0:a:0]atrim={C0}:{C1},asetpts=PTS-STARTPTS,atempo=0.5,atempo={max(0.5, 1 / (a.slow / 2)):.3f}[ac];[0:a:0]atrim={D0}:{D1},asetpts=PTS-STARTPTS[ad];"
      f"[aa][ab][ac][ad]concat=n=4:v=0:a=1,volume=1.2[clip]")
inputs = ["-i", a.src]
if track:
    inputs += ["-ss", f"{music_offset:.3f}", "-i", track]
    af += f";[1:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,volume={a.music_volume},afade=t=in:d=0.3,afade=t=out:st={max(0, total - 1.0):.3f}:d=1.0[m];[clip][m]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]"
else:
    af += ";[clip]anull[a]"
os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
tmpv, tmpa = a.out + ".video.mp4", a.out + ".audio.m4a"  # video and audio are rendered apart, then joined: one graph for both came out short
run(["-i", a.src, "-filter_complex", vf, "-map", "[v]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-profile:v", "high", "-level", "4.0", "-an", tmpv])
run([*inputs, "-filter_complex", af, "-map", "[a]", "-vn", "-c:a", "aac", "-b:a", "160k", tmpa])
run(["-i", tmpv, "-i", tmpa, "-map", "0:v", "-map", "1:a", "-c", "copy", "-movflags", "+faststart", a.out])
for f in (tmpv, tmpa):
    try: os.remove(f)
    except OSError: pass
report(tool="reel", out=a.out, seconds=round(total, 2), impact_in_source=round(impact, 2), impact_in_edit=round(impact_at, 2), slow=a.slow, zoom=a.zoom, punch=a.punch,
       hook=" / ".join(hook), end_text=" / ".join(endt), track=os.path.basename(track) if track else "", drop_at=round(drop, 2), music_offset=round(music_offset, 2), music_volume=a.music_volume)
