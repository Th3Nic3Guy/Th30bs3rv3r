// Package rediscache is the Go-side Memorystore (Redis) client (PRD Section 5, 6.3).
// The orchestrator (cmd/orchestrator) uses it to warm a run's config into Redis before
// the run's Compute Engine instance boots — the "hot path" PRD Section 5 describes:
// Cloud SQL is the source of truth, Redis is what the simulation engine actually reads
// from during the tick loop. Keys and TTLs here must match
// python/freewill/storage/config_cache.py exactly, since both sides read/write the same
// keys.
package rediscache

import (
	"context"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

const (
	configTTL = 24 * time.Hour     // PRD 5: config is read-mostly; TTL just bounds staleness
	dagTTL    = 7 * 24 * time.Hour // PRD 6.3: static per-domain tensors change rarely
)

func configKey(runID string) string { return fmt.Sprintf("run:%s:config", runID) }
func dagKey(domain string) string   { return fmt.Sprintf("domain:%s:dag", domain) }

// Cache wraps a Redis client. Per PRD Section 2, principle 5, this is a cache, not a
// system of record — every value it holds must be reconstructable from Cloud SQL or
// Cloud Storage.
type Cache struct {
	rdb *redis.Client
}

// New connects to a Memorystore Redis instance at addr (host:port, PRD
// infra/terraform/redis.tf's private IP + port output).
func New(addr string) *Cache {
	return &Cache{rdb: redis.NewClient(&redis.Options{Addr: addr})}
}

// PutConfig warms run_id's config JSON (as fetched from Cloud SQL via
// internal/cloudsql.RunRegistry.GetRunConfig) into Redis, matching the key
// python/freewill/storage/config_cache.py.ConfigCache.get_config reads.
func (c *Cache) PutConfig(ctx context.Context, runID string, configJSON []byte) error {
	if err := c.rdb.Set(ctx, configKey(runID), configJSON, configTTL).Err(); err != nil {
		return fmt.Errorf("rediscache: warming config for %q: %w", runID, err)
	}
	return nil
}

// PutDomainDAG caches a domain's serialized static DAG adjacency tensors (D and A, PRD
// 4.1), so repeated runs against the same domain don't re-parse them from Cloud Storage
// on every fresh Compute Engine instance.
func (c *Cache) PutDomainDAG(ctx context.Context, domain string, serialized []byte) error {
	if err := c.rdb.Set(ctx, dagKey(domain), serialized, dagTTL).Err(); err != nil {
		return fmt.Errorf("rediscache: warming DAG cache for domain %q: %w", domain, err)
	}
	return nil
}

// Close closes the underlying Redis client.
func (c *Cache) Close() error {
	return c.rdb.Close()
}
