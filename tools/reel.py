"""Viral-style swing reel: tight framing, a hook line, slow-motion punch-in with a flash at impact,
a music drop on the strike, and the finish held with cover-style text.

usage: python3 tools/reel.py <in.mov> <out.mp4> [--impact 6.64] [--hook "LAST SWING|BEFORE DARK"] [--end "HOLD THE|FINISH"]
       [--mood hype | --track music/x.mp3] [--music-volume 0.5] [--focus 0.53,0.52] [--zoom 1.3] [--punch 1.6] [--slow 2.0]
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
ap.add_argument("--style", choices=["smooth", "punch"], default="smooth", help="smooth: the whole swing in slow motion, full body, small label (the normal golf edit). punch: hook text, slow only at the strike");
ap.add_argument("--label", default="last swing before dark", help="smooth style: small white label at the top; empty for none");
ap.add_argument("--stats", default="", help="launch-monitor card that pops up on the strike: \"Ball speed|156 mph;Carry|265 yds;Launch|12.7°;Spin|2989 rpm;Club speed|108 mph;Smash|1.45\" (up to 6)"); ap.add_argument("--stats-title", default="", help="small title on the card, like 'driver'"); ap.add_argument("--stats-y", type=float, default=0.58, help="card position as a fraction of the height"); ap.add_argument("--stagger", type=float, default=0.12, help="seconds between the card's numbers popping in; 0 shows them at once"); ap.add_argument("--stats-scale", type=float, default=1.0, help="card size, 0.55 is small like the Trackman reels"); ap.add_argument("--stats-x", type=float, default=0.5, help="card centre as a fraction of the width"); ap.add_argument("--stats-layout", choices=["grid", "row"], default="grid", help="grid: two columns; row: one strip of numbers");
ap.add_argument("--strike-punch", type=float, default=1.0, help="smooth style: tighter crop from the strike on, like 1.12 (1 = off)"); ap.add_argument("--push", default="", help="smooth style: slow smooth push-in over the whole clip, \"1.2:1.35\" = from 1.2x to 1.35x (no cut)"); ap.add_argument("--from", dest="start", type=float, help="use the clip from this second instead of the takeaway"); ap.add_argument("--to", dest="stop", type=float, help="…to this second instead of the finish hold"); ap.add_argument("--grade", choices=["none", "pop", "moody"], default="none"); ap.add_argument("--impact", type=float); ap.add_argument("--hook", default="LAST SWING BEFORE DARK", help="one short line on the first second; | for a second line if you must"); ap.add_argument("--end", default="", help="text on the finish; off by default (one line per reel)")
ap.add_argument("--mood", default="hype"); ap.add_argument("--track"); ap.add_argument("--music-volume", type=float, default=0.55)
ap.add_argument("--focus", default="0.53,0.52", help="where the golfer is, as fractions of width,height"); ap.add_argument("--zoom", type=float, default=1.35); ap.add_argument("--punch", type=float, default=1.45)
ap.add_argument("--slow", type=float, default=2.0, help="slow-motion factor at impact (2x on a 60 fps phone clip stays smooth; no frame interpolation, it warps the body)"); ap.add_argument("--lead", type=float, default=0.4, help="seconds of address before the takeaway (keep it short: no standing around)")
ap.add_argument("--pre", type=float, default=1.3, help="seconds before impact at normal speed (the backswing)"); ap.add_argument("--post", type=float, default=0.3, help="seconds after impact in slow motion")
ap.add_argument("--hold", type=float, default=1.6, help="seconds of finish after impact (real time)"); ap.add_argument("--color", default="#FFD400")
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
A0, A1 = max(0.0, impact - a.pre - a.lead), max(0.0, impact - a.pre)
B0, B1 = A1, impact - 0.12
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
if a.style == "smooth":
    S0, S1 = max(0.0, impact - a.pre - a.lead), min(dur, impact + a.hold)  # takeaway to finish, one piece
    if a.start is not None: S0 = max(0.0, min(a.start, impact))
    if a.stop is not None: S1 = min(dur, max(a.stop, impact + 0.3))
    total = (S1 - S0) * a.slow; impact_at = (impact - S0) * a.slow
    music_offset = max(0.0, drop - impact_at)
    cw, ch = int(W / a.zoom) // 2 * 2, int(H / a.zoom) // 2 * 2
    cx = min(max(0, int(W * fx - cw / 2)), W - cw); cy = min(max(0, int(H * fy - ch / 2)), H - ch)
    label = ""
    if a.label.strip():
        esc = a.label.strip().replace("'", r"\'").replace(":", r"\:")
        label = f",drawtext=fontfile={FONT}:text='{esc}':fontsize=46:fontcolor=#16181f:box=1:boxcolor=white@0.96:boxborderw=22:x=(w-text_w)/2:y=330"
    cards = []
    if a.stats.strip():
        from PIL import Image, ImageDraw, ImageFont
        items = [[p.strip() for p in x.split("|", 1)] for x in a.stats.split(";") if x.strip()][:6]; cols = (len(items) if a.stats_layout == "row" else 2) if len(items) > 1 else 1; rows = (len(items) + cols - 1) // cols
        tw, th, gap, pad = 440, 170, 18, 24; W_ = cols * tw + (cols - 1) * gap + pad * 2; title_h = 70 if a.stats_title.strip() else 0; H_ = rows * th + (rows - 1) * gap + pad * 2 + title_h
        def font(size, weight=700):
            f = ImageFont.truetype(FONT, size)
            try: f.set_variation_by_axes([weight])
            except Exception: pass
            return f
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        steps = len(items) if a.stagger > 0 else 1
        for k in range(steps):  # cumulative cards: one more number each step
            im = Image.new("RGBA", (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
            if title_h: d.rounded_rectangle((pad, pad, pad + 260, pad + 50), 14, fill=(255, 255, 255, 245)); d.text((pad + 130, pad + 25), a.stats_title.strip(), font=font(30, 600), fill=(22, 24, 31), anchor="mm")
            for i, it in enumerate(items[: (k + 1) if steps > 1 else len(items)]):
                lab, val = (it + [""])[:2]; x = pad + (i % cols) * (tw + gap); y = pad + title_h + (i // cols) * (th + gap)
                d.rounded_rectangle((x, y, x + tw, y + th), 22, fill=(255, 255, 255, 245)); d.text((x + tw / 2, y + 62), val, font=font(74, 800), fill=(22, 24, 31), anchor="mm"); d.text((x + tw / 2, y + 132), lab.lower(), font=font(28, 500), fill=(90, 96, 110), anchor="mm")
            if a.stats_scale != 1.0: im = im.resize((max(2, int(im.width * a.stats_scale)), max(2, int(im.height * a.stats_scale))), Image.LANCZOS)
            path = f"{a.out}.card{k}.png"; im.save(path); cards.append(path)
        card_at = impact_at + 0.1
    grade = {"pop": ",eq=contrast=1.06:saturation=1.18:brightness=0.01", "moody": ",eq=contrast=1.08:saturation=0.8:brightness=-0.02,curves=preset=darker", "none": ""}[a.grade]
    base_crop = f"crop={cw}:{ch}:{cx}:{cy},scale=1080:1920:flags=lanczos"
    if a.push:  # one smooth push-in across the clip: no cut, no jiggle (linear zoom, per frame)
        z0, z1 = [float(x) for x in a.push.split(":")]; nframes = int((S1 - S0) * a.slow * 30) + 1
        vf = (f"[0:v]trim={S0:.3f}:{S1:.3f},setpts=(PTS-STARTPTS)*{a.slow},scale=1080:1920:flags=lanczos,fps=30,"
              f"zoompan=z='{z0}+({z1}-{z0})*on/{nframes}':x='iw*{fx}-iw/zoom/2':y='ih*{fy}-ih/zoom/2':d=1:s=1080x1920:fps=30{grade}{label},format=yuv420p[base]")
    elif a.strike_punch > 1.0:  # a cut to a tighter frame from the strike on
        z2 = a.zoom * a.strike_punch; cw2, ch2 = int(W / z2) // 2 * 2, int(H / z2) // 2 * 2; cx2 = min(max(0, int(W * fx - cw2 / 2)), W - cw2); cy2 = min(max(0, int(H * fy - ch2 / 2)), H - ch2)
        vf = (f"[0:v]trim={S0:.3f}:{impact - 0.02:.3f},setpts=(PTS-STARTPTS)*{a.slow},{base_crop}[p1];[0:v]trim={impact - 0.02:.3f}:{S1:.3f},setpts=(PTS-STARTPTS)*{a.slow},crop={cw2}:{ch2}:{cx2}:{cy2},scale=1080:1920:flags=lanczos[p2];"
              f"[p1][p2]concat=n=2:v=1:a=0{grade}{label},fps=30,format=yuv420p[base]")
    else:
        vf = f"[0:v]trim={S0:.3f}:{S1:.3f},setpts=(PTS-STARTPTS)*{a.slow},{base_crop}{grade}{label},fps=30,format=yuv420p[base]"
    prev = "base"
    for k, cpath in enumerate(cards):
        t0 = card_at + k * a.stagger; t1 = card_at + (k + 1) * a.stagger if k < len(cards) - 1 else total + 2
        vf += f";[{k + 1}:v]format=rgba{',fade=t=in:st=' + format(t0, '.3f') + ':d=0.15:alpha=1' if k == 0 else ''},setpts=PTS-STARTPTS[c{k}];[{prev}][c{k}]overlay=x=W*{a.stats_x}-w/2:y=H*{a.stats_y}-h/2:enable='between(t,{t0:.3f},{t1:.3f})':format=auto[o{k}]"; prev = f"o{k}"
    vf += f";[{prev}]format=yuv420p[v]"
    # sound: the real audio (slowed if the picture is) kept low, the crack at full speed on the contact frame, music from the downswing
    c0, c1 = max(0.0, impact - 0.04), min(dur, impact + 0.3)
    tempo = "" if a.slow == 1 else f",atempo={max(0.5, 1 / a.slow):.3f}" + (f",atempo={1 / a.slow / 0.5:.3f}" if a.slow > 2 else "")
    af = (f"[0:a:0]atrim={S0:.3f}:{S1:.3f},asetpts=PTS-STARTPTS{tempo},volume=0.35[amb];"
          f"[0:a:0]atrim={c0:.3f}:{c1:.3f},asetpts=PTS-STARTPTS,volume=1.5,adelay={int((impact_at - 0.04 * a.slow) * 1000)}|{int((impact_at - 0.04 * a.slow) * 1000)}[crack];"
          f"[amb][crack]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,alimiter=limit=0.95[clip]")
    inputs = ["-i", a.src]
    if track and a.music_volume > 0:
        start_at = max(0.0, impact_at - 0.9)
        inputs += ["-ss", f"{music_offset:.3f}", "-i", track]
        af += (f";[1:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,volume={a.music_volume},volume=enable='lt(t,{start_at:.3f})':volume=0,afade=t=in:st={start_at:.3f}:d=0.35,afade=t=out:st={max(0, total - 1.2):.3f}:d=1.2[m];"
               f"[clip][m]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]")
    else:
        af += ";[clip]anull[a]"
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True); tmpv, tmpa = a.out + ".video.mp4", a.out + ".audio.m4a"
    vin = ["-i", a.src]
    for cpath in cards: vin += ["-loop", "1", "-t", f"{total:.3f}", "-i", cpath]
    run([*vin, "-filter_complex", vf, "-map", "[v]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-profile:v", "high", "-level", "4.0", "-an", tmpv])
    run([*inputs, "-filter_complex", af, "-map", "[a]", "-vn", "-c:a", "aac", "-b:a", "160k", tmpa])
    run(["-i", tmpv, "-i", tmpa, "-map", "0:v", "-map", "1:a", "-c", "copy", "-movflags", "+faststart", a.out])
    for f in [tmpv, tmpa] + cards:
        try: os.remove(f)
        except OSError: pass
    report(tool="reel", style="smooth", stats=a.stats.strip(), out=a.out, seconds=round(total, 2), impact_in_source=round(impact, 2), impact_in_edit=round(impact_at, 2), slow=a.slow, zoom=a.zoom, label=a.label.strip(),
           track=os.path.basename(track) if track else "", drop_at=round(drop, 2), music_offset=round(music_offset, 2), music_volume=a.music_volume); sys.exit(0)
def crop(z):
    cw, ch = int(W / z) // 2 * 2, int(H / z) // 2 * 2
    x = min(max(0, int(W * fx - cw / 2)), W - cw); y = min(max(0, int(H * fy - ch / 2)), H - ch)
    return f"crop={cw}:{ch}:{x}:{y},scale=1080:1920:flags=lanczos"
def fit(line, size):  # shrink the size until the line fits 86% of the width (drawtext has no auto-fit)
    try:
        from PIL import ImageFont
        while size > 48 and ImageFont.truetype(FONT, size).getlength(line) + 14 > 1080 * 0.86: size -= 4
    except Exception: pass
    return size
def text(lines, y0, size=150, start=0.0, end=None):
    """Stacked lines, brand style: white, the last line (or the last word of a single line) yellow, soft shadow."""
    out = []; y = y0; size = min([fit(l, size) for l in lines] or [size]); bw = max(2, size // 16)
    en = f":enable='between(t,{start},{end})'" if end else f":enable='gte(t,{start})'"
    def dt(txt, col, x, yy):
        esc = txt.replace("'", r"\'").replace(":", r"\:")
        return [f"drawtext=fontfile={FONT}:text='{esc}':fontsize={size}:fontcolor=black@0.7:borderw={bw}:bordercolor=black@0.7:x={x}+{bw}:y={yy + bw}{en}",
                f"drawtext=fontfile={FONT}:text='{esc}':fontsize={size}:fontcolor={col}:borderw={bw}:bordercolor={col}:x={x}:y={yy}{en}"]
    def width(txt):
        try:
            from PIL import ImageFont; return ImageFont.truetype(FONT, size).getlength(txt)
        except Exception: return len(txt) * size * 0.6
    for i, line in enumerate(lines):
        last = i == len(lines) - 1; words = line.split()
        if last and len(lines) == 1 and len(words) > 1:  # one line: last word yellow
            head, tail = " ".join(words[:-1]) + " ", words[-1]; wh, wt = width(head), width(tail); x0 = (1080 - wh - wt) / 2
            out += dt(head, "white", f"{x0:.0f}", y) + dt(tail, a.color, f"{x0 + wh:.0f}", y)
        else:
            out += dt(line, a.color if last else "white", "(w-text_w)/2", y)
        y += int(size * 1.05)
    return "," + ",".join(out) if out else ""
hook = [s.strip().upper() for s in a.hook.split("|") if s.strip()]; endt = [s.strip().upper() for s in a.end.split("|") if s.strip()]
vf = (f"[0:v]trim={A0}:{A1},setpts=PTS-STARTPTS,{crop(a.zoom)}{text(hook, 300, size=120, start=0.0)}[va];"
      f"[0:v]trim={B0}:{B1},setpts=PTS-STARTPTS,{crop(a.zoom)}{text(hook, 300, size=120, start=0.0, end=max(0.0, 1.1 - tA))}[vb];"
      f"[0:v]trim={C0}:{C1},setpts=(PTS-STARTPTS)*{a.slow},{crop(a.punch)}[vc];"
      f"[0:v]trim={D0}:{D1},setpts=PTS-STARTPTS,{crop(a.zoom)}{text(endt, 300, size=120, start=0.5)}[vd];"
      f"[va][vb][vc][vd]concat=n=4:v=1:a=0,fps=30,format=yuv420p[v]")
# clip sound: normal for A, B, D; the strike stretched for C
af = (f"[0:a:0]atrim={A0}:{A1},asetpts=PTS-STARTPTS[aa];[0:a:0]atrim={B0}:{B1},asetpts=PTS-STARTPTS[ab];"
      f"[0:a:0]atrim={C0}:{C1},asetpts=PTS-STARTPTS,volume=1.6,apad=whole_dur={tC:.3f}[ac];[0:a:0]atrim={D0}:{D1},asetpts=PTS-STARTPTS[ad];"
      f"[aa][ab][ac][ad]concat=n=4:v=0:a=1,volume=1.2,alimiter=limit=0.95[clip]")
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
