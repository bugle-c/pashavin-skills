---
name: reels-montage
description: Edits a vertical talking-head video (Reels, TikTok, Shorts) into a fast, graphics-driven reel in the editing style the user picks. It measures a creator's style from 2–5 of their reels, packs it as a new skill, then edits in it. Arch split, face punch-ins, full-frame graphics, 1–3-word captions, logos, counters and mini-UIs on the words, designed sound, CTA. Engine — HyperFrames. Use it for "edit my video like <creator>", "analyze this creator's editing", "edit this talking head with graphics and captions", "add sound design to my reel", or in Russian «смонтируй», «смонтируй в стиле…», «разбери монтаж», «сделай звуки в рилсе», «установи скилл» for this kit. For a talking-head reel it owns the edit end to end, so use it instead of generic video workflows (the hyperframes entry skill, talking-head-recut, embedded-captions).
---
# Reels montage

> **Кратко по-русски.** Скилл монтирует вертикальный ролик с говорящей головой в стиле, который выбрал сам пользователь. Своего
> стиля в скилле нет: сначала пользователь даёт 2–5 роликов блогера, чей монтаж ему нравится, скилл измеряет их и сохраняет стиль
> отдельным скиллом `montage-<ник>`. Потом монтирует видео пользователя в этом стиле: паузы, графика на словах, подписи, музыка,
> звуки, проверки качества. Путь как в ролике: «Установи скилл…» → «Разбери его монтаж и на основе этого создай уникальный скилл»
> + ссылки → модель Opus → «Смонтируй в моём стиле» + видео. Недостающее спрашивай у пользователя сам (раздел «Ask first»).
> Ключи: `OPENAI_API_KEY` (обязателен), `ELEVENLABS_API_KEY` и `APIFY_TOKEN` (по желанию), в `~/.config/reels-montage/keys.env`.
> Отвечай на языке пользователя, коротко, без технических подробностей, пока он сам не спросит.

The skill turns a raw talking-head take into a reel edited the way the creator the user chose edits. There is no built-in style:
every style is measured from reels the user picks, frame by frame (pace, cuts, layout shares, captions, fonts, colours, sound) and
kept as a style profile that is also its own skill.

It has three parts:
1. **Style profiles**: the numbers and rules of one creator's edit (`style.json`, `style-bible.md`, beat sheets), made with
   `scripts/reference/` and packed as a skill `montage-<handle>` by `make_skill.py`. `styles/_defaults/` holds only neutral
   fallback numbers for fields a profile lacks; `styles/_template/style-bible.md` is the skeleton of a style bible.
2. **The engine** (`scripts/`): a plan (`plan.json`) is turned deterministically into a HyperFrames HTML composition, then into mp4,
   then sound is designed from the graphic events.
3. **Quality gates**: the plan is linted before the build, a contact sheet is checked before the render, the finished reel is
   compared with the style's targets after.

Your job as the editor is the decisions: where to cut, which layout each beat gets, what to draw on each phrase. The scripts do
everything mechanical.

## The flow (as the user sees it)

| the user says | do |
|---|---|
| «Установи скилл HyperFrames от HeyGen и второй скилл монтажёра…» + links / "install the skill" | the kit: `START_HERE.md` and `install.py`. If the skill is already installed: `python3 $S/selftest.py`, report, and give the next prompt |
| «Разбери его монтаж и на основе этого создай уникальный скилл» + reel links or files / "analyze this creator's editing" | **A. Make a style skill** |
| «Смонтируй в моём стиле» + a video / "edit my video in my style / like <creator>" | **B. Edit a take** with the user's style skill (`montage-<handle>`); ask which one if there are several |
| an edit request and the user has no style yet | explain in one line that the style comes from reels they like, ask for 2–5 links or files, do A, then B |
| "make the sound" for an existing project | step 7 of B (`finish.py`) |

Recommend the strongest model for A and B (`/model` → Opus).

## Ask first

Ask only for what is missing, in one short message, then work without further questions.
- **Before A:** 2–5 links (Instagram, TikTok, YouTube Shorts) or files of reels by ONE creator, same format and period; the language
  of those reels. If Instagram refuses the download, ask whether to use their Chrome cookies (they must be logged in to Instagram
  in Chrome; macOS asks once for "Chrome Safe Storage" access, they click Allow), an Apify token, or the files themselves.
- **Before B:** the video file (vertical, the face about 40 % of the frame width); which style if they have several; what the
  reel is about in one sentence and the names of products, sites or people it mentions (for the logos, screenshots and whisper
  vocabulary); the call to action at the end (a keyword for comments, a link in the bio, or none); the accent colour (their
  brand, or the style's); the language. Offer, don't require: the script text (better captions), their own screenshots or screen
  recordings, links to what they mention, their own music. ElevenLabs gives a studio-clean voice if they have a key.
- Never ask them to paste API keys into the chat: open `~/.config/reels-montage/keys.env` for them to paste into.
- Frames and sound of the analyzed reels and of their own take go to OpenAI with their key; the video files stay on the computer.
  Say so once, before A.

## What to read and when

| when | file |
|---|---|
| before any plan, always | the style bible of the user's profile: `<profile>/style-bible.md` (a `montage-<handle>` skill folder is a profile) |
| choosing the graphic for a phrase | `references/shot-library.md` — trigger in the speech → move → `gfx` |
| cutting the text into beats | `references/beat-planning.md` — order of decisions and worked examples |
| writing `plan.json` | `references/plan-format.md` — every key of the plan and every graphic's parameters |
| making each reel feel new within the style | `references/move-bank.md` — moves by slot, and how to add depth |
| sound: what goes where, levels, checks | `references/sound-design.md`; background research: `references/sound-research.md` |
| the render breaks or looks odd | `references/engine-notes.md` — layers, framing, HyperFrames pitfalls, fallbacks off macOS |
| making a style profile | `references/style-profiles.md` and `references/beat-sheet-prompt.md` |
| a complete plan | `examples/plan.json` (a fictional reel, 27 beats, each with a `_note` on why) and `examples/README.md` |

## Requirements

- **HyperFrames**: the CLI pinned to the tested version, `npx -y hyperframes@0.8.78 …` (the scripts use the same pin;
  `$REELS_HYPERFRAMES` overrides it), Node 22+. The `hyperframes-core` / `hyperframes-cli` skills describe the engine contract.
- **ffmpeg 7+** (with libx264 and libvpx-vp9), **Python 3.9+** with `numpy` and `Pillow`. `install.py` puts them (and `yt-dlp`,
  and OpenCV off macOS) into the kit's own environment `~/.local/share/reels-montage/venv`; every script re-runs itself there, so
  plain `python3 $S/<script>.py` is always right. Optional: `playwright` (site screenshots), Demucs (sound stems in the analyzer).
- **macOS 12+ on Apple Silicon recommended**: the person cutout and the face track use Apple Vision through the prebuilt arm64
  helpers `scripts/person_mask` and `scripts/face_track`; when they do not run, `prep.py` rebuilds them from the `.swift` sources
  with `swiftc`. Elsewhere the cutout uses `hyperframes remove-background` (local u2net model) and the face track uses OpenCV or a
  centred estimate: check the head framing in the contact sheet then.
- **Keys** (never print them, never paste them into commands or files yourself): `OPENAI_API_KEY` (required: whisper-1
  transcription and the analyzer's frame/audio tagging), `ELEVENLABS_API_KEY` (optional: voice isolation, SFX generation),
  `APIFY_TOKEN` (optional: Instagram downloads). Looked up in the environment, `~/.config/reels-montage/keys.env`, `export` lines
  of `~/.zshrc`/`~/.bashrc`, then `~/.env/<service>.key`. A missing required key stops the script with a message.
- Costs are small: whisper ≈ $0.006 per minute of audio; analyzing a reel ≈ a few cents; Apify ≈ $0.01 per reel. ElevenLabs
  isolation and `sfx_gen.py` spend the user's ElevenLabs credits: ask before running them.

All commands below use:
```bash
S=~/.claude/skills/reels-montage/scripts      # the installed skill
P=~/reels/<date>-<slug>                        # the project folder, never inside the skill
```

## A. Make a style skill ("analyze their editing and create a unique skill")

```bash
D=~/reels/styles/<handle>
python3 $S/reference/fetch_reels.py $D <link or file> <link or file> ...    # 2–5 reels: Instagram, TikTok, Shorts, local files
python3 $S/reference/analyze_reference.py $D all --lang <en|ru|…>           # frames, cuts, words, layouts, captions, colours, framing, sound
```
Then read `$D/STYLE_METRICS.md` and every `$D/work/<id>/sheet.jpg`, write a beat sheet per reel with
`references/beat-sheet-prompt.md` into `$D/analysis/`, turn `$D/style-bible.draft.md` into `$D/style-bible.md` (the skeleton is
`styles/_template/style-bible.md`, end it with 10–20 numbered rules with numbers), and check `$D/style.json`. Details, the
observation → engine-feature table and the limits are in `references/style-profiles.md`. The downloaded reels stay private in
`$D/raw`: never republish them, never reuse their frames, music or script.

Pack the profile as its own skill, so «смонтируй в моём стиле» works in any later session:
```bash
python3 $S/reference/make_skill.py $D --title "@<handle>"      # → ~/.claude/skills/montage-<handle>/ (SKILL.md + the profile)
```
Report to the user in 5–8 lines: pace, layout mix, captions, colours, sound, the 2–3 signature moves, and the skill's name. Then
the next prompt: «Смонтируй в моём стиле» with their video attached.

## B. Edit a take

**1. Prepare the take**
```bash
python3 $S/prep.py init <raw.mov> $P --lang en --vocab "ProductName, OtherName" [--script script.txt]
```
Normalizes to 1080×1920 @30, gets word timings from whisper and writes `work/phrases.txt`. Read the phrases: find retakes, slips,
dead parts. `--vocab` teaches whisper product names; `--script` lays the known script over whisper's timings (restores spelling
and punctuation). The sound offset of phone MOVs is fixed automatically.
```bash
python3 $S/prep.py cut $P --drop 12.4-15.1,40.2-41.0
```
Cuts every pause longer than 0.18 s and the marked ranges → `work/clean.mp4` and a numbered `work/words.txt`. The word number is
`w:N` in the plan. **A take full of repeated attempts:** keep only the good ranges with `cut $P --keep 0.8-9.1,11.5-20.6,...`,
then re-transcribe the clean cut with `prep.py words $P --script script.txt` (whisper glues repeats together, so raw timings lie).
```bash
python3 $S/prep.py voice $P --isolate
python3 $S/prep.py face $P
python3 $S/prep.py cutout $P
```
Voice clean-up (`--isolate` uses ElevenLabs Audio Isolation, then the EQ/compression chain; without the key, the chain only), face track
(`work/face.json`), person cutout (`work/clean_subject.webm`). `prep.py all <raw> $P --lang en` runs everything.

**2. Assets** go to `$P/assets/`: logos, 3D emoji, GitHub cards and site screenshots come from `fetch_assets.py` (examples in
`shot-library.md`). The product needs real screenshots and screen recordings. A real person named in the script appears only on a
real photo you may use. Build every visual fresh for this reel.

**3. Plan**
```bash
python3 $S/autoplan.py $P --cta KEYWORD --lang en --style <profile folder> [--accent "#D97757"] [--era 2025]
```
Gives `plan.draft.json`: beats cut at phrases, layouts alternating like the style, `TODO` placeholders instead of graphics. Without
`--style` it uses the user's only profile, or stops and asks. Read the profile's `style-bible.md`, `beat-planning.md` and `shot-library.md`, replace every `TODO` with a concrete graphic, move beat borders and
layouts where needed, and save as `plan.json`.

**4. Lint the plan**
```bash
python3 $S/plan_lint.py $P [--projects ~/reels]
```
Zero errors required. Resolve the warnings about layout shares, long static beats, two faces in a row and a late first change.
With `--projects` (or `$REELS_PROJECTS`) it also fails a plan whose opening repeats one of the user's two latest reels.

**5. Build and contact sheet** (gate)
```bash
python3 $S/build.py $P
(cd $P/hf && npx -y hyperframes@0.8.78 lint .)
python3 $S/snap.py $P
```
Lint must show 0 errors (`nested_structure_needs_subcomposition` warnings are expected and harmless). `snap.py` writes one still
per beat to `work/snap_sheet.jpg`. Look at it with Read and check: every beat shows what is being said; no empty zones; captions
readable and off the eyes; the head sits right in the arch with nothing floating above the hair. Fix the plan and rebuild: a
snapshot takes seconds, a render takes minutes.

**6. Render**
```bash
PRODUCER_BROWSER_GPU_MODE=hardware npx -y hyperframes@0.8.78 render $P/hf -o $P/out/picture.mp4 --fps 30 --quality looks
```
About 2–3 minutes per 30–60 s of reel on a recent Mac; run it in the background. Drop the GPU variable off macOS. If Chrome
exits at once (a sandboxed agent shell on macOS blocks it), run the render with the sandbox off or ask the user to run the
command in their terminal; `npx -y hyperframes@0.8.78 doctor` shows what is missing.

**7. Sound and delivery** (details: `references/sound-design.md`)
```bash
python3 $S/finish.py $P $P/out/picture.mp4 --name <slug>
```
The engine places sounds from the graphic events: the opening swell (or the user's own riser in `open_riser/` of their kit), a whoosh on every scene change by transition type, pops,
clicks, typing, counter rolls that lock with a click, up to three hero moments (riser, music dip, impact, sparkle). Variants
rotate, pitch and level vary slightly, the music gives up only the voice band, buried key cues are raised until they cut
through. Profile `bold` (default) keeps every cue clearly audible; `measured` reproduces the style's quiet measured levels. Output:
`out/<slug>.mp4` at −14 LUFS and a light copy `out/<slug>_light.mp4` under 20 MB.

**8. Compare with the style** (gate)
```bash
python3 $S/qa.py $P
```
Compares pace, pauses, first change, layout shares, effect density and loudness with the style's targets and writes
`out/qa_sheet.jpg` (one frame per second). Look at it. Fix failures in the plan, not in the output.

## Craft rules that hold in any style

The numbers come from the user's style profile; these hold whatever it says:
1. **Speech from the first frame**; something moves on screen from frame one; the first picture change within about 3 s.
2. **Cuts on clause starts**, 20–60 ms before the word (`t0: "w:N"`).
3. **The layout changes on every cut**, in the style's shares; never two faces in a row.
4. **Everything said is drawn.** A brand → its logo, early. A number → a counter. A verb → a UI state change. A claim → proof: a
   screenshot, README or post. A person → their real photo you may use.
5. **Nothing stands still longer than 2 s.** Inside a long beat something changes every 0.3–0.6 s.
6. **One accent colour per reel**: only benefits, numbers, highlights and the CTA keyword get it.
7. **Captions** in the style's chunk size; no caption where the word is already drawn.
8. **Sound is half the edit**: an opening sound, a soft transition and a whoosh on every scene change, effects audible in profile
   `bold`, music under the whole reel.
9. **Every reel new, the style the same**: keep the grid, captions, accent discipline and sound system; change the opening, number
   treatment, backgrounds, music and custom moves each time (`references/move-bank.md`).
10. **Real interfaces, whole prompts, adult objects**: show an app the way viewers know it; a prompt types on screen in full, with
    the keyboard audible (`typing` with `dur`); an example person is made up, never a real third party without permission; objects
    are dark and premium (glow, big type, logos, mini-UIs), not cartoon 3D emoji on bright gradients.

A move the kit lacks (before/after, a slot-machine list, a logo morph) is built right in the plan as an `html` beat (example in
`shot-library.md`). Transitions are soft by default (`meta.trans: "auto"`); hard cuts are `meta.trans: "cut"`. Built-in moves:
the speaker snapping into the arch (`meta.open_zoom`), a white flash (`meta.flash_start`), glyph noise resolving into a pixel title
(`title` + `decode`), "IT'S CALLED" (`over_style: "caps"`), a warm light leak (`trans: "leak"`), a red strike through a
competitor's logo (`strike`). The 50/50 split with boxed captions is `meta.era: "2025"`.

## Pitfalls

- **Word indexes.** `w:N` points into `work/words.txt` of the clean cut. After re-cutting or `--words-only`, the numbers shift:
  re-check the plan.
- **Product names.** Whisper mangles names and splits hyphenated words; pass new names with `--vocab` and check
  `work/phrases.txt` after `init`.
- **Wide shots.** If the face is under ~300 px wide in the take, the close-up hits `face_scale_max` (2.2) and gets soft. Ask for
  takes where the face is about 40 % of the frame width.
- **Long numbers.** Numbers longer than 6 digits read better with `font: "serif"` (blur-in) than as a rolling odometer.
- **HyperFrames rules.** No video inside an element with `data-start`; animate only through `tl`; local fonts only. More in
  `engine-notes.md`.
- **Scores are not approval.** Script, lint and model scores are checks, not a verdict: the user judges the reel.

## Other languages

Every bundled font has Cyrillic except Instrument Serif. For Russian the engine sets the big italic caps to Noto Serif Display
(Playfair's italic Cyrillic "Т" reads like an apostrophe). Captions are cut by characters (16–20 per chunk). Keep product names in
Latin script. The CTA keeps its form (face close, italic connector, keyword in the accent) with the creator's own words; set the
keyword with `--cta` / `meta.cta_word`.

## Files

```
SKILL.md · README.md · ASSETS.md · LICENSE · THIRD_PARTY_NOTICES.md · requirements.txt
references/  shot-library · beat-planning · plan-format · engine-notes · move-bank · sound-design · sound-research
             style-profiles · beat-sheet-prompt
styles/      _defaults/style.json (engine fallback numbers) · _template/style-bible.md (skeleton)
examples/    plan.json (a fictional reel) · README.md
scripts/     prep · autoplan · plan_lint · build · snap · finish · qa · selftest · fetch_assets · sfx_gen · sfx_synth · common · _env (.py)
             face_track(.swift) · person_mask(.swift)
             reference/ fetch_reels · analyze_reference · make_skill · sfx_probe · sfx_extract · sfx_classify (.py)
assets/      base.css · runtime.js · fonts/ (+ LICENSES/) · vendor/gsap.min.js · sfx/<class>/ · music/
```
