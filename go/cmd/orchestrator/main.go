// Command orchestrator provisions and tears down the one Compute Engine instance per
// simulation run (PRD Section 9), across the ~3,960-run experiment budget (PRD Section
// 1). It is a fleet-provisioning tool, not a job scheduler inside one VM: each run gets
// its own instance for its full lifetime (PRD Section 6.0).
//
// Responsibilities (PRD Section 9):
//   - create the run's Cloud SQL row (internal/cloudsql)
//   - warm its config + static domain tensors into Redis (internal/rediscache) — the
//     "hot path" PRD Section 5 describes
//   - provision the run's Compute Engine instance from the prebuilt image
//     (internal/compute)
//   - wait for completion/failure and mark the run "failed" in Cloud SQL if the instance
//     disappears without a summary row
//   - tear the instance down
//
// This is a scaffold: RunOne below implements the sequencing described in PRD Section 9,
// but batch concurrency caps, preemption retry, and the actual completion-detection
// polling loop are left as TODOs for the M0.5 milestone (docs/FREE_WILL_PRD.md Section
// 10) to fill in against the project's real quota and image.
package main

import (
	"context"
	"flag"
	"log"
	"time"

	"github.com/th3nic3guy/th30bs3rv3r/go/internal/cloudsql"
	"github.com/th3nic3guy/th30bs3rv3r/go/internal/compute"
	"github.com/th3nic3guy/th30bs3rv3r/go/internal/rediscache"
)

type config struct {
	project          string
	zone             string
	cloudSQLInstance string
	cloudSQLDB       string
	cloudSQLUser     string
	redisAddr        string
	sourceImage      string
	network          string
	subnetwork       string
	serviceAccount   string
	machineType      string
	runID            string
	domain           string
	pollInterval     time.Duration
}

func main() {
	var cfg config
	flag.StringVar(&cfg.project, "project", "", "GCP project ID")
	flag.StringVar(&cfg.zone, "zone", "us-central1-a", "Compute Engine zone")
	flag.StringVar(&cfg.cloudSQLInstance, "cloudsql-instance", "", "Cloud SQL instance connection name (PROJECT:REGION:INSTANCE)")
	flag.StringVar(&cfg.cloudSQLDB, "cloudsql-db", "freewill", "Cloud SQL database name")
	flag.StringVar(&cfg.cloudSQLUser, "cloudsql-user", "freewill-orchestrator@PROJECT.iam", "Cloud SQL IAM database user — the orchestrator service account's email with the .gserviceaccount.com suffix trimmed (matches infra/terraform/cloudsql.tf's google_sql_user.orchestrator); must be overridden with the real project ID")
	flag.StringVar(&cfg.redisAddr, "redis-addr", "", "Memorystore Redis address (host:port)")
	flag.StringVar(&cfg.sourceImage, "source-image", "", "Compute Engine source image for the run instance")
	flag.StringVar(&cfg.network, "network", "default", "VPC network")
	flag.StringVar(&cfg.subnetwork, "subnetwork", "default", "VPC subnetwork")
	flag.StringVar(&cfg.serviceAccount, "service-account", "", "service account email for the run instance")
	flag.StringVar(&cfg.machineType, "machine-type", "n2-standard-4", "Compute Engine machine type")
	flag.StringVar(&cfg.runID, "run-id", "", "run_id to provision (single-run mode)")
	flag.StringVar(&cfg.domain, "domain", "", "axiom domain for this run")
	flag.DurationVar(&cfg.pollInterval, "poll-interval", 30*time.Second, "polling interval while waiting for run completion")
	flag.Parse()

	if cfg.runID == "" {
		log.Fatal("orchestrator: -run-id is required (batch mode over the experiment matrix is a TODO, PRD Section 9)")
	}

	ctx := context.Background()
	if err := runOne(ctx, cfg); err != nil {
		log.Fatalf("orchestrator: run %q failed: %v", cfg.runID, err)
	}
}

func runOne(ctx context.Context, cfg config) error {
	registry, err := cloudsql.Open(ctx, cloudsql.Config{
		InstanceConnectionName: cfg.cloudSQLInstance,
		DBName:                 cfg.cloudSQLDB,
		DBUser:                 cfg.cloudSQLUser,
		UseIAMAuthN:            true,
	})
	if err != nil {
		return err
	}
	defer registry.Close()

	redisCache := rediscache.New(cfg.redisAddr)
	defer redisCache.Close()

	computeMgr, err := compute.NewManager(ctx)
	if err != nil {
		return err
	}
	defer computeMgr.Close()

	// Warm the run's config into Redis before boot (PRD Section 5's hot path). The
	// run row itself, and its config document, are expected to already exist in
	// Cloud SQL (created by whatever submits the experiment matrix) — TODO: batch
	// mode should call registry.CreateRun itself instead of assuming this.
	runConfig, err := registry.GetRunConfig(ctx, cfg.runID)
	if err != nil {
		return err
	}
	if err := redisCache.PutConfig(ctx, cfg.runID, runConfig); err != nil {
		return err
	}

	instanceName := "freewill-run-" + cfg.runID
	spec := compute.InstanceSpec{
		Project:              cfg.project,
		Zone:                 cfg.zone,
		Name:                 instanceName,
		MachineType:          cfg.machineType,
		SourceImage:          cfg.sourceImage,
		Network:              cfg.network,
		Subnetwork:           cfg.subnetwork,
		ServiceAccount:       cfg.serviceAccount,
		ServiceAccountScopes: []string{"https://www.googleapis.com/auth/cloud-platform"},
		Metadata:             map[string]string{"run-id": cfg.runID},
		Preemptible:          true,
	}

	if err := registry.MarkRunStatus(ctx, cfg.runID, "provisioning", instanceName); err != nil {
		return err
	}
	if err := computeMgr.CreateInstance(ctx, spec); err != nil {
		_ = registry.MarkRunStatus(ctx, cfg.runID, "failed", instanceName)
		return err
	}
	if err := registry.MarkRunStatus(ctx, cfg.runID, "running", instanceName); err != nil {
		return err
	}

	if err := waitForCompletion(ctx, registry, computeMgr, cfg, instanceName); err != nil {
		return err
	}

	return computeMgr.DeleteInstance(ctx, cfg.project, cfg.zone, instanceName)
}

// waitForCompletion polls until either the instance's Cloud SQL run row reaches a
// terminal status (set by the Python engine itself on completion) or the instance
// disappears/stops without one, in which case the run is marked "failed" (PRD Section
// 9). This is a minimal polling loop; production use should replace it with an
// operations-log or Pub/Sub-based signal to avoid per-run polling at ~3,960-run scale.
func waitForCompletion(
	ctx context.Context,
	registry *cloudsql.RunRegistry,
	computeMgr *compute.Manager,
	cfg config,
	instanceName string,
) error {
	ticker := time.NewTicker(cfg.pollInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-ticker.C:
			hasSummary, err := registry.HasRunSummary(ctx, cfg.runID)
			if err != nil {
				return err
			}
			if hasSummary {
				return registry.MarkRunStatus(ctx, cfg.runID, "completed", instanceName)
			}

			inst, err := computeMgr.Get(ctx, cfg.project, cfg.zone, instanceName)
			if err != nil {
				// Instance is gone with no summary written -> failed run.
				return registry.MarkRunStatus(ctx, cfg.runID, "failed", instanceName)
			}
			if inst.GetStatus() == "TERMINATED" || inst.GetStatus() == "STOPPED" {
				return registry.MarkRunStatus(ctx, cfg.runID, "failed", instanceName)
			}
			// Still running with no summary yet -> keep polling.
		}
	}
}
