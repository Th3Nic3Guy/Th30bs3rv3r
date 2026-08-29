# python

The FREE WILL tensor-native simulation engine. See `../docs/FREE_WILL_PRD.md` for the
full design and `../docs/adr/0001-gcp-tech-stack.md` for the GCP stack this targets.

## Layout

- `freewill/engine` — state tensors (`state.py`) and the tick loop (`tick_loop.py`),
  PRD Section 4.1–4.2.
- `freewill/mechanisms` — one module per FREE_WILL_draft.md section, PRD Section 4.3.
  Every function here is currently a stub raising `NotImplementedError`: per PRD Section
  2.3, no formula is implemented without a specific draft-section reference, and
  FREE_WILL_draft.md is not yet part of this repo.
- `freewill/config` — the run-time parameter schema (`RunConfig`), PRD Section 5/11.
- `freewill/storage` — Cloud Storage checkpoint store, event-log buffer, Cloud SQL run
  registry client, Redis config cache — PRD Section 6.
- `freewill/validation` — the slow per-agent iterative reference oracle, PRD Section 4.4.
- `freewill/metrics` — run-summary metric computation, PRD Section 4.7/6.4.

## Setup

```sh
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,ui]"
```

## Test

```sh
pytest
```

Cross-validation tests (PRD Section 4.4) are skipped until the mechanism modules are
implemented against FREE_WILL_draft.md — see `tests/test_cross_validation.py`.
