# reels-montage

A Claude Code skill that edits a vertical talking-head video (Reels, TikTok, Shorts) in the editing style of a creator you pick.
It has no style of its own: you give it 2–5 reels of a creator whose editing you like, it measures them frame by frame and saves
the style as a skill of its own (`montage-<handle>`), then edits your videos in that style. [Русская версия ниже](#по-русски).

## The flow

1. **Install:** «Установи скилл HyperFrames от HeyGen и второй скилл монтажёра…» with the two links (or run `install.py` from the kit).
2. **Make your style:** «Разбери его монтаж и на основе этого создай уникальный скилл» + 2–5 reel links or files.
3. **Model:** `/model` → Opus.
4. **Edit:** «Смонтируй в моём стиле» + your video. Claude asks for anything it is missing (topic, names, call to action, colour).

The engine is [HyperFrames](https://github.com/heygen-com/hyperframes) (HTML + GSAP → mp4). Claude makes the editing decisions;
the scripts do the mechanical work and check it at three gates: plan lint, contact sheet, final QA against your style.

## Requirements

- Claude Code (Pro or Max). A Mac with Apple Silicon is the tested setup; Linux and Windows use fallbacks, untested.
- ffmpeg 7+, Node.js 22+, Python 3.9+. `install.py` sets up the rest (its own Python environment, the pinned HyperFrames CLI and
  its Chrome) and renders a 5-second test reel.
- `OPENAI_API_KEY` (transcription and reel analysis, cents per reel); optional `ELEVENLABS_API_KEY` (studio-clean voice) and
  `APIFY_TOKEN` (Instagram downloads). Keys go into `~/.config/reels-montage/keys.env`, never into the chat.

## Limitations

- Talking heads only: split / face / full-frame graphic / b-roll; other layouts need custom HTML beats.
- The style carries over by numbers and moves. Other creators' frames, music and scripts are never copied; downloaded reels stay
  on your computer for analysis only (frames and sound go to OpenAI with your key).
- Instagram often refuses anonymous downloads: log in to Instagram in Chrome, use Apify, or give the files.

`SKILL.md` (what Claude reads) · `references/` · `scripts/` · `styles/_defaults` (fallback numbers) · `styles/_template` ·
`assets/` (fonts, GSAP, sound kit, music) · `examples/` · `ASSETS.md` · `THIRD_PARTY_NOTICES.md` · `LICENSE` (MIT).

---

## По-русски

Скилл для Claude Code монтирует вертикальное видео с говорящей головой в стиле блогера, которого выберете вы. Своего стиля у него
нет. Вы даёте 2–5 роликов блогера, чей монтаж нравится. Скилл покадрово измеряет их и сохраняет стиль отдельным скиллом
`montage-<ник>`. Потом монтирует ваши видео в этом стиле.

1. «Установи скилл HyperFrames от HeyGen и второй скилл монтажёра от Игоря Косолапова» и две ссылки.
2. «Разбери его монтаж и на основе этого создай уникальный скилл» и ссылки на 2–5 роликов.
3. Модель: `/model`, затем Opus.
4. «Смонтируй в моём стиле» и ваше видео. Недостающее Claude спросит сам: о чём ролик, какие названия звучат, призыв в конце,
   цвет.

Нужны Mac на Apple Silicon (проверено), ключ OpenAI (центы за ролик) и по желанию ключ ElevenLabs для чистого голоса. Ключи вы
вставляете сами в `~/.config/reels-montage/keys.env`, в чат их не отправляйте.
