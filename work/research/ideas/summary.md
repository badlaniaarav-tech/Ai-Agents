# Golf shorts and reels: what gets views (idea-scout, second run, 2026-10-20)

What this is based on: 16 queries on YouTube, each as a Shorts search and a normal search, 30 results each: 957 rows, 540 unique videos, 537 with a view count (`results.jsonl`, 32 thumbnail sheets in this folder). Views are all-time, not last 90 days; the Shorts shelf shows no dates or channels. No Instagram or TikTok search was possible; the owner's five example strips in `../reel-style/examples/` are the Instagram evidence. Baseline for the 442 Shorts: median 63.5K views, mean 1.8M, 19% over 1M (use the median).

## The ten patterns
1. Slow motion in the title: 73 Shorts, median 339K (5x the baseline), 26% over 1M. Rory McIlroy iron slow motion 5.9M, Nataliya Guseva driver 8.6M.
2. A famous name: 141 Shorts, median 379K. No name and no slow motion: median 33.5K. Slow motion without a name still doubles the baseline (71K). Copy the slow motion, not the name.
3. Driver and woods over irons: driver, wood or stinger titles median 473K, 35% over 1M; iron titles 244K.
4. Slow motion plus analysis with lines drawn: only 8 Shorts but median 1.15M, 4 of 8 over 1M (Bryson DTL analysis 3.6M, "The OPPOSITE of over the top" 2.6M with a teal hand-path line, Jake Knapp analysis 2M with red lines). 5 of the 60 best-viewed Shorts had drawn lines.
5. Face-on beats down-the-line in titles: 338K vs 90K median (small groups: 21 and 19). Test both on the owner's account.
6. Plain frame, little or no text: of the 60 best-viewed swing Shorts, about 27 had no text, 19 a small caption, 6 big caps. The biggest (Rory 5.9M, Linn Grant 4.2M, Tiger 2.6M) carry no text. Matches the brand rule: one small label, no big caps.
7. A drill with a promise: drill Shorts median 75K, but with "only", "simple", "perfect", "instantly" or "best" in the title median 502K, 44% over 1M. The winners are instructors talking; the label has to carry the promise.
8. Satisfying, pure, stinger, divot: median 145K, 34% over 1M ("Top 12 Most Satisfying Shots" 13M, Scheffler divot pattern 5.8M, "Most satisfying golf video ever" 3M: one swing per club with the club list down the side). Ranked and top-N titles: median 116K.
9. Short titles, no hashtags: titles of 40 characters or fewer median 85K vs 57K; no hashtag 85K vs 49.5K; question titles 28K; emoji and numbers do not help.
10. Sound, POV and trick shots are a lottery: medians 36.5K, 52K and 28K with single outliers at 120M, 121M and 19M. Range routines 37K, tempo 80.5K, before and after 48K with nothing over 1.3M. One test each, not a plan.

## The owner's examples, matched to formats
- rhythm and tempo label: `tempo-number-label`, `smooth-slow`
- wgachampionships whole swing in slow motion: `smooth-slow`
- Trackman numbers: `stats-card` (on YouTube the same idea is one number in the caption: "190 mph" 2M, "2-iron from 274 yards" 3.1M)
- fairwayfilm montage: `montage-on-the-strike`
- noahhenry "aesthetic reps": `angles-stacked`

## Make first (also `make_first_rank` in ideas/formats.json)
1. `smooth-slow`, driver first, face-on; make one face-on and one down-the-line to settle pattern 5.
2. `lines-on-swing`: the highest median measured; the page editor draws the lines, one small label.
3. `signature-move-slow`: name one move ("the transition", 4.2M); same build with a different label.
4. `angles-stacked` when the owner films two or three angles.
5. `ranked-countdown`: his best five shots; montage.py with per-clip labels.
6. `club-by-club-session`: montage.py; the on-screen club list is still missing.
7. `impact-closeup`: one test clip, phone low and close at 240 fps.
8. `tempo-number-label`: a label variant of format 1 with a measured number only.
9. `stats-card`: needs the owner's launch-monitor numbers and a new tool.
10. `drill-in-one-line`: only with a drill the owner can state in a few words.
11. `two-angles-split`, `before-after-swing`: last; low medians and they need the compare tool.

## Still needs a tool (for the Dev team)
split-screen compare synced on the strike (`tools/compare.py`); stats card (`tools/stats.py`); tempo counter (`tools/tempo.py`); arrow or circle overlays in the page editor; ball-flight tracer; club list kept on screen; a countdown counter (5 to 1) for montage; a second smaller name line under the label; timed text overlay (`tools/text.py`); check reel.py on a 240 fps clip at 3x or 4x.
