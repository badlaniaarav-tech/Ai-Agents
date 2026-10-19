"""Add music under an edit: picks a track from music/ (or --track), loops or trims it to the video, keeps it low,
ducks it automatically whenever someone speaks, fades in and out, and writes the final file.

usage: python3 tools/music.py <edit.mp4> <final.mp4> [--track music/song.mp3] [--mood hype] [--volume 0.18] [--fade 1.0] [--no-duck]
--mood picks a track whose file name starts with that tag (music/hype-*.mp3), see music/brief.md; any track if none match.
Prints one JSON line with the result. Put royalty-free tracks you have the rights to use (mp3, wav, m4a) in music/.
"""
import argparse, json, os, random, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from media import FFMPEG, probe, report, run

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--track", help="music file; default: a random file from music/")
ap.add_argument("--mood", help="prefer tracks named <mood>-*.mp3 in music/ (hype, chill, cinematic, funny…)")
ap.add_argument("--volume", type=float, default=0.18, help="music level under the voice (0 to 1)")
ap.add_argument("--fade", type=float, default=1.0, help="fade in and out, seconds")
ap.add_argument("--no-duck", action="store_true", help="keep the music level steady instead of dipping under speech")
a = ap.parse_args()

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
track = a.track
if not track:
    folder = os.path.join(root, "music")
    files = [f for f in (os.listdir(folder) if os.path.isdir(folder) else []) if f.lower().endswith((".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"))]
    if not files:
        print(json.dumps({"tool": "music", "error": "no tracks in music/. Add royalty-free mp3 or wav files there, or pass --track."})); sys.exit(1)
    if a.mood:
        tagged = [f for f in files if f.lower().startswith(a.mood.lower() + "-")]
        files = tagged or files
    track = os.path.join(folder, random.choice(files))

dur = float(probe(a.src)["duration"])
has_voice = "Audio:" in subprocess.run([FFMPEG, "-hide_banner", "-i", a.src], capture_output=True, text=True).stderr
fade = max(0.0, min(a.fade, dur / 2))
music = f"[1:a]aloop=loop=-1:size=2000000000,atrim=0:{dur:.3f},asetpts=N/SR/TB,volume={a.volume},afade=t=in:d={fade},afade=t=out:st={max(0, dur - fade):.3f}:d={fade}[m]"
if has_voice and not a.no_duck:
    chain = f"{music};[0:a:0]asplit=2[v1][v2];[m][v2]sidechaincompress=threshold=0.04:ratio=6:attack=30:release=500:makeup=1[md];[v1][md]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]"
elif has_voice:
    chain = f"{music};[0:a:0][m]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]"
else:
    chain = f"{music};[m]anull[a]"
os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
run(["-i", a.src, "-stream_loop", "-1", "-i", track, "-filter_complex", chain, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", a.out])
report(tool="music", out=a.out, track=os.path.basename(track), mood=a.mood or "", seconds=round(dur, 2), music_volume=a.volume, ducked=bool(has_voice and not a.no_duck), fade=fade)
