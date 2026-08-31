// Package cloudsql is the Go-side Cloud SQL (PostgreSQL) client for the run registry
// (PRD Section 6.4). It mirrors python/freewill/storage/run_registry.py's role — the Go
// orchestrator (cmd/orchestrator) uses this to create a run's row before provisioning
// its Compute Engine instance, and to mark the run's terminal status if the instance
// dies without writing its own summary (PRD Section 9).
//
// See infra/sql/schema.sql for the `runs` / `run_summaries` / `checkpoints` DDL this
// package reads and writes.
//
// Local development (docker-compose.yml): Cloud SQL has no official local emulator
// (unlike Cloud Storage, which internal/gcs just points at fake-gcs-server via
// STORAGE_EMULATOR_HOST with no code changes). OpenLocal bypasses cloudsqlconn entirely
// and talks to a plain Postgres instance over a standard DSN; every method on
// *RunRegistry works identically either way since they only ever touch r.db.
package cloudsql

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"

	"cloud.google.com/go/cloudsqlconn"
	"cloud.google.com/go/cloudsqlconn/postgres/pgxv5"
	_ "github.com/jackc/pgx/v5/stdlib" // registers the "pgx" database/sql driver, used by OpenLocal
)

const driverName = "cloudsql-postgres"

// RunRegistry is a connection to the `runs` registry, dialed through the Cloud SQL Auth
// Proxy connector (cloudsqlconn) so callers never handle IP allowlisting or SSL certs.
type RunRegistry struct {
	db      *sql.DB
	cleanup func() error
}

// Config identifies the Cloud SQL instance and database to connect to.
// InstanceConnectionName is "PROJECT:REGION:INSTANCE", matching Terraform's
// google_sql_database_instance.connection_name output (infra/terraform/cloudsql.tf).
type Config struct {
	InstanceConnectionName string
	DBName                 string
	DBUser                 string
	// UseIAMAuthN selects IAM database authentication over a static password.
	// Preferred in production; the orchestrator's service account (infra/terraform/iam.tf)
	// is granted the cloudsql.instanceUser role for this.
	UseIAMAuthN bool
}

// Open connects to the run registry.
func Open(ctx context.Context, cfg Config) (*RunRegistry, error) {
	var opts []cloudsqlconn.Option
	if cfg.UseIAMAuthN {
		opts = append(opts, cloudsqlconn.WithIAMAuthN())
	}

	cleanup, err := pgxv5.RegisterDriver(driverName, opts...)
	if err != nil {
		return nil, fmt.Errorf("cloudsql: registering driver: %w", err)
	}

	dsn := fmt.Sprintf("host=%s user=%s dbname=%s sslmode=disable",
		cfg.InstanceConnectionName, cfg.DBUser, cfg.DBName)
	db, err := sql.Open(driverName, dsn)
	if err != nil {
		_ = cleanup()
		return nil, fmt.Errorf("cloudsql: opening db: %w", err)
	}

	if err := db.PingContext(ctx); err != nil {
		_ = db.Close()
		_ = cleanup()
		return nil, fmt.Errorf("cloudsql: ping: %w", err)
	}

	return &RunRegistry{db: db, cleanup: cleanup}, nil
}

// OpenLocal connects straight to a plain Postgres instance (docker-compose's `postgres`
// service) instead of dialing Cloud SQL. `dsn` is a standard libpq keyword/value or URI
// connection string, e.g. "host=postgres user=freewill password=freewill dbname=freewill
// sslmode=disable".
func OpenLocal(ctx context.Context, dsn string) (*RunRegistry, error) {
	db, err := sql.Open("pgx", dsn)
	if err != nil {
		return nil, fmt.Errorf("cloudsql: opening local db: %w", err)
	}
	if err := db.PingContext(ctx); err != nil {
		_ = db.Close()
		return nil, fmt.Errorf("cloudsql: ping local db: %w", err)
	}
	return &RunRegistry{db: db, cleanup: func() error { return nil }}, nil
}

// CreateRun inserts a new `runs` row in "pending" status.
func (r *RunRegistry) CreateRun(ctx context.Context, runID, domain string, seed int64, config any) error {
	configJSON, err := json.Marshal(config)
	if err != nil {
		return fmt.Errorf("cloudsql: marshaling config: %w", err)
	}
	_, err = r.db.ExecContext(ctx, `
		INSERT INTO runs (run_id, domain, seed, config, status, started_at)
		VALUES ($1, $2, $3, $4, 'pending', now())`,
		runID, domain, seed, configJSON)
	if err != nil {
		return fmt.Errorf("cloudsql: creating run %q: %w", runID, err)
	}
	return nil
}

// MarkRunStatus updates a run's status and, on a terminal status, its ended_at
// timestamp. Used by the orchestrator both for normal lifecycle transitions
// ("provisioning" -> "running" -> "completed") and to mark a run "failed" when its
// instance disappears without writing a summary (PRD Section 9).
func (r *RunRegistry) MarkRunStatus(ctx context.Context, runID, status string, computeInstance string) error {
	_, err := r.db.ExecContext(ctx, `
		UPDATE runs
		SET status = $1,
		    compute_instance = COALESCE(NULLIF($2, ''), compute_instance),
		    ended_at = CASE WHEN $1 IN ('completed', 'failed') THEN now() ELSE ended_at END
		WHERE run_id = $3`,
		status, computeInstance, runID)
	if err != nil {
		return fmt.Errorf("cloudsql: marking run %q status %q: %w", runID, status, err)
	}
	return nil
}

// HasRunSummary reports whether run_summaries already has a row for runID — the
// orchestrator's check, on instance disappearance, for whether the engine finished
// writing its summary before dying (PRD Section 9).
func (r *RunRegistry) HasRunSummary(ctx context.Context, runID string) (bool, error) {
	var exists bool
	err := r.db.QueryRowContext(ctx,
		`SELECT EXISTS(SELECT 1 FROM run_summaries WHERE run_id = $1)`, runID,
	).Scan(&exists)
	if err != nil {
		return false, fmt.Errorf("cloudsql: checking run summary for %q: %w", runID, err)
	}
	return exists, nil
}

// GetRunConfig fetches a run's config document, e.g. for the orchestrator's Redis
// warm-cache step (PRD Section 5's "hot path").
func (r *RunRegistry) GetRunConfig(ctx context.Context, runID string) (json.RawMessage, error) {
	var config json.RawMessage
	err := r.db.QueryRowContext(ctx,
		`SELECT config FROM runs WHERE run_id = $1`, runID,
	).Scan(&config)
	if err != nil {
		return nil, fmt.Errorf("cloudsql: fetching config for %q: %w", runID, err)
	}
	return config, nil
}

// Close closes the underlying connection pool and the Cloud SQL dialer.
func (r *RunRegistry) Close() error {
	if err := r.db.Close(); err != nil {
		return err
	}
	return r.cleanup()
}
