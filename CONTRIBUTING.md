# Contributing

This repository is an archive of one-off scripts, not a maintained project. Read
[README.md](README.md) first: there is no build system, no test suite and no
shared API to keep stable, and nothing here is guaranteed to run on your machine.

## What is useful

- **A credential.** If you find a key, token, password, private host or internal
  name that survived the publication scrub, report it privately (GitHub security
  advisory, or email the maintainer) rather than opening an issue. The file will
  be removed and the value should be considered compromised.
- **A reproducible break** — a script that fails on a clean checkout in a way its
  own header does not warn about, with the command and traceback inline. Fixes are
  welcome for these; please keep them minimal and send them as a pull request.
- **A correction** — a README or note that states something the code contradicts.

## What is not useful

- New features, refactors, formatting sweeps, dependency bumps or "let's turn this
  into a package". The flat structure is the point; see the roadmap in
  [README.md](README.md#roadmap).
- Issues of the "does not work" kind without a command, an environment and a
  traceback. Most files expect data, services or toolchains that are not in the
  repository, and that is by design.

## Pull requests

- One change per pull request, Conventional Commit style in the title
  (`fix(term): handle ESC[3~`, `docs: correct the term.py line count`).
- Keep files flat and self-contained: a script must still run on its own, with its
  own imports and its own header docstring.
- Python 3.12+ syntax (PEP 695 generics) is in use across several files; do not
  downgrade a file's syntax just to widen compatibility.
- `python3 -m py_compile <file>` must pass for every Python file you touch,
  `bash -n <file>` for shell scripts, and `python3 term.py` must still start and
  exit cleanly if you touch the terminal.
- Never include real credentials, hostnames, usernames or internal asset names —
  placeholders (`<REDACTED:host>`) are the established convention in this tree.

## Issues

Open one when the report matches the "useful" list above and contains the command,
the environment and the full traceback. Response time is not promised; the
repository is maintained on a best-effort, when-it-bothers-me basis.
