#!/usr/bin/env python3
"""QA of a rendered reel against the measured targets of its style profile (plan meta.style, default: the engine defaults).

  python3 qa.py <project> [out/<slug>.mp4]
Prints measured vs style targets and writes out/qa_sheet.jpg (1 frame per second) to look at. Exit 1 on hard failures
(loudness off, captions missing, wrong opening/closing layout).
"""
import os as _os, sys as _sys  # noqa: E401
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import _env  # noqa: E402,F401  (runs the script in the kit's Python env, see _env.py)
import json, os, re, statistics as st, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import era_view, load_style  # noqa: E402


def sh(*a):
    return subprocess.run(list(a), capture_output=True, text=True)


def main(P, video):
    tl = json.load(open(f"{P}/work/timeline.json")); W = json.load(open(f"{P}/work/words.json"))["words"]; D = tl["duration"]; fails, warns = [], []
    meta = json.load(open(f"{P}/plan.json")).get("meta", {})
    S = era_view(load_style(meta.get("style"), P), meta.get("era", "2026")); pace, snd, L = S["pace"], S["sound"], S["layouts"]
    bold = meta.get("profile", "bold") != "measured"
    err = sh("ffmpeg", "-v", "info", "-i", video, "-af", "ebur128=peak=true", "-f", "null", "-").stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", err)[-1]); tp = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", err)[-1])
    if abs(I - (-14.0)) > 1.0: fails.append(f"loudness {I} LUFS (target -14 ±1)")
    if tp > -0.5: fails.append(f"true peak {tp} dBTP (must be ≤ -0.5)")
    gaps = sorted(b["start"] - a["end"] for a, b in zip(W, W[1:])); wps = len(W) / max(W[-1]["end"] - W[0]["start"], 1e-6)
    if gaps and gaps[-1] > 0.6: warns.append(f"longest pause {gaps[-1]:.2f}s — re-run prep.py cut with a smaller --max-gap")
    share = {"split": 0, "graphic": 0, "face": 0}; runs = []
    for b in tl["beats"]:
        lay = "graphic" if b["layout"] in ("graphic", "broll") else b["layout"]; d = b["t1"] - b["t0"]; share[lay] += d / D
        if runs and runs[-1][0] == lay: runs[-1][1] += d
        else: runs.append([lay, d])
    if S.get("open_layout") and tl["beats"][0]["layout"] != S["open_layout"]: fails.append(f"opening beat is not {S['open_layout']} (style '{S.get('name')}')")
    if S.get("close_layout") and tl["beats"][-1]["layout"] != S["close_layout"]: fails.append(f"closing beat is not {S['close_layout']} (style '{S.get('name')}')")
    first_change = tl["beats"][1]["t0"] if len(tl["beats"]) > 1 else D
    sfx = json.load(open(f"{P}/work/sfx_used.json")) if os.path.exists(f"{P}/work/sfx_used.json") else tl["sfx"]
    dens = 10 * len(sfx) / D; ref_sfx = snd["sfx_per_10s"]
    cap_sfx = 13 if bold else ref_sfx["hi"] + 2
    if dens > cap_sfx: warns.append(f"{dens:.1f} SFX per 10 s — busier than the {'bold profile' if bold else 'style'} allows; lower meta.sfx_per_10s")
    idx = open(f"{P}/hf/index.html").read(); caps = len(re.findall(r'class="clip cap ', idx))
    if caps < len(W) / 3.5 and S.get("captions", {}).get("always_on", True): fails.append(f"only {caps} caption chunks for {len(W)} words (style: ~1 chunk per 2 words, captions on almost all the time)")
    print(f"style '{S.get('name')}'\n{'metric':28} {'this reel':>12} {'style':>12}")
    for k, v, r in [("duration s", f"{D:.1f}", f"{pace['duration'][0]}–{pace['duration'][1]}"), ("words per second", f"{wps:.2f}", pace["wps"]),
                    ("pause p90 s", f"{gaps[int(len(gaps) * .9)]:.2f}" if gaps else "-", pace["gap_p90"]),
                    ("first visual change s", f"{first_change:.2f}", pace["first_change"]["median"]), ("layout run median s", f"{st.median(r[1] for r in runs):.2f}", pace["layout_run_median"]),
                    ("split share", f"{share['split']:.2f}", L["split"]["median"]), ("graphic share", f"{share['graphic']:.2f}", L["graphic"]["median"]), ("face share", f"{share['face']:.2f}", L["face"]["median"]),
                    ("caption chunks", caps, "~words/2"), ("SFX per 10 s", f"{dens:.1f}", "bold 8–12" if bold else f"{ref_sfx['lo']}–{ref_sfx['hi']}"),
                    ("loudness LUFS", I, snd["lufs"]), ("true peak dBTP", tp, snd["true_peak"])]:
        print(f"{k:28} {str(v):>12} {str(r):>12}")
    os.makedirs(f"{P}/out", exist_ok=True)
    rows = int(D) // 9 + 1
    sh("ffmpeg", "-v", "error", "-y", "-i", video, "-vf", f"fps=1,scale=180:-1,tile=9x{rows}", "-frames:v", "1", "-q:v", "4", f"{P}/out/qa_sheet.jpg")
    for f in fails: print("FAIL", f)
    for w in warns: print("warn", w)
    print("sheet →", f"{P}/out/qa_sheet.jpg (look at it: every beat readable at thumbnail size, no empty frames, captions never over the eyes)")
    return 1 if fails else 0


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"): raise SystemExit(__doc__)
    P = os.path.abspath(sys.argv[1])
    v = sys.argv[2] if len(sys.argv) > 2 else max((os.path.join(P, "out", f) for f in os.listdir(f"{P}/out") if f.endswith(".mp4") and "light" not in f and f != "picture.mp4"), key=os.path.getmtime)
    sys.exit(main(P, v))
