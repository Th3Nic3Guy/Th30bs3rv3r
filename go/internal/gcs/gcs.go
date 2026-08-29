// Package gcs is a thin Cloud Storage client for the objects the Go services write:
// the event-log archive (PRD Section 6.5) uploaded by the log shipper, and metadata
// reads the orchestrator needs at run start. Checkpoint archives themselves (PRD Section
// 6.2) are written by the Python simulation engine directly
// (python/freewill/storage/checkpoint_store.py) — this package does not duplicate that.
package gcs

import (
	"context"
	"fmt"
	"io"

	"cloud.google.com/go/storage"
)

// Client wraps a Cloud Storage client scoped to one bucket.
type Client struct {
	bucket string
	gcs    *storage.Client
}

// New creates a Client for the given bucket, e.g. "freewill-event-logs" (PRD 6.5) or
// "freewill-checkpoints" (PRD 6.2).
func New(ctx context.Context, bucket string) (*Client, error) {
	gcsClient, err := storage.NewClient(ctx)
	if err != nil {
		return nil, fmt.Errorf("gcs: creating client: %w", err)
	}
	return &Client{bucket: bucket, gcs: gcsClient}, nil
}

// UploadObject writes r to gs://{bucket}/{objectPath}, overwriting any existing object,
// and returns the resulting gs:// URI. Used by the log shipper to upload event-log
// batches (PRD 6.5: "gs://freewill-event-logs/{run_id}/events.jsonl").
func (c *Client) UploadObject(ctx context.Context, objectPath string, r io.Reader) (string, error) {
	w := c.gcs.Bucket(c.bucket).Object(objectPath).NewWriter(ctx)
	w.ContentType = "application/x-ndjson"

	if _, err := io.Copy(w, r); err != nil {
		_ = w.Close()
		return "", fmt.Errorf("gcs: writing object %q: %w", objectPath, err)
	}
	if err := w.Close(); err != nil {
		return "", fmt.Errorf("gcs: closing object %q: %w", objectPath, err)
	}
	return fmt.Sprintf("gs://%s/%s", c.bucket, objectPath), nil
}

// Close releases the underlying Cloud Storage client.
func (c *Client) Close() error {
	return c.gcs.Close()
}
