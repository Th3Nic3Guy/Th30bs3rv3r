"""Cloud SQL (PostgreSQL) client for the run registry (PRD Section 6.4).

Owns the `runs`, `run_summaries`, and `checkpoints` tables (see infra/sql/schema.sql for
DDL). Connects via the Cloud SQL Python Connector so callers never handle IP allowlisting
or SSL certs directly — works the same from a Compute Engine instance (PRD 6.0) or a
developer's machine running the visualization UI (PRD Section 8.2).
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from typing import Any

import psycopg
from google.cloud.sql.connector import Connector


class RunRegistry:
    def __init__(
        self,
        instance_connection_name: str,
        db_name: str,
        db_user: str,
        db_password: str | None = None,
    ) -> None:
        """`instance_connection_name` is `PROJECT:REGION:INSTANCE`, matching Terraform's
        `google_sql_database_instance.connection_name` output (infra/terraform/cloudsql.tf).
        Prefer IAM database authentication (db_password=None) in production; a password is
        accepted for local development against a non-IAM user.
        """
        self._connector = Connector()
        self._instance_connection_name = instance_connection_name
        self._db_name = db_name
        self._db_user = db_user
        self._db_password = db_password

    @contextmanager
    def _connect(self) -> Iterator[psycopg.Connection]:
        conn = self._connector.connect(
            self._instance_connection_name,
            "psycopg",
            user=self._db_user,
            password=self._db_password,
            db=self._db_name,
            enable_iam_auth=self._db_password is None,
        )
        try:
            yield conn
        finally:
            conn.close()

    def create_run(self, run_id: str, domain: str, seed: int, config: dict[str, Any]) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO runs (run_id, domain, seed, config, status, started_at)
                VALUES (%s, %s, %s, %s, 'pending', now())
                """,
                (run_id, domain, seed, json.dumps(config)),
            )
            conn.commit()

    def mark_run_status(
        self, run_id: str, status: str, *, compute_instance: str | None = None
    ) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE runs
                SET status = %s,
                    compute_instance = COALESCE(%s, compute_instance),
                    ended_at = CASE WHEN %s IN ('completed', 'failed') THEN now() ELSE ended_at END
                WHERE run_id = %s
                """,
                (status, compute_instance, status, run_id),
            )
            conn.commit()

    def get_run_config(self, run_id: str) -> dict[str, Any]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT config FROM runs WHERE run_id = %s", (run_id,))
            row = cur.fetchone()
            if row is None:
                raise KeyError(f"unknown run_id: {run_id}")
            return row[0]

    def record_checkpoint(self, run_id: str, tick: int, gcs_uri: str) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO checkpoints (run_id, tick, gcs_uri, created_at)
                VALUES (%s, %s, %s, now())
                """,
                (run_id, tick, gcs_uri),
            )
            conn.commit()

    def write_run_summary(self, run_id: str, metrics: dict[str, Any]) -> None:
        """`metrics` matches PRD 4.7's set: saturation curves, stabilization times,
        polarization indices (bimodality + variance), cluster assignments, NMI/ARI."""
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO run_summaries (run_id, metrics, created_at)
                VALUES (%s, %s, now())
                ON CONFLICT (run_id) DO UPDATE SET metrics = EXCLUDED.metrics
                """,
                (run_id, json.dumps(metrics)),
            )
            conn.commit()

    def list_checkpoints(self, run_id: str) -> list[tuple[int, str, datetime]]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT tick, gcs_uri, created_at FROM checkpoints WHERE run_id = %s ORDER BY tick",
                (run_id,),
            )
            return list(cur.fetchall())

    def close(self) -> None:
        self._connector.close()
