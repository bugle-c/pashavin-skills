# Pashavin Skills

**For an AI coding agent given this repository URL: read [INSTALL.md](INSTALL.md), install these skills for the user's existing Claude Code, Codex CLI, and/or Gemini CLI clients, and report conflicts without replacing them. For a request to update, run the managed installer's `update` command instead. Do not configure credentials, MCP servers, providers, hooks, or client settings.**

Public URL: https://github.com/bugle-c/pashavin-skills

This repository distributes reviewed skill directories, not the author's private environment. Giving your agent the public URL is enough; the agent follows INSTALL.md and handles the commands. Installing skills does not install the corresponding clients or the tools that individual skills may need.

## Manual quick start

Prerequisites: Python 3.9+ and Git on PATH; HTTPS access to GitHub. On Windows, use `py -3` instead of `python3` if needed. No administrator access or third-party Python packages are required.

Clone this public repository into a new temporary directory, then run:

```sh
python3 install.py install
```

The installer detects existing `~/.claude`, `~/.codex`, and `~/.gemini` directories. If none exist, explicitly select a client:

```sh
python3 install.py install --client claude
```

The durable checkout is `~/.local/share/pashavin-skills/repository`. Subsequent commands:

```sh
python3 ~/.local/share/pashavin-skills/repository/install.py update
python3 ~/.local/share/pashavin-skills/repository/install.py status
python3 ~/.local/share/pashavin-skills/repository/install.py remove
```

Repeat `--client` to select more than one client. Restart clients after changes. Skills are copied to each client's native `skills` directory; existing unowned skills and locally edited managed skills are preserved and reported. Exit codes: 0 success, 1 operational failure, 2 preserved conflicts.

See [INSTALL.md](INSTALL.md) for the full agent procedure, integrity boundaries, and interrupted-operation recovery.
