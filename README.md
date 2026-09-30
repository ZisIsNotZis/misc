# misc

A flat personal scratch directory — ~85 one-off scripts, 8 small notebooks,
notes and config files accumulated while experimenting with ML vision pipelines,
llama.cpp builds, async network tooling, and terminal emulation.

Why it exists: this is a working junk drawer, not a project. Nothing here is a
coherent library or application; each file was written to answer a single question
or automate a single chore, then left in place. It is kept as a raw record of the
problems that were being worked on and the techniques used to attack them.

How to run: there is no build system, package manifest, or shared entrypoint. Each
script is standalone and expects its own environment. The one file with no
third-party dependencies is the virtual-terminal server:
`python3 term.py` (stdlib only; interactive).

**Status: archive — a working junk drawer, kept for reference; not maintained.**
Mixed-era personal experiments, last touched 2026-04. Several parts are
deliberately deprecated (2020/2024 era) and kept as an archive:

- `sources.list` pins Ubuntu focal (20.04, EOL May 2025).
- `train.md` targets `THUDM/chatglm2-6b` with a 2023-era fine-tuning CLI.
- `ggmlmk.txt` documents a 2024 llama.cpp build; flags have since changed.

This is not a product, not a maintained library, and not a template. Treat it as
a public reading copy of a private scratch drawer.

## Sanitisation before publication

This directory was migrated out of a private archive. Before publication, all
credential-bearing files were removed and inline secrets were redacted:

- `lm.yml` / `lm.json` — multi-provider API-key stores (~24 providers) — deleted.
- `github-recovery-codes.txt` — GitHub 2FA recovery codes — deleted.
- `p.txt` — an unrestricted "no refusals" LLM prompt — deleted.
- `chengzhi.sh` — real usernames, jump host and non-standard ports — redacted.
- `down.py` — MinIO endpoint and access/secret keys — redacted.
- `trtllm.sh` — a real host IP — redacted.

Every exposed credential should be treated as compromised and rotated. Do not
reintroduce real values into this repository.

## Dependency list (inferred from imports; no manifest exists)

numpy, torch, torchvision, opencv-python (cv2), matplotlib, scikit-learn, PyYAML,
Pillow, pyarrow, orjson, requests, aiohttp, pydantic, fastapi, uvloop, pulp,
miniopy_async, gmqtt, and MVTec **halcon** (commercial, license-gated) in `roi2.py`.

## Repro command

`python3 term.py` — the only dependency-free, single-file program (stdlib-only
virtual terminal server). All other files are context-dependent; no shared
reproducible command identified.

## License

No `LICENSE` file exists. Absent an explicit grant, default copyright applies —
do not redistribute this directory as public source. Any future public extraction
must be a hand-picked subset with a new license, not a copy of the directory.
