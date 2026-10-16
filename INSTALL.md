# Agent installation and update procedure

When the user provides https://github.com/bugle-c/pashavin-skills, perform this procedure rather than asking the user to copy files or configure tools.

1. Read this file and `install.py` from the public repository. Check Python 3.9+ and Git availability. Do not install missing system software without the user's authorization. On Windows `py -3` can replace `python3`.
2. For a first installation, clone `https://github.com/bugle-c/pashavin-skills.git` into a fresh temporary directory using Git (never reuse an arbitrary existing directory). Run `python3 <temporary-directory>/install.py install`. The installer creates its own durable checkout; the bootstrap clone may then be removed. Do not pipe remote code into a shell.
3. Existing `~/.claude`, `~/.codex`, and `~/.gemini` directories determine the detected clients. Explicit `--client claude`, `--client codex`, or `--client gemini` overrides detection and may be repeated. If no client exists, ask which client the user wants; do not invent a client choice.
4. On update requests, run `python3 ~/.local/share/pashavin-skills/repository/install.py update` with the desired client options. Do not reclone over a checkout, reset Git, or delete dirty files to force an update.
5. Report the command's exit code and conflicts, and advise restarting client sessions. Do not claim individual skills' external integrations are configured or authenticated.

## Storage and boundaries

The installer owns `~/.local/share/pashavin-skills/`: `repository/` contains a public-only Git checkout; per-client JSON state records the exact file hashes previously installed; `install.lock` excludes concurrent operations. Native copies go to `~/.claude/skills`, `~/.codex/skills`, and `~/.gemini/skills`. Windows uses the corresponding home directory paths. No symlinks, administrator permissions, or Python packages are required. Redirected/symlinked destination ancestors are refused rather than guessed. Git must support HTTPS.

Only skill directories are installed. No environment variables, credential stores, MCP servers, providers, hooks, client configuration, or project repositories are modified. A skill may document extra tools or credentials; installing its text does not grant those capabilities. Treat instructions and bundled programs as code to review before executing them.

The checked-in manifest lists SHA-256 of the exact bytes of every regular file in every skill. Inventories must match exactly before installation and after staging. Symlinks and traversal paths are refused. Hashes detect corruption and drift, not malicious changes by a trusted repository maintainer. Trust is anchored in the public HTTPS repository, not a separate signed release.

When the trusted checkout supplies a changed installer, the running installer releases its lock and invokes the new implementation with `install` and the same selected clients before parsing the new skill manifest. This avoids using an old manifest parser after an installer/schema update; the child exit code is preserved.

Updates require an exact trusted origin URL, a clean isolated checkout, and a fast-forward history. Diverged commits, changed origins, and local checkout edits stop the update. Preserve such edits separately; do not use reset/clean as an automatic workaround. Existing unowned destination directories are never adopted, even if their files happen to match. Managed destinations update or disappear only if every file still matches the prior recorded inventory. Conflicts are left untouched; unrelated skills are never removed.

## Commands

```sh
python3 ~/.local/share/pashavin-skills/repository/install.py install
python3 ~/.local/share/pashavin-skills/repository/install.py update
python3 ~/.local/share/pashavin-skills/repository/install.py status
python3 ~/.local/share/pashavin-skills/repository/install.py remove --client codex
```

`install` uses the current managed checkout without fetching; `update` fetches the trusted remote and fast-forwards before synchronizing. `remove` deletes only unchanged owned skills, not the public checkout or unowned/local-edited copies. `status` reports tracked destinations and local drift without fetching. Detection is repeated each command; use explicit client options to target a previously selected client whose configuration directory was removed.

Exit codes: **0** successful/no conflicts; **1** invalid input, integrity failure, or operational failure; **2** one or more preserved destination conflicts. Publication is per-skill, not whole-install atomic: earlier completed skills remain installed after a later error. Rerunning is idempotent.

## Interrupted operations

State is written atomically, and each replacement stages a complete validated copy before recording a transaction and moving the old copy aside. Retry the same mutating command to recover a pending transaction; unknown content encountered during recovery stops rather than overwrites it. `status` reports pending recovery without modifying it.

After an abrupt process termination, `install.lock` may remain. Verify no installer is running before deleting **only that lock**, then retry. Hidden `.pashavin-stage-*` or `.pashavin-backup-*` directories can remain after a crash. Do not blindly delete them: a pending transaction may need them, or a backup may contain the only old copy. Completed-but-unreferenced leftovers may be inspected and removed manually after a successful retry. If recovery reports a local conflict or missing stage, preserve the reported content and state files for diagnosis rather than forcing replacement.
