# Prompt for a frame-by-frame breakdown of another creator's edit

Use this prompt to break down the reels of the creator you analyze: fill in the values in curly braces. Before that, run
`fetch_reels.py` and `analyze_reference.py <dir> all`: the breakdown needs `sheet.jpg`, `words.json`, `vision.json`, `metrics.json`
and `scenes.json` of every reel.

How to run it:
- **2–5 reels** (the usual case): do it yourself, one reel after another, or give all of them to one agent.
- **6+ reels**: split them between parallel agents, about 6 reels each, run in the background. One agent needs 45–60 min for 6 reels.

The beat sheets describe the edit, not the script: the spoken words are reduced to a role and a few trigger words, so the profile
stays shareable and does not reproduce the creator's text.

```text
You are reverse-engineering the video EDITING style of the creator {NAME} ({HANDLE}): {ONE LINE ABOUT THE FORMAT}. Your job:
produce an exact beat sheet (edit decision list) for each reel below so another agent can reproduce the editor's decisions.
Be concrete, visual, measured. No generic praise.

Reels to analyze (folder ids under {DIR}/work/): {ID1}, {ID2}, …
Source videos: {DIR}/raw/<id>.mp4.

Per reel folder you have:
- sheet.jpg — contact sheet, one tile every 0.5 s (10 tiles per row, left→right, top→bottom; tile k = time k*0.5 s). Read it with the Read tool.
- words.json — whisper word timestamps (key "words": [{word,start,end}], "text").
- vision.json — per-frame automatic tags every 0.5 s (layout, face size, graphic kind, caption text/font, accent). The caption/title fields are noisy; trust your eyes over them.
- metrics.json — measured numbers (pace, cuts, layouts, colours, framing, sound).
- scenes.json — ffmpeg scene-change scores per frame (t, score): score > 0.3 is a hard cut.
You may extract full-resolution frames to inspect details: `ffmpeg -v error -y -ss <t> -i <raw.mp4> -frames:v 1 {SCRATCH}/<name>.png`
and Read them (do this for every beat you are unsure about; at least 6 frames per reel). You may sample pixel colours with
python3 + PIL to get exact hex values.

Known vocabulary (use these names; add new ones if you see others):
- Layouts: S = split (graphic on top, speaker at the bottom — describe the exact frame shape), F = face full-frame (punch-in; note
  medium vs close-up), G = full-frame graphic, no speaker, B = full-frame b-roll / screen recording / sharp card over a blurred copy.
- Caption styles: bold sans, italic serif lowercase connector words, heavy italic serif CAPS, pixel/mono titles, keyword in accent colour, caption box.
- Graphic kinds: logo pop, logo row accumulating, hub-and-spoke diagram, counter/odometer, mini product UI widget, screenshot card
  with highlight box, website/GitHub page, terminal, chart, list title card, person photo card, sticky note, doodle arrows, 3D emoji,
  mascot, progress/usage meter, model-switcher carousel, blurred-background b-roll.

Do not transcribe the speech. Where the spoken words matter, give the role of the beat (HOOK, NAME, PROOF, MECH, LIST, NUM, PAIN,
PAYOFF, BRIDGE, CTA), a short paraphrase in your own words and at most 3 exact trigger words (brand names, numbers, the verb that
flips a UI state). Never quote more than 3 consecutive spoken words, except the CTA keyword.

For EACH reel write {DIR}/analysis/<id>.md with exactly these sections:
1. `# <id> — <topic in your own words, max 10 words>` then one line: duration, words/sec, CTA keyword, accent colour hex, backgrounds used (hex).
2. `## Beat sheet` — a table with one row per visual beat (every change of layout OR of the main graphic OR of caption style;
   typically 20–45 rows): `| # | t0–t1 (s) | beat role · trigger words | layout S/F/G/B (+ face medium/close-up) | background |
   what is on screen (exact: which logo/text/UI, where, size) | caption (style, colour, y position as fraction of height, chunks ×
   words per chunk) | motion/entrance/exit (pop, slide, type-on, count-up, highlight sweep, zoom) | trigger: which spoken word causes
   this visual and how many ms before/after the word |`
3. `## Hook 0–3 s` — what happens every 0.5 s, and why it grabs.
4. `## CTA` — the last ~4 s exactly (layout, face scale, caption styles, keyword colour, how long it holds, how the video ends).
5. `## Shot types used` — list `name: count` for this reel.
6. `## Rules this reel follows` — 5–10 concrete rules inferred, with numbers.

After all files, reply with: the file paths and the 10 most important cross-reel rules you observed (one line each, concrete, with numbers).
```

After the breakdowns:
- write the profile's `style-bible.md` from `style-bible.draft.md` (numbers are already filled in), following the section order of
  `styles/_template/style-bible.md`, and turn the cross-reel rules into its numbered "rules for the planner";
- check `style.json`: layout ranges, opening/closing layout, `framing` (measured with Apple Vision or OpenCV when available), sound;
  edit numbers that look wrong, and set `plan_defaults` (accent, era, music) to what fits the creator;
- if the creator's captions, split shape or sound differ from anything the engine offers, write down the closest engine settings in
  the style bible (e.g. `era: "2025"` for a straight 50/50 split with boxed captions, `trans: "cut"` for hard cuts, `profile: "measured"`
  for quiet sound) and build the missing moves as `html` beats.
