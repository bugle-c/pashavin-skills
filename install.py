#!/usr/bin/env python3
"""Install reviewed public skills without changing client configuration."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
import uuid

REMOTE = "https://github.com/bugle-c/pashavin-skills.git"
CLIENTS = {"claude": ".claude/skills", "codex": ".codex/skills", "gemini": ".gemini/skills"}
NAME = re.compile(r"[a-z0-9][a-z0-9-]*\Z")


def git(*args):
    return subprocess.run(["git", *map(str, args)], check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".state-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_json(path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def inventory(path):
    if path.is_symlink() or not path.is_dir():
        raise ValueError(f"Not a regular directory: {path}")
    result = {}
    for root, directories, files in os.walk(path, followlinks=False):
        for name in directories + files:
            item = Path(root) / name
            if item.is_symlink():
                raise ValueError(f"Symlink is not allowed: {item}")
        for name in files:
            item = Path(root) / name
            if not item.is_file():
                raise ValueError(f"Not a regular file: {item}")
            result[item.relative_to(path).as_posix()] = hashlib.sha256(item.read_bytes()).hexdigest()
    return result


def validate_files(files):
    if not isinstance(files, dict) or "SKILL.md" not in files:
        raise ValueError("Skill inventory must contain SKILL.md")
    for name, digest in files.items():
        parts = PurePosixPath(name)
        if (not isinstance(name, str) or not name or parts.is_absolute()
                or ".." in parts.parts or "\\" in name or str(parts) != name
                or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)):
            raise ValueError(f"Invalid manifest entry: {name!r}")


def manifest(checkout):
    data = load_json(checkout / "manifest.json")
    if data.get("schema_version") != 1 or not isinstance(data.get("skills"), dict):
        raise ValueError("Unsupported manifest schema")
    for name, entry in data["skills"].items():
        if not NAME.fullmatch(name):
            raise ValueError(f"Invalid skill name: {name}")
        validate_files(entry["files"])
        if inventory(checkout / "skills" / name) != entry["files"]:
            raise ValueError(f"Integrity validation failed: {name}")
    return data["skills"]


def safe_directory(path):
    # Never follow a redirected client/state directory, even through an ancestor.
    for ancestor in [path, *path.parents]:
        if ancestor.is_symlink():
            raise ValueError(f"Refusing symlink directory: {ancestor}")
    if path.exists() and not path.is_dir():
        raise ValueError(f"Not a directory: {path}")


def checkout_repository(path, update, validate=True):
    safe_directory(path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix="checkout-", dir=path.parent))
        try:
            git("clone", "--origin", "origin", "--", REMOTE, temporary)
            if validate:
                manifest(temporary)
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)
    else:
        if not (path / ".git").is_dir() or (path / ".git").is_symlink():
            raise ValueError(f"Not a managed Git checkout: {path}")
        if git("-C", path, "rev-parse", "--show-toplevel") != str(path.resolve()):
            raise ValueError("Unexpected checkout root")
        urls = git("-C", path, "remote", "get-url", "--all", "origin").splitlines()
        if urls != [REMOTE]:
            raise ValueError("Checkout origin is not the trusted public repository")
        if git("-C", path, "status", "--porcelain", "--untracked-files=all"):
            raise ValueError("Managed checkout has local edits; preserve them before updating")
        if update:
            git("-C", path, "fetch", "--prune", "origin")
            branch = git("-C", path, "symbolic-ref", "refs/remotes/origin/HEAD")
            git("-C", path, "merge-base", "--is-ancestor", "HEAD", branch)
            if not branch.startswith("refs/remotes/origin/"):
                raise ValueError("Unexpected remote default branch")
            git("-C", path, "merge", "--ff-only", branch)
    return manifest(path) if validate else None


def matches(path, files):
    try:
        return inventory(path) == files
    except (ValueError, OSError):
        return False


def recover(state_path, state):
    pending = state.get("pending")
    if not pending:
        return
    target = Path(pending["target"])
    backup = Path(pending["backup"])
    staged = Path(pending["staged"]) if pending.get("staged") else None
    old, new = pending["old"], pending["new"]
    if old is not None:
        validate_files(old)
    if new is not None:
        validate_files(new)
    if staged is not None and staged.exists() and not matches(staged, new):
        raise ValueError(f"Interrupted stage failed integrity validation: {staged}")
    if backup.exists() and (old is None or not matches(backup, old)):
        raise ValueError(f"Interrupted backup has local changes: {backup}")
    if target.exists() or target.is_symlink():
        if new is not None and matches(target, new):
            pass
        elif old is not None and matches(target, old) and not backup.exists():
            if new is not None and (staged is None or not staged.exists()):
                raise ValueError("Interrupted installation lacks staged files; old copy preserved")
            target.rename(backup)
            if staged is not None:
                staged.rename(target)
        else:
            raise ValueError(f"Interrupted operation conflicts with local content: {target}")
    elif staged is not None and staged.exists():
        staged.rename(target)
    elif new is not None:
        if backup.exists() and matches(backup, old):
            backup.rename(target)
        raise ValueError("Interrupted installation lacks staged files; restored old copy where available")
    if new is None:
        state["skills"].pop(pending["name"], None)
    else:
        state["skills"][pending["name"]] = new
    state.pop("pending")
    atomic_json(state_path, state)
    if backup.exists():
        if old is None or not matches(backup, old):
            raise ValueError(f"Preserved unexpected transaction backup: {backup}")
        shutil.rmtree(backup)
    if staged is not None and staged.exists():
        shutil.rmtree(staged)


def change(state_path, state, root, name, old, new, source):
    stage = Path(tempfile.mkdtemp(prefix=".pashavin-stage-", dir=root)) if new is not None else None
    if stage is not None:
        try:
            shutil.copytree(source, stage, dirs_exist_ok=True)
            if inventory(stage) != new:
                raise ValueError(f"Staged integrity failure: {name}")
        except BaseException:
            shutil.rmtree(stage)
            raise
    backup = root / (".pashavin-backup-" + uuid.uuid4().hex)
    state["pending"] = {"name": name, "target": str(root / name), "backup": str(backup),
                        "staged": str(stage) if stage else None, "old": old, "new": new}
    atomic_json(state_path, state)
    recover(state_path, state)


def sync_client(base, home, client, skills, checkout, remove=False, status=False):
    root = home / CLIENTS[client]
    safe_directory(root)
    state_path = base / (client + ".json")
    state = load_json(state_path) if state_path.exists() else {"version": 1, "root": str(root), "skills": {}}
    if state.get("version") != 1 or state.get("root") != str(root):
        raise ValueError(f"Unexpected state for {client}")
    for name, files in state["skills"].items():
        if not NAME.fullmatch(name):
            raise ValueError("Invalid state skill name")
        validate_files(files)
    if state.get("pending"):
        pending = state["pending"]
        if (pending["name"] not in state["skills"] and pending["old"] is not None
                or Path(pending["target"]) != root / pending["name"]
                or not NAME.fullmatch(pending["name"])
                or Path(pending["backup"]).parent != root
                or not Path(pending["backup"]).name.startswith(".pashavin-backup-")
                or pending.get("staged") and (Path(pending["staged"]).parent != root
                    or not Path(pending["staged"]).name.startswith(".pashavin-stage-"))):
            raise ValueError("Invalid pending transaction")
        if status:
            print(f"{client}: interrupted transaction; run install/update/remove to recover")
            return 1
        recover(state_path, state)
    conflicts = 0
    desired = {} if remove else skills
    for name in sorted(set(desired) | set(state["skills"])):
        target = root / name
        old = state["skills"].get(name)
        new = desired.get(name, {}).get("files")
        exists = target.exists() or target.is_symlink()
        if exists and (old is None or not matches(target, old)):
            print(f"CONFLICT {client}/{name}: preserving unmanaged or locally edited content")
            conflicts += 1
            continue
        if status:
            print(f"{client}/{name}: {'installed' if exists else 'missing'}")
            continue
        if old == new and exists:
            continue
        if not exists and new is None:
            state["skills"].pop(name, None)
            atomic_json(state_path, state)
            continue
        root.mkdir(parents=True, exist_ok=True)
        change(state_path, state, root, name, old if exists else None, new,
               checkout / "skills" / name if new is not None else None)
        print(f"{client}/{name}: {'removed' if new is None else 'installed'}")
    return conflicts


@contextlib.contextmanager
def lock(base):
    safe_directory(base)
    base.mkdir(parents=True, exist_ok=True)
    path = base / "install.lock"
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError(f"Installer already running, or interrupted: {path}. If no installer is running, remove this lock and retry.")
    try:
        os.write(descriptor, str(os.getpid()).encode())
        os.close(descriptor)
        yield
    finally:
        path.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["install", "update", "status", "remove"])
    parser.add_argument("--client", action="append", choices=sorted(CLIENTS), help="Repeat to select multiple clients; otherwise detect existing client directories")
    args = parser.parse_args(argv)
    home = Path.home().absolute()
    base = home / ".local" / "share" / "pashavin-skills"
    clients = args.client or [name for name in CLIENTS if (home / ("." + name)).is_dir()]
    if not clients:
        parser.error("No clients detected. Choose --client claude, --client codex, or --client gemini.")
    checkout = base / "repository"
    running_code = Path(__file__).read_bytes()
    handoff = False
    try:
        with lock(base):
            if args.command in ("remove", "status"):
                skills = {}
            else:
                checkout_repository(checkout, args.command == "update", validate=False)
                handoff = (checkout / "install.py").read_bytes() != running_code
                skills = None if handoff else manifest(checkout)
            if not handoff:
                conflicts = sum(sync_client(base, home, client, skills, checkout,
                                           remove=args.command == "remove", status=args.command == "status")
                                for client in dict.fromkeys(clients))
        if handoff:
            # Release the lock before invoking the newly fetched implementation.
            # The install command uses the already updated checkout, without a fetch loop.
            command = [sys.executable, str(checkout / "install.py"), "install"]
            for client in dict.fromkeys(clients):
                command.extend(["--client", client])
            try:
                subprocess.run(command, check=True)
                return 0
            except subprocess.CalledProcessError as error:
                return error.returncode
        return 2 if conflicts else 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr.strip(), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
