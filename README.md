# Take Off International — YouTube videos

Videos for the Take Off International YouTube channel (Mon / Wed / Fri, 4:00 PM Asia/Dhaka), published through Metricool (brand id 7806609).

- `videos/` — finished MP4s. Metricool fetches them from
  `https://raw.githubusercontent.com/takeoffsylhet-bd/takeoff-videos/main/videos/<file>`.
- `tools/` — the template used to make them:
  - `projects/*.json` — one file per video: `id`, `o` (`v` = 1080×1920 Short, `h` = 1920×1080 video), `key`, `seed`, `scenes[]`.
    Scene types: `hook` (badge, html, sub), `item` (num, label, title, desc or checks[], red), `cta` (html). Each has `dur` in seconds.
  - `node render.js projects/X.json preview` writes stills to `tools/<id>/prev_*.jpg`; `full` renders `tools/<id>/s*.mp4` + `list.txt`.
  - `python3 music.py projects/X.json out.wav` synthesizes background music and sound effects timed to the scenes.
  - Join: `ffmpeg -f concat -safe 0 -i <id>/list.txt -i out.wav -map 0:v -map 1:a -c:v copy -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 192k -shortest -movflags +faststart final.mp4`

## Content rules (from the owner)
- Say **"অসাধু এজেন্ট ও দালাল"**, never just "দালাল".
- Do not mention RL / recruiting-licence numbers. Talk about a valid **business licence**, an office, and proof of professional work.
- Brand: logo `tools/logo.png`, "Take Off Int'L (Pvt.)", slogan "Get Visa Safely", WhatsApp 01334913153.
- Topics: country-wise work visas, and visa tips & warnings. No invented prices or facts.

## Log
| Date | Type | Topic | File |
|---|---|---|---|
| 2026-11-02 Mon | Short | অসাধু এজেন্ট ও দালাল চেনার ৫টি লক্ষণ | videos/2026-11-02_short_asadhu-agent-dalal.mp4 |
| 2026-11-04 Wed | Video | গ্রীস ওয়ার্ক ভিসা ও রেসিডেন্সি: পুরো প্রসেস | videos/2026-11-04_video_greece-work-visa.mp4 |
| 2026-11-06 Fri | Short | ভিসার আগে ৫টি কাগজ যাচাই করুন | videos/2026-11-06_short_documents-check.mp4 |
