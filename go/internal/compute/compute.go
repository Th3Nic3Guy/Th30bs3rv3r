// Package compute manages the Compute Engine instance lifecycle for one simulation run
// (PRD Section 6.0, Section 2 principle 4: exactly one instance per run). Used by the
// orchestrator (cmd/orchestrator) to provision a run's VM, wait for it to finish, and
// tear it down.
package compute

import (
	"context"
	"fmt"

	compute "cloud.google.com/go/compute/apiv1"
	"cloud.google.com/go/compute/apiv1/computepb"
	"google.golang.org/protobuf/proto"
)

// InstanceSpec describes the per-run Compute Engine instance to create. Callers fill
// this in from the run's config (freewill.config.params.RunConfig on the Python side)
// plus infra-level defaults from infra/terraform/compute.tf's instance template.
type InstanceSpec struct {
	Project     string
	Zone        string
	Name        string // e.g. "freewill-run-{run_id}"
	MachineType string // e.g. "n2-standard-4"; sized per PRD Section 4.1's population/tensor scale
	// SourceImage is the prebuilt image carrying the Python simulation engine
	// (python/Dockerfile baked into a Compute Engine image, or a container-optimized-OS
	// image running that container) — PRD Section 6.0 step 1.
	SourceImage          string
	Network              string
	Subnetwork           string
	ServiceAccount       string
	ServiceAccountScopes []string
	// Metadata is passed to the instance as key/value pairs; must include at least
	// "run-id" so the instance's startup script (or container entrypoint) knows which
	// run to load from Cloud SQL/Redis (PRD Section 5).
	Metadata map[string]string
	// Preemptible instances are cheaper for the ~3,960-run experiment budget (PRD
	// Section 1) but require the orchestrator to retry on preemption (PRD Section 9).
	Preemptible bool
}

// Manager wraps the Compute Engine Instances client.
type Manager struct {
	client *compute.InstancesClient
}

// NewManager creates a Manager. Callers must call Close when done.
func NewManager(ctx context.Context) (*Manager, error) {
	client, err := compute.NewInstancesRESTClient(ctx)
	if err != nil {
		return nil, fmt.Errorf("compute: creating instances client: %w", err)
	}
	return &Manager{client: client}, nil
}

// CreateInstance provisions one Compute Engine instance for a run and waits for the
// insert operation to complete (i.e. the instance exists and is booting) — not for the
// simulation itself to finish. Callers poll WaitForCompletion for that.
func (m *Manager) CreateInstance(ctx context.Context, spec InstanceSpec) error {
	items := make([]*computepb.Items, 0, len(spec.Metadata))
	for k, v := range spec.Metadata {
		items = append(items, &computepb.Items{Key: proto.String(k), Value: proto.String(v)})
	}

	req := &computepb.InsertInstanceRequest{
		Project: spec.Project,
		Zone:    spec.Zone,
		InstanceResource: &computepb.Instance{
			Name:        proto.String(spec.Name),
			MachineType: proto.String(fmt.Sprintf("zones/%s/machineTypes/%s", spec.Zone, spec.MachineType)),
			Scheduling: &computepb.Scheduling{
				Preemptible: proto.Bool(spec.Preemptible),
			},
			Disks: []*computepb.AttachedDisk{{
				Boot:       proto.Bool(true),
				AutoDelete: proto.Bool(true),
				InitializeParams: &computepb.AttachedDiskInitializeParams{
					SourceImage: proto.String(spec.SourceImage),
				},
			}},
			NetworkInterfaces: []*computepb.NetworkInterface{{
				Network:    proto.String(spec.Network),
				Subnetwork: proto.String(spec.Subnetwork),
			}},
			ServiceAccounts: []*computepb.ServiceAccount{{
				Email:  proto.String(spec.ServiceAccount),
				Scopes: spec.ServiceAccountScopes,
			}},
			Metadata: &computepb.Metadata{Items: items},
			Labels:   map[string]string{"freewill-run": "true"},
		},
	}

	op, err := m.client.Insert(ctx, req)
	if err != nil {
		return fmt.Errorf("compute: inserting instance %q: %w", spec.Name, err)
	}
	if err := op.Wait(ctx); err != nil {
		return fmt.Errorf("compute: waiting for instance %q to be created: %w", spec.Name, err)
	}
	return nil
}

// Get fetches the current instance resource, e.g. so the orchestrator can check
// Status ("RUNNING", "TERMINATED", ...) while polling for run completion (PRD Section
// 9). Completion itself is signaled out-of-band, by the run's Cloud SQL status row
// (internal/cloudsql.RunRegistry) — this is for detecting an instance that disappeared
// or stopped without the engine reporting completion.
func (m *Manager) Get(ctx context.Context, project, zone, name string) (*computepb.Instance, error) {
	inst, err := m.client.Get(ctx, &computepb.GetInstanceRequest{
		Project:  project,
		Zone:     zone,
		Instance: name,
	})
	if err != nil {
		return nil, fmt.Errorf("compute: getting instance %q: %w", name, err)
	}
	return inst, nil
}

// DeleteInstance tears down a run's instance once it has completed (or been marked
// failed) — PRD Section 6.0 step 6.
func (m *Manager) DeleteInstance(ctx context.Context, project, zone, name string) error {
	op, err := m.client.Delete(ctx, &computepb.DeleteInstanceRequest{
		Project:  project,
		Zone:     zone,
		Instance: name,
	})
	if err != nil {
		return fmt.Errorf("compute: deleting instance %q: %w", name, err)
	}
	if err := op.Wait(ctx); err != nil {
		return fmt.Errorf("compute: waiting for instance %q to be deleted: %w", name, err)
	}
	return nil
}

// Close releases the underlying Compute Engine client.
func (m *Manager) Close() error {
	return m.client.Close()
}
