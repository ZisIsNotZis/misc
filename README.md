<p align="center"><img src="assets/logo.svg" alt="misc" width="200" height="40"></p>

**English** | [简体中文](README.zh-CN.md)

# misc

A flat drawer of one-off scripts, notebooks and notes — the techniques tried while
answering concrete engineering questions, kept verbatim.

**Eighty-odd standalone files that each solve one narrow problem — a from-scratch
ANSI terminal, an asyncio HTTP server, industrial-vision config munging, llama.cpp
build recipes — published because the same problems keep coming back and the
answer is usually already in here.**

> **Status: archive.** This is a working junk drawer, not a library and not a
> project: no package, no manifest, no shared entry point, no tests. Contents span
> roughly 2020–2026 and are not maintained. Read it, copy from it, don't depend on it.

## Quick start

Only one file is dependency-free, self-contained and runnable as-is — the
single-file virtual terminal:

```bash
git clone https://github.com/ZisIsNotZis/misc.git
cd misc
python3 term.py      # spawns a shell on a pty and renders it itself; Ctrl-D / exit to leave
```

Everything else is context-dependent: most scripts expect data laid out next to
them, local services, or a specific toolchain (see [Requirements](#requirements)).
Read a script's header before running it — several reference absolute paths or
hosts from the machine they were written on.

## What's inside

**Terminal and systems** — `term.py` is a ~685-line VT/ANSI emulator: it opens a
pty, parses SGR/OSC and key sequences, keeps a screen buffer and repaints with
diffed JSON updates, stdlib only. `pow` pins CPU cores online and caps their
frequency; `kil` stops the usual laptop daemons; `nic.py` prints per-interface
counters from `/proc/net/dev`; `remove_r.py` filters carriage-return progress
output with `readv`/`writev`; `mycdll.py`, `util.py`, `mymisc.py` wrap `ctypes`
signatures from annotations.

**Servers and wire protocols** — `mysvr.py` is a small asyncio HTTP server
(routing, ranges, tar streaming); `myminio.py` / `myminios.py` are an object-store
client and an S3-compatible shim on top of it; `mreq.py` implements request/response
RPC over MQTT topics (`gmqtt` + `uvloop`), with `mreqtest.py` as its driver;
`fromtobytes.py` moves byte blobs through FastAPI; `mdview.htm` renders Markdown
in the browser.

**Async plumbing** — `cb.py`, `cb2.py`, `sub.py`, `val3.py`, `futs.py`,
`myasync.py`, `connectcoro.py` can be read as a progression of attempts to wire
callbacks, subscriptions and cancellation on plain `asyncio` futures without
pulling in a framework.

**Numerics and types** — `lns.py` is a log-number-system tensor type (log-magnitude
+ signbit) for arithmetic over huge dynamic range; `qkvfft.py` does sliding-window
attention as FFT convolutions; `cast.py` runtime-casts through `Union` /
`TypedDict` / dataclass annotations; `mutuple.py` is a mutable tuple; `npjson.py`
round-trips numpy structured arrays through JSON; `vec.py` is a memmap-backed
`ndarray`; `selfcallable.py` and `stub.py` are typing toys.

**Industrial vision** — `featbox2xywcfg.py` and `imgcls2featbox.py` (10–12 KB each)
convert between feature-box, image-class and `x/y/w/cfg` task configs;
`roi2.py`, `roi2cfg.py`, `fix2cfg.py` drive region work off YAML + cv2 (and
commercial MVTec **halcon** for `roi2.py`); `dinoseg*.py` run DINOv3 embeddings for
segmentation; `featmap2seg.py`, `feat2cls.py`, `img2cls.py`, `img2clsall.sh` are
the labelling pipeline that feeds them.

**LLM infrastructure** — `mk.sh` builds llama.cpp across compilers and backends
with tuned flags; `ggmlmk.txt` records an earlier build; `analyze.py` and
`graphics.md` turn `llama-bench` CSV output into GPU/quant throughput tables;
`beam.py` runs beam search against a local `llama-server`; `trtllm.sh` is a
TensorRT-LLM serving profile; `k3s.sh` bootstraps a k3s node; `dl.sh` pulls the
model set; `ds2txt.py` and `jsonl2txt.py` render chat-format datasets to text.

**Shell chores** — `apt.sh`, `99clean`, `sources.list`, `pip.sh`, `clean.re`,
`gitclean`, `bashsqhist.sh` (sqlite-backed shell history with frecency),
`htmlconv.sh`, `duext.py`, `greprate.py`.

**Notebooks** — eight short handwritten experiments, no datasets required:
`quant` (post-training quantisation), `packmask` / `packmask2` (bit-packed masks),
`aps` (alternating projections), `minla` (minimum linear arrangement on PCA
embeddings), `fitsin` (SwiGLU capacity), `thres` (thresholding), `continuousatn`
(continuous attention).

**Notes** — `graphics.md` (GPU spec/throughput table), `sandbox.md` (isolation
options, unsandboxed → full virtualisation), `train.md` (Chinese: speeding up
training, cutting VRAM), `v4lqsvrtsp.txt` (v4l2 / QuickSync / RTSP), `road.drawio`.

## Architecture

There isn't one — deliberately. The repository is flat: every file is an island
with its own imports, and no file is imported by more than a couple of neighbours.
The few real edges are these:

```
mysvr.py ──► myminio.py        object store rides on the asyncio HTTP server
   │
   └──────► myminios.py        S3-compatible shim (aiohttp client side)

mreq.py ◄──► mreqtest.py       MQTT request/response RPC, driven by the test
term.py                        self-contained: pty + VT parser + renderer

dinoseg*.py ──► featmap2seg.py ──► featbox2xywcfg.py ──► roi2.py
   (embeddings)     (decode)         (config mapping)     (halcon regions)
```

Shared helpers (`feat.py` — moment invariants such as area, aspect, covariance and
eccentricity computed straight from a mask; `util.py`, `cast.py`, `futs.py`) are
copy-paste progenitors rather than libraries: later files inline the better version.
Rename or move anything you like in your own copy; nothing here has an API to break.

## Requirements

No manifest exists; dependencies are inferred from imports:

```
numpy torch torchvision opencv-python matplotlib scikit-learn PyYAML Pillow
pyarrow orjson requests aiohttp pydantic fastapi uvloop pulp miniopy_async gmqtt
```

`roi2.py` additionally needs MVTec **halcon**, which is commercial and
license-gated. Python 3.12+ is required for the files using PEP 695 generics
(`cb.py`, `sub.py`, `mutuple.py`, `cast.py`, …); `term.py` and the shell scripts
need nothing beyond a stock Python 3 and `/bin/sh`.

## Working on it

There is no build, no test suite, no linter config and no lockfile. The checks that
exist are the ones you run by hand:

```bash
python3 -m py_compile some_script.py   # syntax check a single file
python3 term.py                        # the one end-to-end smoke test
bash -n mk.sh                          # shell scripts, likewise
```

Editing rules for this repository: keep it flat, keep each file self-contained, and
never commit a credential (see below). Notes belong in the file's header docstring
or in one of the `.md` notes, not in a new document.

## Publication hygiene

This directory was migrated out of a private archive; credential-bearing files were
removed and inline secrets redacted before publication:

- `lm.yml` / `lm.json` — multi-provider API-key stores (~24 providers) — deleted.
- `github-recovery-codes.txt` — GitHub 2FA recovery codes — deleted.
- `p.txt` — an unrestricted "no refusals" LLM prompt — deleted.
- `chengzhi.sh` — real usernames, jump host and non-standard ports — redacted.
- `trtllm.sh` — a real host IP — redacted.

Every credential that was ever in this tree should be treated as compromised and
rotated. `.gitignore` blocks `.env*`, `*.pem`, `*.key`, `lm.yml`/`lm.json` and
recovery-code files so they cannot come back by accident.

## Roadmap

**Implemented** — everything described under [What's inside](#whats-inside): the
terminal, the asyncio server family, the MQTT RPC, the LNS/FFT numeric sketches, the
vision config pipeline, the llama.cpp build and bench harness, the shell chores, the
eight notebooks and the notes.

**Planned** — nothing. This is an archive: no new features, no fixes, no dependency
updates. Known-deprecated pieces are kept on purpose as a record of their era:
`sources.list` pins Ubuntu focal (20.04, EOL May 2025), `train.md` targets
`THUDM/chatglm2-6b` with a 2023-era fine-tuning CLI, and `ggmlmk.txt` records a 2024
llama.cpp build whose flags have since changed.

If this drawer is ever to become more than an archive, the honest path is not to
grow it: lift one thread out into its own repository — `term.py` and the
`mysvr`/`myminio`/`mreq` family are the two closest to being useful standalone
tools — give it tests and a licence-appropriate home, and leave the rest as
reference.

## Contributing

The repository is not maintained and pull requests against it are not expected — see
[CONTRIBUTING.md](CONTRIBUTING.md) for what is and isn't useful to send.

## License

[GNU Affero General Public License v3.0 only](LICENSE) (AGPL-3.0-only),
© ZisIsNotZis.

The licence covers the code in this repository. Third-party code, models, build
recipes and notes referenced by these scripts keep their own licences; MVTec halcon
is commercial and never vendored here.
