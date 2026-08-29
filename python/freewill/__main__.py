"""CLI entry point for the per-run Compute Engine instance (PRD Section 6.0).

Invoked by the Go orchestrator (go/cmd/orchestrator, PRD Section 9) as:

    python -m freewill --run-id <run_id>

Pulls the run's config from Redis (falling back to Cloud SQL, PRD Section 5), runs the
tick loop (freewill.engine.run_simulation), and writes the run summary (PRD Section 6.4)
on completion.
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="freewill")
    parser.add_argument("--run-id", required=True, help="run_id already registered in Cloud SQL")
    args = parser.parse_args(argv)

    # TODO: wire up freewill.storage.{run_registry,config_cache} to load the RunConfig
    # for args.run_id, initialize freewill.engine.SimulationState, and call
    # freewill.engine.run_simulation — pending the mechanism-module implementations
    # (PRD Section 2.3) this whole pipeline depends on.
    raise NotImplementedError(f"run pipeline not yet implemented (run_id={args.run_id!r})")


if __name__ == "__main__":
    sys.exit(main())
