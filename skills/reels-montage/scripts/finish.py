#!/usr/bin/env python3
"""Sound design + delivery: voice + music bed (carved under the voice) + placed SFX → −14 LUFS master, muxed onto the picture.

  python3 finish.py <project> [picture.mp4] [--name slug]
Reads work/voice.wav, work/timeline.json (sound events written by build.py) and plan.json meta:
  profile      bold (default) | measured      levels, music and density, see PROFILES and references/sound-design.md
  music        tense_a (default, dark tense bed) | tense_b | tense_c | tense_d | ambient_tech_90 | lofi_keys_84 | path to your own mp3/wav
  music_rel_db music level vs the voice speech level, dB        sfx_offset_db   shift of every SFX level
  sfx_per_10s  density cap                                        open_sfx       riser (bold) | swell (measured) | false | path to a riser wav
  open_rate    speed-up of an opening riser (1.2)                 sfx_dir        your own SFX kit folder (<class>/<class>_a.wav …)
Writes out/<slug>.mp4 (master), out/<slug>_light.mp4 (crf 28, < 20 MB for phones), work/sfx_used.json (what was placed where).

How levels work: every SFX level is the PEAK of that sound relative to the voice's speech RMS (dB). In a quiet, measured mix
whooshes and clicks peak 24–26 dB under the voice RMS (felt more than heard), the opening sub swell ≈ 12–16 dB under and the
music bed takes its level from the style profile: that is profile "measured". Profile "bold" (default) makes every cue clearly audible:
whooshes and pops 4–6 dB under the voice RMS, music ≈ 15 dB under, up to 12 cues per 10 s.

The opening. Profile bold opens on the kit's riser (assets/sfx/open_riser: a riser that builds and stops dead): it is sped up
1.2× like a sampler, trimmed from the front so its hard stop lands on the first scene change (or on the first hero reveal right
after it), a deep sub hit lands the cut, and the music waits under it at −9 dB and opens on the cut. Profile measured (and bold
with a kit that has no riser) opens on a synthesised sub swell (assets/sfx/open).
A prompt typing on screen (a "typing" cue with "dur" in the plan) plays the keyboard for the whole typing, sped up 1.5×, at
+3 dB vs the voice RMS in profile bold, while the music ducks ≈ 12 dB and comes back after it.
SFX kit lookup: meta.sfx_dir → $REELS_SFX_DIR → the bundled assets/sfx. A class missing everywhere falls back to a related
class (tap → click, reveal → chime, …); generate richer ones with sfx_gen.py (needs ELEVENLABS_API_KEY).
"""
import os as _os, sys as _sys  # noqa: E401
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import _env  # noqa: E402,F401  (runs the script in the kit's Python env, see _env.py)
import functools, hashlib, json, os, re, subprocess, sys, wave
try:
    import numpy as np
except ImportError:
    raise SystemExit("this script needs numpy and Pillow: python3 -m pip install -r requirements.txt (in the skill folder)")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import SKILL, era_view, load_style  # noqa: E402

BUNDLED_SFX = f"{SKILL}/assets/sfx"

# per kind: level = SFX peak vs voice speech RMS (dB) in each profile; align = where the event time sits on the sound
#   onset: sound starts at t (beds: typing, count) · peak: loudest point (the transient) lands at t + shift · end: sound ends at t (risers into a reveal)
#   start: starts at t exactly · cut: an opening riser whose hard stop lands on the first scene change
KINDS = {
    "open":        dict(bold=-2,  measured=-12, align="start", prio=0, shift=0.0),
    "open_riser":  dict(bold=4,   measured=-4,  align="cut",   prio=0, shift=0.0),    # peak +4 dB vs the voice RMS ≈ 4 LU under the voice (the energy is low)
    "whoosh":      dict(bold=-4,  measured=-24, align="peak",  prio=1, shift=0.12),   # reference: whoosh peaks ≈ 0.2–0.25 s after the cut, on the graphic's fly-in
    "whoosh_low":  dict(bold=-4,  measured=-24, align="peak",  prio=1, shift=0.10),   # punch-in/out to the face: a low whoomp (reference whooshes are mostly 80–250 Hz)
    "whoosh_soft": dict(bold=-8,  measured=-26, align="peak",  prio=2, shift=0.12),
    "impact":      dict(bold=-4,  measured=-22, align="peak",  prio=1, shift=0.0),
    "punch":       dict(bold=-3,  measured=-20, align="peak",  prio=1, shift=0.0),    # a cartoon hit in a custom opening (a mascot fights a logo)
    "shatter":     dict(bold=-3,  measured=-20, align="onset", prio=1, shift=0.0),    # glass/logo breaking: starts on the impact frame
    "riser_soft":  dict(bold=-9,  measured=-26, align="end",   prio=4, shift=0.0),
    "pop":         dict(bold=-5,  measured=-24, align="peak", prio=2, shift=0.01),
    "chime":       dict(bold=-6,  measured=-24, align="peak", prio=2, shift=0.01),
    "ding":        dict(bold=-6,  measured=-24, align="peak", prio=2, shift=0.01),
    "reveal":      dict(bold=-7,  measured=-24, align="peak", prio=2, shift=0.01),
    "glitch":      dict(bold=-8,  measured=-26, align="peak", prio=2, shift=0.01),
    "error":       dict(bold=-6,  measured=-24, align="peak", prio=2, shift=0.01),
    "click":       dict(bold=-6,  measured=-24, align="peak", prio=3, shift=0.01),
    "tap":         dict(bold=-5,  measured=-24, align="peak", prio=3, shift=0.01),
    "toggle":      dict(bold=-6,  measured=-24, align="peak", prio=3, shift=0.01),
    "send":        dict(bold=-5,  measured=-24, align="peak", prio=3, shift=0.01),
    "shutter":     dict(bold=-6,  measured=-24, align="peak", prio=3, shift=0.01),
    "swipe":       dict(bold=-8,  measured=-26, align="peak", prio=3, shift=0.01),
    "tick":        dict(bold=-9,  measured=-27, align="peak", prio=4, shift=0.01),
    "blip":        dict(bold=-8,  measured=-26, align="peak", prio=4, shift=0.01),
    "typing":      dict(bold=-11, measured=-28, align="onset", prio=5, shift=0.0),
    "count":       dict(bold=-10, measured=-28, align="onset", prio=5, shift=0.0),
}
# a class that is missing from every kit borrows a related one
ALIAS = {"tap": "click", "toggle": "click", "shutter": "click", "send": "whoosh_soft", "blip": "tick", "reveal": "chime", "typing": "click",
         "count": "tick", "riser_soft": "whoosh_soft", "punch": "impact", "shatter": "glitch", "whoosh_low": "whoosh", "whoosh_soft": "whoosh",
         "swipe": "whoosh_soft", "chime": "ding", "ding": "chime", "glitch": "click", "error": "click", "tick": "click"}
PROFILES = {
    "bold":     dict(music_rel_db=-15.0, sfx_per_10s=12.0, min_gap=0.12, carve=True, open="riser"),   # the kit's riser, or the swell when a kit has none
    "measured": dict(music_rel_db=None, sfx_per_10s=None, min_gap=0.5, carve=True, open="swell"),   # None = from the style profile
}
BEDS = ("typing", "count")   # continuous textures may overlap other sounds
STAGED = ("punch", "shatter")   # a staged hit in the plan (a punch, a logo breaking) layers with the landing, never thinned out
# a prompt that types on screen for a while (a typing cue with "dur"): the keyboard plays the whole time, clearly audible, while the
# music ducks ≈ 12 dB (quiet while the prompt types, but the keyboard is heard); +3 dB peak vs the voice RMS
TYPING_LONG_DB = {"bold": 3.0}


def sh(*a):
    a = list(a)
    if a and os.path.basename(str(a[0])) == "ffmpeg" and "-/filter_complex" in a:
        index = a.index("-/filter_complex")
        with open(a[index + 1], encoding="utf-8") as graph:
            a[index:index + 2] = ["-filter_complex", graph.read()]
    r = subprocess.run(list(a), capture_output=True, text=True)
    if r.returncode: raise SystemExit(f"FAILED {' '.join(a[:5])}\n{r.stderr[-1500:]}")
    return r


def load(f):
    with wave.open(f) as w:
        n, ch, sr = w.getnframes(), w.getnchannels(), w.getframerate(); a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768
    return a.reshape(-1, ch).mean(axis=1), sr


def speech_db(wav):
    a, sr = load(wav); h = int(sr * 0.05)
    e = np.array([np.sqrt(np.mean(a[i * h:(i + 1) * h] ** 2)) + 1e-9 for i in range(len(a) // h)]); db = 20 * np.log10(e)
    return float(np.median(db[db > np.percentile(db, 40)]))


def mean_db(f):
    err = subprocess.run(["ffmpeg", "-v", "info", "-i", f, "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.search(r"mean_volume: (-?[\d.]+)", err).group(1))


_INFO = {}
def info(f):
    """peak level (dBFS), time of the loudest 10 ms and of the hardest drop (a riser's cut) of a kit file"""
    if f not in _INFO:
        if not f.lower().endswith(".wav"):   # own risers may come as mp3/m4a: analyse a wav copy
            tmp = f"{f}.tmp_analysis.wav"; sh("ffmpeg", "-y", "-v", "error", "-i", f, "-ar", "48000", tmp); a, sr = load(tmp); os.remove(tmp)
        else: a, sr = load(f)
        h = int(sr * 0.01); env = np.array([np.sqrt(np.mean(a[i * h:(i + 1) * h] ** 2)) for i in range(max(1, len(a) // h))])
        db = 20 * np.log10(env + 1e-9); drop = db[:-3] - db[3:] if len(db) > 3 else np.zeros(1)
        _INFO[f] = dict(peak=20 * np.log10(np.max(np.abs(a)) + 1e-9), t_peak=float(np.argmax(env)) * 0.01, dur=len(a) / sr, t_cut=(float(np.argmax(drop)) + 1) * 0.01)
    return _INFO[f]


SFX_DIRS = [BUNDLED_SFX]


def variants(kind, seen=()):
    """files of a class: the first kit that has it wins; a class missing everywhere borrows its ALIAS"""
    for d in SFX_DIRS:
        sub = os.path.join(d, kind)
        files = sorted(os.path.join(sub, x) for x in os.listdir(sub) if x.lower().endswith(".wav")) if os.path.isdir(sub) else []
        if not files and os.path.exists(os.path.join(d, f"{kind}.wav")): files = [os.path.join(d, f"{kind}.wav")]
        if files: return files
    alt = ALIAS.get(kind)
    return variants(alt, seen + (kind,)) if alt and alt not in seen else []


def pick(kind, k):
    """round-robin through the variants of a kind; deterministic, never the same file twice in a row"""
    fs = variants(kind)
    return fs[k % len(fs)] if fs else None


def label(f):
    for d in SFX_DIRS:
        if f.startswith(d + os.sep): return os.path.relpath(f, d)
    return os.path.basename(f)


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"): raise SystemExit(__doc__)
    P = os.path.abspath(a[0]); pic = a[1] if len(a) > 1 and not a[1].startswith("--") else f"{P}/out/picture.mp4"
    plan = json.load(open(f"{P}/plan.json")); meta = plan.get("meta", {}); tlj = json.load(open(f"{P}/work/timeline.json")); D = tlj["duration"]
    prof_name = meta.get("profile", "bold")
    if prof_name not in PROFILES: print(f"unknown profile '{prof_name}', using 'bold'"); prof_name = "bold"
    prof = dict(PROFILES[prof_name]); era25 = str(meta.get("era", "2026")) == "2025"
    S = era_view(load_style(meta.get("style"), P), meta.get("era", "2026")); snd = S["sound"]
    if prof_name == "measured":
        prof["music_rel_db"] = snd.get("music_mix_rel_db", snd["music_rel_voice_db"]); prof["sfx_per_10s"] = snd["sfx_per_10s"]["median"]
    elif era25: prof.update(music_rel_db=-12.0, sfx_per_10s=12.0, min_gap=0.15)
    for d in (meta.get("sfx_dir"), os.environ.get("REELS_SFX_DIR")):
        if d:
            d = d if os.path.isabs(os.path.expanduser(d)) else os.path.join(P, d); d = os.path.abspath(os.path.expanduser(d))
            if os.path.isdir(d): SFX_DIRS.insert(len(SFX_DIRS) - 1, d)
            else: print(f"sfx kit folder not found, ignored: {d}")
    slug = a[a.index("--name") + 1] if "--name" in a else os.path.basename(P)
    voice = f"{P}/work/voice.wav"; w = f"{P}/work/_mix"; os.makedirs(w, exist_ok=True)
    vdb = speech_db(voice)

    # ---- events: build.py's list + the opening, thinned by priority and spacing
    evs = [dict(e) for e in tlj["sfx"] if e["t"] < D - 0.05]; locked, dips = [], []
    opening = meta.get("open_sfx", prof["open"]); opening = prof["open"] if opening is True else opening; t_cut = None
    riser = None
    if opening and opening != "swell":
        if opening == "riser": riser = pick("open_riser", 0)
        else:
            cand = opening if os.path.isabs(os.path.expanduser(str(opening))) else os.path.join(P, str(opening)); cand = os.path.expanduser(cand)
            riser = cand if os.path.exists(cand) else None
        if not riser:
            if meta.get("open_sfx"): print(f"opening riser '{opening}' not found (add a riser wav to your kit's open_riser/ folder or give a path); using the swell")
            opening = "swell"
    if riser and not any(e["kind"].startswith("open") for e in evs):
        # the riser's hard cut lands on the first scene change (≥ 0.7 s), or on the first hero reveal right after it
        t_cut = next((b["t0"] for b in tlj["beats"][1:] if b["t0"] >= 0.7), min(1.6, D / 2))
        t_cut = next((e["t"] for e in evs if e["kind"] == "hero" and -0.1 <= e["t"] - t_cut <= 0.35), t_cut)
        evs.append(dict(t=0.0, kind="open_riser", cut=t_cut, file=riser))
        locked.append(dict(t=t_cut, kind="impact", db=2.0, landing=1, hero=1, file=next((f for f in variants("impact") if "sub_hit" in f), None)))   # the riser lands on a deep hit
    elif opening and not any(e["kind"].startswith("open") for e in evs): evs.append(dict(t=0.0, kind="open"))
    cap = int(round(D / 10 * float(meta.get("sfx_per_10s", prof["sfx_per_10s"])))); gap = prof["min_gap"]
    heroes = sorted((e for e in evs if e["kind"] == "hero"), key=lambda e: e["t"])[:3]; evs = [e for e in evs if e["kind"] != "hero"]
    for h in heroes:   # the hero reveal: riser that ends on the reveal, a beat of music dip before it, layered hit, sparkle ~0.8 s later
        if t_cut is not None and abs(h["t"] - t_cut) <= 0.1: dips.append((max(0.0, h["t"] - 0.35), h["t"] + 0.02)); continue   # the opening riser and its hit already make this reveal
        locked += [dict(t=h["t"], kind="riser_soft", hero=1), dict(t=h["t"], kind="impact", hero=1)]
        if not any(h["t"] + 0.5 < e["t"] < h["t"] + 1.1 for e in evs): locked.append(dict(t=h["t"] + 0.8, kind="chime", hero=1))
        dips.append((max(0.0, h["t"] - 0.35), h["t"] + 0.02))
    evs = [e for e in evs if e["kind"] in BEDS + STAGED or not any(abs(e["t"] - x["t"]) < 0.12 for x in locked)]
    if any(e["kind"] == "open" for e in evs): evs = [e for e in evs if e["kind"] == "open" or e["kind"] in STAGED or e["t"] >= 0.6]   # the opening "fade" owns the first 0.6 s; a staged fight keeps its hits
    if t_cut is not None:   # the riser owns everything up to its cut and the scene whoosh on it; the music waits under it and opens on the cut
        evs = [e for e in evs if e["kind"] == "open_riser" or e["kind"] in STAGED or e["t"] >= t_cut + 0.2]; dips.append((0.0, t_cut))   # a staged fight keeps its hits
    kept = list(locked)
    for e in sorted(evs, key=lambda e: (KINDS.get(e["kind"], KINDS["click"])["prio"], e["t"])):
        if len(kept) >= cap and not e["kind"].startswith("open"): continue
        if e["kind"] not in BEDS + STAGED and any(abs(e["t"] - x["t"]) < gap and x["kind"] not in BEDS and not x.get("hero") for x in kept): continue   # staged hits layer on purpose
        kept.append(e)
    kept.sort(key=lambda e: e["t"])

    # typing on screen (a typing cue with "dur"): the bed steps back ≈ 12 dB so the keys are heard, then comes back
    tdips = [(e["t"], e["t"] + float(e["dur"])) for e in kept if e["kind"] == "typing" and e.get("dur")]
    # ---- music bed: level vs the voice, fade in under the opening
    mname = str(meta.get("music") or S.get("plan_defaults", {}).get("music") or "tense_a")
    mpath = next((c for c in (os.path.expanduser(mname), os.path.join(P, mname), f"{SKILL}/assets/music/{mname}.mp3") if os.path.isfile(c)), None)
    if not mpath:
        have = sorted(f[:-4] for f in os.listdir(f"{SKILL}/assets/music") if f.endswith(".mp3"))
        raise SystemExit(f"music '{mname}' not found: use one of {have} or a path to your own track")
    rel = float(meta.get("music_rel_db", prof["music_rel_db"])); g = vdb + rel - mean_db(mpath)
    sh("ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-i", mpath, "-t", f"{D:.3f}", "-af",
       f"volume={g:.2f}dB," + (f"volume='if({'+'.join(f'between(t,{a:.3f},{b:.3f})' for a, b in dips)},0.35,1)':eval=frame," if dips else "")
       + ((lambda rs: f"volume='1-0.75*{rs}':eval=frame,")(
           functools.reduce(lambda x, y: f"max({x},{y})", [f"clip((t-{a:.3f})/0.15,0,1)*clip(({b:.3f}-t)/0.2,0,1)" for a, b in tdips])) if tdips else "")   # smooth ≈ −12 dB duck
       + f"afade=t=in:d=0.3,afade=t=out:st={max(D - 1.2, 0):.3f}:d=1.2", "-ar", "48000", "-ac", "2", f"{w}/music.wav")

    # ---- place every sound (as a function of per-cue boosts, so buried cues can be rescued in a second pass)
    def render_sfx(boost, alt=None):
        alt = alt or {}
        ins, fc, labs, used, count = [], [], [], [], {}
        for e in kept:
            kind = e["kind"] if e["kind"] in KINDS else "click"; k = count.get(kind, 0); count[kind] = k + 1
            f = e.get("file") or pick(kind, k + alt.get(len(labs), 0))   # a buried cue may try another variant of its class
            if not f: continue
            spec = KINDS[kind]; inf = info(f)
            base_lvl = TYPING_LONG_DB.get(prof_name, spec[prof_name]) if kind == "typing" and e.get("dur") else spec[prof_name]   # a prompt typing on screen is a feature, not a bed
            lvl = (e["db"] if e.get("db") is not None else base_lvl) + float(meta.get("sfx_offset_db", 0))
            hh = int(hashlib.md5(f"{kind}{k}".encode()).hexdigest(), 16)
            jit = 0.0 if kind.startswith("open") or e.get("landing") else (hh % 31 - 15) / 10   # ±1.5 dB
            spread = 6 if kind.startswith("whoosh") else 3   # whooshes repeat most: ±6 %, the rest ±3 % pitch/speed
            rate = 1.0 if kind in BEDS or kind == "open" else 1 + ((hh // 31) % (2 * spread + 1) - spread) / 100
            gain = vdb + lvl + jit - inf["peak"] + boost.get(len(labs), 0.0)
            if kind == "open_riser":   # trimmed from the front so the hard cut lands on e["cut"], sped up like a sampler, 0.6 s of its tail
                rate = float(meta.get("open_rate", 1.2)); c = inf["t_cut"]; s0 = max(0.0, c - e["cut"] * rate); start = max(0.0, e["cut"] - c / rate)
                body = (f"atrim=start={s0:.3f}:end={c + 0.6 * rate:.3f},asetpts=PTS-STARTPTS,asetrate={48000 * rate:.0f},aresample=48000,highpass=f=35,equalizer=f=1400:t=o:w=3:g=-4,"
                        f"afade=t=in:d=0.2,afade=t=out:st={(c - s0) / rate + 0.2:.3f}:d=0.4,")
                t_pk = start + (c - s0) / rate - 0.04   # the loudest moment is right before the cut
            else:
                if spec["align"] == "peak": start = e["t"] + spec["shift"] - inf["t_peak"] / rate
                elif spec["align"] == "end": start = e["t"] - inf["dur"] / rate
                elif spec["align"] == "start": start = e["t"]
                else: start = e["t"] - 0.005
                start = max(0.0, start)
                dur = float(e.get("dur") or 0.9) if kind == "typing" else min(inf["dur"], 3.0)   # typing lasts as long as the text types on screen
                eq = {"open": "", "impact": "", "whoosh_low": "lowpass=f=5000,", "whoosh": "highpass=f=110,lowpass=f=6500,", "whoosh_soft": "highpass=f=110,lowpass=f=6500,"
                      }.get(kind, "highpass=f=140,")   # low end stays with voice and bed; whooshes never get a bright "ninja" top
                pitch = f"asetrate={48000 * rate:.0f},aresample=48000," if rate != 1.0 else ""
                fades = f"afade=t=in:d=0.04,afade=t=out:st={max(0.0, dur - 0.12):.3f}:d=0.12," if kind == "typing" else ""
                tempo = "atempo=1.5," if kind == "typing" else ""   # on-screen typing is fast: denser keys, same pitch
                body = f"{pitch}{tempo}atrim=0:{dur:.3f},{fades}{eq}"; t_pk = start + inf["t_peak"] / rate
            ins += (["-stream_loop", "-1"] if kind == "typing" and float(e.get("dur") or 0) > inf["dur"] else []) + ["-i", f]; j = len(labs)   # long typing loops the keyboard clip
            fc.append(f"[{j}:a]aformat=channel_layouts=stereo,aresample=48000,{body}volume={gain:.2f}dB,adelay={int(start * 1000)}:all=1[e{j}]"); labs.append(f"[e{j}]")
            used.append(dict(t=round(e["t"], 3), start=round(start, 3), kind=kind, file=label(f), level_db=round(lvl + jit, 1),
                             t_peak=round(t_pk, 3), hero=bool(e.get("hero"))))
        json.dump(used, open(f"{P}/work/sfx_used.json", "w"), indent=0)
        if labs:
            fc.append("".join(labs) + f"amix=inputs={len(labs)}:normalize=0:duration=longest,apad,atrim=0:{D:.3f}[o]")
            open(f"{w}/sfx_graph.txt", "w").write(";".join(fc))
            sh("ffmpeg", "-y", "-v", "error", *ins, "-/filter_complex", f"{w}/sfx_graph.txt", "-map", "[o]", "-ar", "48000", "-ac", "2", f"{w}/sfx.wav")
        else:
            sh("ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", f"{D:.3f}", f"{w}/sfx.wav")
        return used

    # ---- audibility, closer to hearing than a level meter: in a 60 ms window around each cue's peak, compare its energy with voice + music
    # in four bands. A cue louder than everything else in at least one band cuts through (masking works per band). Buried key cues are
    # raised just enough to cut through (max +6 dB) in one more pass; the ones still buried are reported.
    vv, sr = load(voice); mm, _ = load(f"{w}/music.wav")
    BANDS = [(60, 250), (250, 1000), (1000, 4000), (4000, 12000)]
    def band_e(x, a0):
        seg = x[int(max(0, a0) * sr):int(max(0, a0) * sr) + int(0.06 * sr)]
        if len(seg) < 16: return np.full(len(BANDS), 1e-12)
        S_ = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) ** 2; f = np.fft.rfftfreq(len(seg), 1 / sr)
        return np.array([S_[(f >= lo) & (f < hi)].sum() + 1e-12 for lo, hi in BANDS])
    KEY = ("open", "open_riser", "punch", "shatter", "whoosh", "impact", "pop", "chime", "ding", "glitch", "error")
    def audit(used):
        ss, _ = load(f"{w}/sfx.wav")
        for u in used:
            if u["kind"] in BEDS: continue
            a0 = u["t_peak"] - 0.03; snr = 10 * np.log10(band_e(ss, a0) / (band_e(vv, a0) + band_e(mm, a0)))
            u["band_snr_db"] = round(float(snr.max()), 1); u["band"] = "%d-%d Hz" % BANDS[int(np.argmax(snr))]
        return used
    boost, alt = {}, {}
    used = audit(render_sfx(boost))
    for attempt in range(3):   # raise buried key cues (max +6 dB); if raising is not enough, try the next variant of the class
        bad = [j for j, u in enumerate(used) if u["kind"] in KEY and u.get("band_snr_db", 9) < 0]
        if not bad: break
        for j in bad:
            if boost.get(j, 0) >= 6.0: alt[j] = alt.get(j, 0) + 1; boost[j] = 3.0
            else: boost[j] = min(6.0, boost.get(j, 0) + 1.0 - used[j]["band_snr_db"])
        used = audit(render_sfx(boost, alt))
    for j, u in enumerate(used): u["boost_db"] = round(boost.get(j, 0.0), 1)
    json.dump(used, open(f"{P}/work/sfx_used.json", "w"), indent=0)
    buried = [f"{u['kind']}@{u['t']:.2f}s {u['band_snr_db']} dB" for u in used if u["kind"] in KEY and u.get("band_snr_db", 9) < 0]
    lifts = sorted(u["band_snr_db"] for u in used if "band_snr_db" in u)

    # ---- mix. Carve: the bed gives the voice only the band it needs (250 Hz–4 kHz ducks up to ~6 dB while the speaker talks, lows and
    # highs stay), then the whole bed breathes ~2 dB. After that a gentle glue compressor, loudness to −14 LUFS, ceiling −1 dBTP.
    carve = meta.get("carve", prof["carve"])
    if carve:
        graph = ("[0:a]aresample=48000,aformat=channel_layouts=stereo,asplit=3[v][k1][k2];"
                 "[1:a]asplit=3[ml][mm][mh];[ml]lowpass=f=250[l];[mm]highpass=f=250,lowpass=f=4000[m];[mh]highpass=f=4000[h];"
                 "[m][k1]sidechaincompress=threshold=0.015:ratio=4:attack=15:release=380:makeup=1[mc];"
                 "[l][mc][h]amix=inputs=3:normalize=0[mb];[mb][k2]sidechaincompress=threshold=0.02:ratio=1.8:attack=25:release=450:makeup=1[bed];"
                 "[v][bed][2:a]amix=inputs=3:normalize=0:duration=first,acompressor=threshold=-16dB:ratio=2:attack=12:release=160:makeup=1,alimiter=limit=0.95:level=0[a]")
    else:
        graph = "[0:a]aresample=48000,aformat=channel_layouts=stereo[v];[v][1:a][2:a]amix=inputs=3:normalize=0:duration=first,alimiter=limit=0.95:level=0[a]"
    open(f"{w}/mix_graph.txt", "w").write(graph)
    sh("ffmpeg", "-y", "-v", "error", "-i", voice, "-i", f"{w}/music.wav", "-i", f"{w}/sfx.wav", "-/filter_complex", f"{w}/mix_graph.txt", "-map", "[a]", "-t", f"{D:.3f}", f"{w}/pre.wav")
    err = subprocess.run(["ffmpeg", "-v", "info", "-i", f"{w}/pre.wav", "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", err)[-1]); g2 = -14.0 - I
    sh("ffmpeg", "-y", "-v", "error", "-i", f"{w}/pre.wav", "-af", f"volume={g2:.2f}dB,alimiter=limit=0.89:level=0:attack=3:release=60", "-c:a", "aac", "-b:a", "192k", f"{w}/mix.m4a")
    os.makedirs(f"{P}/out", exist_ok=True); master = f"{P}/out/{slug}.mp4"; light = f"{P}/out/{slug}_light.mp4"
    sh("ffmpeg", "-y", "-v", "error", "-i", pic, "-i", f"{w}/mix.m4a", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy", "-shortest", "-movflags", "+faststart", master)
    sh("ffmpeg", "-y", "-v", "error", "-i", master, "-c:v", "libx264", "-crf", "28", "-preset", "medium", "-c:a", "copy", "-movflags", "+faststart", light)
    err = subprocess.run(["ffmpeg", "-v", "info", "-i", master, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    I2 = re.findall(r"I:\s+(-?[\d.]+) LUFS", err)[-1]; tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", err)
    kinds = {}
    for u in used: kinds[u["kind"]] = kinds.get(u["kind"], 0) + 1
    print(f"profile {prof_name}; voice {vdb:.1f} dBFS; music {os.path.basename(mpath)} at {rel} dB; {len(used)} sounds ({', '.join(f'{k} {n}' for k, n in sorted(kinds.items()))}); "
          f"carve {'on' if carve else 'off'}; loudness {I2} LUFS, true peak {tp[-1] if tp else '?'}\n"
          f"audibility: median best-band SNR {lifts[len(lifts) // 2] if lifts else 0} dB (≥ 0 = the cue cuts through), {len(boost)} buried cues raised" + (f"; still buried: {', '.join(buried)}" if buried else "; every key cue cuts through") +
          f"\n→ {master}\n→ {light} ({os.path.getsize(light) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
