# Style profiles: measure a creator, then edit in their style

A **style profile** is a folder that tells the engine and the planner how a particular creator's reels are edited. The skill ships
no built-in style: every user first makes a profile from 2–5 reels of a creator they choose, then edits a new talking-head take in
that style. `scripts/reference/make_skill.py` can pack the profile as its own skill, `montage-<handle>`. The engine keeps neutral
fallback numbers in `styles/_defaults/style.json`, used only for fields a profile lacks; `styles/_template/style-bible.md` is the
section skeleton of a style bible.

## What is in a profile

| file | who writes it | who reads it |
|---|---|---|
| `style.json` | `analyze_reference.py report` (edit it if a number looks wrong) | `autoplan.py` (opening layout, face share, defaults), `plan_lint.py` and `qa.py` (targets), `build.py` (face framing), `finish.py` (levels of the `measured` sound profile) |
| `STYLE_METRICS.md` | `analyze_reference.py report` | you, when writing the style bible |
| `style-bible.md` | you, from `style-bible.draft.md` | the planner, before every plan in this style |
| `analysis/<id>.md` | you, with `references/beat-sheet-prompt.md` | you and the planner, as worked examples |
| `raw/`, `work/`, `sources.json` | `fetch_reels.py`, `analyze_reference.py` | nobody else: private working files |

`raw/` holds the downloaded reels and `work/` their frames and transcripts. They are for private analysis: keep them out of any
repository you publish (a profile you share needs only the four files above).

## Make a profile ("analyze this creator's montage")

```bash
S=~/.claude/skills/reels-montage/scripts          # where the skill is installed
D=~/reels/styles/<handle>                          # a folder next to your projects, not inside the skill
python3 $S/reference/fetch_reels.py $D <link or file> <link or file> ...
python3 $S/reference/analyze_reference.py $D all --lang en
```

1. **Collect 2–5 reels.** Links to Instagram reels, TikToks, YouTube Shorts, or local video files. With `APIFY_TOKEN` set,
   Instagram links go through Apify (≈ $0.01 per reel); otherwise, and for all other sites, `yt-dlp` downloads them. Instagram
   often blocks anonymous downloads: then pass cookies to yt-dlp (`--yt-dlp-args "--cookies-from-browser chrome"`), set
   `APIFY_TOKEN`, or ask the user to download the reels and give you the files. Pick reels of the same format and period: one
   creator can change their edit a lot within a year.
2. **Measure.** `analyze_reference.py all` extracts 2 frames per second, contact sheets, cuts, words (whisper-1), per-frame tags
   (layout, face size, graphic kind, caption font/colour/position) with an OpenAI vision model, dominant colours, face framing
   (Apple Vision on macOS, OpenCV elsewhere), loudness and a description of the music and effects by an OpenAI audio model.
   Cost: a few cents per reel; time: 1–3 min per reel. Optional: with Demucs installed (`DEMUCS_PY`), the `stems` step also
   measures the music level under the voice and the effect density.
3. **Look.** Read `STYLE_METRICS.md`, every `work/<id>/sheet.jpg` (tile k = k·0.5 s) and full-size frames of anything unclear.
4. **Break it down.** Write `analysis/<id>.md` per reel with `references/beat-sheet-prompt.md` (roles and trigger words, never the
   script).
5. **Write the style bible.** Turn `style-bible.draft.md` into `style-bible.md`: keep the section order of
   `styles/_template/style-bible.md`, fill every TODO with what you saw, and end with 10–20 numbered rules for the planner, each with
   numbers. Map every observation onto an engine feature (table below).
6. **Check `style.json`.** Ranges come from only a few reels, so they are widened a little; fix anything that contradicts your
   eyes, and set `plan_defaults` (accent, era, music, trans).
7. **Report to the user** in 5–8 lines: pace, layout mix, captions, colours, sound, the 2–3 signature moves, and the profile path.

## Edit in a profile ("edit my video in this style")

```bash
python3 $S/autoplan.py $P --style ~/reels/styles/<handle> --cta WORD --lang en
```
`autoplan.py` stores the profile path in `plan.json → meta.style`. From then on: read the profile's `style-bible.md` before
planning (the engine docs in `references/` stay the same), and `plan_lint.py`, `build.py`, `finish.py` and `qa.py` use its numbers
automatically. A `montage-<handle>` skill folder is a valid profile too. Without `--style` the engine has only the fallback
numbers of `styles/_defaults`, which are not a style: make a profile first (SKILL.md part A).

## Observation → engine feature

| you see in the analyzed reels | use |
|---|---|
| split with an arch, the head crossing its top edge | default split (`era: "2026"`) |
| straight 50/50 split, captions in a grey box | `meta.era: "2025"` |
| hard cuts only | `meta.trans: "cut"` |
| soft push-ins, dissolves, zooms between scenes | `meta.trans: "auto"` |
| effects clearly audible, many per 10 s | `meta.profile: "bold"` |
| effects felt more than heard, few per 10 s | `meta.profile: "measured"` (levels from `style.json`) |
| the frame punches in at the start | `meta.open_punch` |
| the speaker snaps from a close-up into the split at the start | `meta.open_zoom` |
| a white flash at the start | `meta.flash_start` |
| warm light leaks on some cuts | `"trans": "leak"` on those beats |
| a title that scrambles through glyphs | `title` with `decode: true` |
| caption styles | `caption_style` per beat (`split`, `face`, `caps`, `mix`, `box`, `box_seam`, `face25`) |
| a font the kit does not have | the closest bundled one (Inter, Playfair Display, Noto Serif Display, Press Start 2P, Pixelify Sans, JetBrains Mono, Unbounded, Instrument Serif); to add a font, put its woff2 files in `assets/fonts/` with its licence and add `@font-face` rules to `assets/fonts/fonts.css` |
| a signature move the kit lacks | an `html` beat (see `shot-library.md`) |
| the face bigger or smaller than the fallback framing | `style.json → framing` (measured automatically when a face tracker is available) |

## Limits

- The engine builds one grid: split / face / full-frame graphic / b-roll. Other layouts (picture-in-picture, side-by-side) need
  `html` beats with the head hidden, or are out of reach.
- Caption animation is limited to the engine's caption styles; exotic kinetic typography can be approximated with `html`.
- Fonts, music and the creator's own footage are not copied: use free fonts, your own music and your own screenshots and clips.
- Framing and colours are measured; taste is not. The style bible is only as good as the breakdowns you write.
- Learn from public reels, do not copy them: don't reuse their frames, audio or script.
