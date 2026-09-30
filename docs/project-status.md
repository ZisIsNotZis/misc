# misc project status

## Classification

Personal scratch directory: a flat collection of ~85 one-off scripts, 8 short
notebooks, notes and config files. No package, no manifest, no shared entrypoint,
no library surface. Not a product; not a maintained tool.

## Status

Archive — kept for reference, not maintained. Content spans roughly 2020–2026;
last touched 2026-04. Known-deprecated pieces are retained deliberately:
`sources.list` pins Ubuntu focal (20.04, EOL May 2025), `train.md` targets a
2023-era `THUDM/chatglm2-6b` fine-tuning CLI, and `ggmlmk.txt` records a 2024
llama.cpp build whose flags have since changed. Sanitised for publication:
credential stores removed, inline secrets redacted (see below).

## Evidence

- `term.py` — 685-line from-scratch VT/ANSI terminal emulator, stdlib only;
  `python3 term.py` is the one reproducible entrypoint.
- `mysvr.py`, `myminio.py`, `myminios.py`, `cb.py` — from-scratch coroutine /
  socket / event-loop infrastructure rather than framework glue.
- `featbox2xywcfg.py`, `imgcls2featbox.py` — ~10–12 KB of non-trivial industrial
  vision pipeline logic; `dinoseg*.py`, `roi2.py` — DINO segmentation tooling.
- `mk.sh`, `ggmlmk.txt` — llama.cpp build + benchmark harness.
- 8 notebooks (`quant`, `packmask`, `packmask2`, `minla`, `aps`, `fitsin`,
  `thres`, `continuousatn`) are short in-place handwritten experiments on
  synthetic `torch.randn` / `numpy` tensors — no dataset or customer data.
- Sanitisation record: `lm.yml`, `lm.json`, `github-recovery-codes.txt`, `p.txt`
  deleted; `chengzhi.sh`, `down.py`, `trtllm.sh` redacted. Final credential/IP
  scan over the tree returns zero matches.

## Boundaries

No tests, no CI, no dependency manifest, no LICENSE. Scripts are
context-dependent and several reference absolute paths or local hosts, so most
will not run unmodified. `fitbox.py` is empty; `feat.py`, `nic.py`, `mymisc.py`
are trivial stubs. `roi2.py` depends on commercial MVTec **halcon** (license-gated).
`down.py` retains employer-internal asset/bucket naming from an industrial-vision
deployment even after its credentials were stripped — treat it as a governance
liability and drop it before any wider redistribution.

## Publication removals

- `down.py` was removed before publication: it carried employer-internal
  industrial-vision asset and bucket naming. Credentials in that file were
  redacted first; the file itself was dropped as employer-internal (AGENTS.md rule 3).
