---
description: Play a hole with me: every shot on one hole in order, a two-line label on each (yards and club), the hole card on the tee shot, real speed, music low
---
Build a "play a hole with me" reel from the shot clips in `inbox/` (or the ones named), in the order they were played. $ARGUMENTS gives the labels, one per shot, separated by |, for example: `512 yards, par 5 | 170 yards, 9 iron | 22 yards, 60 wedge | par` (the last one is the result if it is a score word).

The owner's approved look (hole 15 reel), the default for every hole:
- Intro card `--intro "come play|a par <n> with me"` high above the golfer over the tee-shot address. No `--card`.
- Every shot: a small two-line side label far right (yards and club). The score goes in the putt label (`"<putt clip>|15 ft|birdie putt"`), never `--result`.
- Tee shot starts 2.2 s before the strike (default). The putt starts when the golfer is settled over the ball: look at the frames and set its own seconds-before (fifth field, e.g. `|9|2.95`) so any look-up or stand-up before it is cut; it ends right after the stroke, no `--hold`.
- Real sound, music at 30%. Always two files: `hole-chill.mp4` (chill CC track) and `hole-raye-touch-of-funk.mp4` (`--music-volume 0`, the owner adds the Instagram sound "RAYE with a Touch Of Funk" when posting).

1. Put it on the board