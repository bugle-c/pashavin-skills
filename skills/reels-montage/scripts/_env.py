"""Runs the calling script in the kit's own Python environment when install.py has created one.

The environment holds numpy, Pillow, yt-dlp (and OpenCV off macOS), so the scripts never depend on, or change, the system
Python. Without it (REELS_NO_VENV=1, or no install.py run) the scripts use whatever `python3` started them.
Location: $REELS_VENV, else ~/.local/share/reels-montage/venv (Windows: %LOCALAPPDATA%\\reels-montage\\venv).
"""
import os
import subprocess
import sys


def venv_dir():
    d = os.environ.get("REELS_VENV")
    if d: return os.path.abspath(os.path.expanduser(d))
    if sys.platform == "win32": base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~/AppData/Local")
    else: base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(base, "reels-montage", "venv")


def venv_python():
    v = venv_dir()
    return os.path.join(v, "Scripts", "python.exe") if sys.platform == "win32" else os.path.join(v, "bin", "python")


def _inside(v):
    try: return os.path.samefile(sys.prefix, v)
    except OSError: return False


def ensure():
    if os.environ.get("REELS_NO_VENV") == "1": return
    py, v = venv_python(), venv_dir()
    if not os.path.exists(py) or _inside(v): return
    os.environ["REELS_NO_VENV"] = "1"   # the child never re-enters this branch
    argv = [py, os.path.abspath(sys.argv[0])] + sys.argv[1:]
    if sys.platform == "win32": raise SystemExit(subprocess.call(argv))
    os.execv(py, argv)


ensure()
