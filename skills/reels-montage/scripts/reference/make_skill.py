#!/usr/bin/env python3
"""Packs a style profile (the result of "analyze this creator's montage") into its own Claude Code skill.

  python3 make_skill.py <profile_dir> [--name montage-<handle>] [--title "@handle"] [--dest ~/.claude/skills]

The new skill holds the profile's shareable files (style.json, style-bible.md, STYLE_METRICS.md, analysis/*.md, never raw/ or
work/) and a SKILL.md that tells Claude to edit with the reels-montage engine and this profile. After it, a request like
"edit my video in <handle>'s style" / «смонтируй в стиле <handle>» triggers the new skill in any session.
The profile folder itself can be passed as --style too: the skill folder is a valid profile.
"""
import os as _os, sys as _sys  # noqa: E401
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..")); import _env  # noqa: E402,F401  (runs the script in the kit's Python env, see _env.py)
import datetime, glob, json, os, re, shutil, sys

SKILL_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "creator"


def rules_block(bible):
    """the numbered rules for the planner from style-bible.md (the section whose heading mentions rules), else the first 40 lines"""
    lines = bible.splitlines(); out, on = [], False
    for ln in lines:
        if ln.startswith("#"):
            if on: break
            on = bool(re.search(r"(?i)rule|правил", ln))
            continue
        if on: out.append(ln)
    text = "\n".join(out).strip()
    return text or "\n".join(lines[:40]).strip()


def num(v, k="median"):
    return v.get(k) if isinstance(v, dict) else v


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"): raise SystemExit(__doc__)
    prof = os.path.abspath(os.path.expanduser(a[0]))
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if not os.path.isfile(os.path.join(prof, "style.json")): raise SystemExit(f"no style.json in {prof}: run analyze_reference.py … all first")
    bible_f = os.path.join(prof, "style-bible.md")
    if not os.path.isfile(bible_f):
        raise SystemExit(f"no style-bible.md in {prof}: turn style-bible.draft.md into style-bible.md first (references/style-profiles.md, step 5)")
    style = json.load(open(os.path.join(prof, "style.json")))
    handle = opt("--title") or style.get("name") or os.path.basename(prof)
    name = slug(opt("--name") or f"montage-{handle.lstrip('@')}")
    dest = os.path.abspath(os.path.expanduser(opt("--dest", "~/.claude/skills")))
    out = os.path.join(dest, name)
    if os.path.exists(out):
        bak = os.path.join(os.path.dirname(dest), "skills-backup", f"{name}-{datetime.datetime.now():%Y%m%d-%H%M%S}")
        os.makedirs(os.path.dirname(bak), exist_ok=True); shutil.move(out, bak); print(f"previous version moved to {bak}")
    os.makedirs(out)
    for f in ("style.json", "style-bible.md", "STYLE_METRICS.md", "reference-reels.md", "sources.json"):
        if os.path.isfile(os.path.join(prof, f)): shutil.copy(os.path.join(prof, f), out)
    an = sorted(glob.glob(os.path.join(prof, "analysis", "*")))
    if an:
        os.makedirs(os.path.join(out, "analysis"))
        for f in an:
            if os.path.isfile(f): shutil.copy(f, os.path.join(out, "analysis"))
    style["name"] = name; json.dump(style, open(os.path.join(out, "style.json"), "w"), ensure_ascii=False, indent=1)

    pace, lay, snd = style.get("pace", {}), style.get("layouts", {}), style.get("sound", {})
    facts = []
    if pace.get("wps"): facts.append(f"pace {pace['wps']:.1f} words/s")
    if num(pace.get("first_change")): facts.append(f"first picture change ≈ {num(pace['first_change']):.1f} s")
    if pace.get("beat_len_median"): facts.append(f"beat ≈ {pace['beat_len_median']:.1f} s")
    if lay: facts.append("layouts " + " / ".join(f"{k} {num(v):.0%}" for k, v in lay.items() if num(v) is not None))
    if snd.get("music_rel_voice_db") is not None: facts.append(f"music {snd['music_rel_voice_db']:.0f} dB under the voice")
    if num(snd.get("sfx_per_10s")): facts.append(f"{num(snd['sfx_per_10s']):.1f} effects per 10 s")
    n = style.get("reels") or len(an) or "several"
    engine = os.path.join(SKILL_DIR, "scripts").replace(os.path.expanduser("~"), "~")
    here = out.replace(os.path.expanduser("~"), "~")
    desc = (f"Edits a talking-head video (Reels, TikTok, Shorts) in the measured editing style of {handle}, made by reels-montage from a "
            f"frame-by-frame analysis of {n} of their reels ({'; '.join(facts[:3]) or 'pace, layouts, captions, sound'}). Use it whenever the user "
            f"asks to edit a video in {handle}'s style, like {handle}, in this style or in my style after this analysis, or in Russian "
            f"«смонтируй в стиле {handle}», «смонтируй как у {handle}», «смонтируй в этом стиле», «в моём стиле». Needs the reels-montage skill (the engine).")
    skill_md = f"""---
name: {name}
description: {json.dumps(desc, ensure_ascii=False)}
---

# Montage in the style of {handle}

Created on {datetime.date.today():%Y-%m-%d} by `reels-montage` from {n} reels of {handle}. This folder is a **style profile**: the numbers
(`style.json`), the style bible (`style-bible.md`), measurements (`STYLE_METRICS.md`) and beat sheets (`analysis/`). The engine is
the `reels-montage` skill.

## How to edit a take in this style
1. Read `~/.claude/skills/reels-montage/SKILL.md` (part **B. Edit a take**) and this folder's `style-bible.md` before planning.
2. Run every step of part B; pass this profile to the planner: `python3 {engine}/autoplan.py $P --style {here} …`.
   `autoplan.py` writes it into `plan.json → meta.style`, and `plan_lint.py`, `build.py`, `finish.py`, `qa.py` use its numbers.
3. Plan the beats with the rules below and the moves in `analysis/`; keep the engine's quality gates (lint, contact sheet, qa).

## The style in numbers
{chr(10).join('- ' + f for f in facts) or '- see STYLE_METRICS.md'}

## Rules for the planner (from style-bible.md)
{rules_block(open(bible_f).read())}
"""
    open(os.path.join(out, "SKILL.md"), "w").write(skill_md)
    print(f"skill '{name}' → {out}\nAsk for it by name or say «смонтируй в стиле {handle}»; the profile path for --style is {here}")


if __name__ == "__main__":
    main()
