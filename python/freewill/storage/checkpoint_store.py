"""Checkpoint storage on Cloud Storage (PRD Section 6.2).

One archive per checkpoint: a compressed `.npz` for the scipy-sparse/dense numpy pieces
(belief matrix B, trust tensor T or its per-proposition dict fallback, grid positions),
bundled with a sibling `.parquet` for the per-agent coefficient table. Explicitly not one
file per agent (PRD 6.2) — at population/checkpoint/run-count scale that would produce
tens of millions of small objects.

Object layout: gs://{bucket}/{run_id}/tick_{tick:06d}.npz (+ .parquet)
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from google.cloud import storage


@dataclass
class CheckpointRef:
    run_id: str
    tick: int
    npz_uri: str
    parquet_uri: str


class CheckpointStore:
    """Writes/reads checkpoint archives to/from a Cloud Storage bucket.

    Callers are the simulation engine (write, every `checkpoint_interval_ticks` ticks and
    at run start/end, PRD 4.2 step 7) and the visualization UI's post-hoc replay path
    (read, PRD Section 8.1).
    """

    def __init__(self, bucket_name: str, client: storage.Client | None = None) -> None:
        self._client = client or storage.Client()
        self._bucket = self._client.bucket(bucket_name)

    def _npz_blob_name(self, run_id: str, tick: int) -> str:
        return f"{run_id}/tick_{tick:06d}.npz"

    def _parquet_blob_name(self, run_id: str, tick: int) -> str:
        return f"{run_id}/tick_{tick:06d}.parquet"

    def write_checkpoint(
        self,
        run_id: str,
        tick: int,
        *,
        arrays: dict[str, Any],
        coefficient_table: pd.DataFrame,
    ) -> CheckpointRef:
        """Write one checkpoint.

        `arrays` holds the sparse/dense tensor pieces (B, T, grid positions, ...) as
        whatever `numpy.savez_compressed`-compatible objects the engine's serialization
        layer produces (e.g. scipy.sparse matrices converted to COO component arrays).
        `coefficient_table` is the per-agent coefficient table (PRD 4.1), agents x 9.
        """
        npz_buf = io.BytesIO()
        np.savez_compressed(npz_buf, **arrays)
        npz_buf.seek(0)
        npz_name = self._npz_blob_name(run_id, tick)
        self._bucket.blob(npz_name).upload_from_file(npz_buf, content_type="application/octet-stream")

        parquet_buf = io.BytesIO()
        coefficient_table.to_parquet(parquet_buf, index=False)
        parquet_buf.seek(0)
        parquet_name = self._parquet_blob_name(run_id, tick)
        self._bucket.blob(parquet_name).upload_from_file(parquet_buf, content_type="application/octet-stream")

        return CheckpointRef(
            run_id=run_id,
            tick=tick,
            npz_uri=f"gs://{self._bucket.name}/{npz_name}",
            parquet_uri=f"gs://{self._bucket.name}/{parquet_name}",
        )

    def read_checkpoint(self, run_id: str, tick: int) -> tuple[dict[str, Any], pd.DataFrame]:
        """Read one checkpoint back for replay (PRD Section 8.1/8.4)."""
        npz_bytes = self._bucket.blob(self._npz_blob_name(run_id, tick)).download_as_bytes()
        arrays = dict(np.load(io.BytesIO(npz_bytes), allow_pickle=False))

        parquet_bytes = self._bucket.blob(self._parquet_blob_name(run_id, tick)).download_as_bytes()
        coefficient_table = pd.read_parquet(io.BytesIO(parquet_bytes))

        return arrays, coefficient_table
