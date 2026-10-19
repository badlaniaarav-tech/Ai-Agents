---
description: Instagram competitors from Metricool: their followers, posts, reels, engagement and top posts next to ours, then a Research brief on why they win
---
Compare us with our Instagram competitors: $ARGUMENTS

1. If the Metricool connector tools are available (`mcp__Metricool_Social_Media_Management__getBrandSettings`, `mcp__Metricool_Social_Media_Management__getAnalyticsDataByMetrics`):
   - Call `getBrandSettings` for the brand id. If it says no social network is connected, tell the owner to connect Instagram at the link it gives and stop.
   - Call `getAnalyticsDataByMetrics` for the last 30 days (or the range asked) three times:
     - ours: `IGEV01` followers, `IGEV37` posts, `IGEV22` reels, `IGEV13` likes, `IGEV21` engagement, `IGEV43` followers gained, `IGEV44` lost, `IGEV23` reel views
     - competitors: `IGCO02` handle, `IGCO03` name, `IGCO07` followers, `IGCO08` posts, `IGCO12` reels, `IGCO09` avg likes, `IGCO06` comments, `IGCO10` engagement
     - their posts: `IGCP01` competitor, `IGCP04` text, `IGCP05` published, `IGCP07` likes, `IGCP08` comments, `IGCP09` interactions, `IGCP10` engagement, `IGCP11` url
   - If the competitor rows are empty, tell the owner to add competitors in Metricool (Analytics → Instagram → Competitors) and stop.
2. If the tools are not available: say so and point the owner to the Competitors tab in Agent HQ, which asks Metricool directly.
3. Write `work/research/instagram-competitors/<date>.md`: a table of us versus each competitor, their top eight posts with links, and then start **research-director** with that file to answer: what they do that we don't (format, hooks, cadence, posting times), and three changes for our next two weeks. Add the task to the board (`python3 office/tasks.py add`).
4. Report the table and the three changes. Nothing is posted.
