"""Ball tracker: a circle that follows the ball after the strike, on any rendered clip.

usage: python3 tools/track.py <in.mp4> <out.mp4> [--impact 3.1] [--ball 0.52,0.74] [--radius 26] [--color #FFD400] [--trail] [--max 4.0] [--search 140]
--ball is where the ball sits before the strike (fractions of width,height); without it the tool looks for a small bright
round blob in the lower middle of the frame. From the strike on it follows the ball frame by frame: a bright, moving, small
blob near where the last position and speed predict it. It stops when the ball is lost (out of frame, in the trees, too small).
Works only when the phone keeps the ball in frame: a driver filmed face-on leaves the frame in two frames and gets no circle.
Prints one JSON line with the tracked seconds and the path.
"""
import argparse, json, os, subprocess, sys
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from media import FFMPEG, probe, report

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("out"); ap.add_argument("--impact", type=float); ap.add_argument("--ball", default="")
ap.add_argument("--radius", type=int, default=26); ap.add_argument("--color", default="#FFD400"); ap.add_argument("--trail", action="store_true", help="draw the path behind the ball too")
ap.add_argument("--max", type=float, default=4.0, help="seconds to track after the strike"); ap.add_argument("--search", type=int, default=140, help="search window in pixels around the predicted spot")
ap.add_argument("--min-area", type=int, default=3); ap.add_argument("--max-area", type=int, default=900)
a = ap.parse_args()
info = probe(a.src); W, H, fps, dur = int(info["width"]), int(info["height"]), float(info["fps"]), float(info["duration"])
col = tuple(int(a.color.lstrip("#")[i:i + 2], 16) for i in (4, 2, 0))  # BGR

def impact_time():
    if a.impact is not None: return a.impact
    raw = subprocess.run([FFMPEG, "-v", "error", "-i", a.src, "-map", "0:a:0", "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
    s = np.frombuffer(raw, np.float32); w = 320
    if len(s) < w: return dur * 0.5
    env = np.array([np.abs(s[i:i + w]).max() for i in range(0, len(s) - w, w)]); return float(np.argmax(env) * w / 16000)
T = impact_time(); f_imp = int(T * fps)

dec = subprocess.Popen([FFMPEG, "-hide_banner", "-loglevel", "error", "-i", a.src, "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
tmp = a.out + ".video.mp4"
enc = subprocess.Popen([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)

def bright_small(gray, hsv, mask_region=None):
    """Small bright, low-saturation blobs: candidates for a golf ball."""
    m = ((gray > 185) & (hsv[..., 1] < 70)).astype(np.uint8)
    if mask_region is not None: m &= mask_region
    n, lab, stats, cent = cv2.connectedComponentsWithStats(m, 8)
    out = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if a.min_area <= area <= a.max_area and 0.4 <= w / max(1, h) <= 2.5: out.append((cent[i][0], cent[i][1], area))
    return out

pos = None; vel = np.zeros(2); path = []; prev_gray = None; frame_i = 0; tracked = 0; lost = 0; start_pos = None
if a.ball: start_pos = np.array([float(v) * d for v, d in zip(a.ball.split(","), (W, H))])
nbytes = W * H * 3
while True:
    buf = dec.stdout.read(nbytes)
    if len(buf) < nbytes: break
    frame = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy(); t = frame_i / fps
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY); hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    if frame_i == max(0, f_imp - 3) and start_pos is None:  # find the ball at rest: lower middle, small and round
        region = np.zeros((H, W), np.uint8); region[int(H * 0.5):int(H * 0.88), int(W * 0.3):int(W * 0.7)] = 1
        cands = bright_small(gray, hsv, region)
        if cands: c = min(cands, key=lambda c: abs(c[2] - 60)); start_pos = np.array([c[0], c[1]])
    if frame_i >= f_imp and t <= T + a.max and lost < 4 and (start_pos is not None):
        if pos is None: pos = start_pos.copy(); vel = np.zeros(2)
        pred = pos + vel
        if prev_gray is not None:
            motion = (cv2.absdiff(gray, prev_gray) > 18).astype(np.uint8)
            x0, y0 = int(max(0, pred[0] - a.search)), int(max(0, pred[1] - a.search)); x1, y1 = int(min(W, pred[0] + a.search)), int(min(H, pred[1] + a.search))
            region = np.zeros((H, W), np.uint8); region[y0:y1, x0:x1] = 1
            cands = [c for c in bright_small(gray, hsv, region & motion) if np.hypot(c[0] - pred[0], c[1] - pred[1]) <= a.search]
            if not cands and frame_i == f_imp: cands = bright_small(gray, hsv, region)
            if cands:
                c = min(cands, key=lambda c: np.hypot(c[0] - pred[0], c[1] - pred[1])); new = np.array([c[0], c[1]])
                if frame_i > f_imp: vel = 0.6 * vel + 0.4 * (new - pos)
                pos = new; lost = 0; tracked += 1; path.append((int(pos[0]), int(pos[1])))
            else:
                lost += 1; pos = pred
        if lost < 2 and path:
            if a.trail and len(path) > 1: cv2.polylines(frame, [np.array(path, np.int32)], False, col, 4, cv2.LINE_AA)
            cv2.circle(frame, (int(pos[0]), int(pos[1])), a.radius, col, 4, cv2.LINE_AA)
    enc.stdin.write(frame.tobytes()); prev_gray = gray; frame_i += 1
enc.stdin.close(); enc.wait(); dec.wait()
subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-i", tmp, "-i", a.src, "-map", "0:v", "-map", "1:a?", "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", a.out], check=True); os.remove(tmp)
report(tool="track", out=a.out, impact=round(T, 2), start=[round(float(v), 1) for v in start_pos] if start_pos is not None else None, tracked_frames=tracked, tracked_seconds=round(tracked / fps, 2), path_points=len(path), note="" if tracked > 3 else "ball not found after the strike: it left the frame or was too small; film down the line and pan with the ball")
