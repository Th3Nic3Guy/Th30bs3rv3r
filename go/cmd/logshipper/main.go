// Command logshipper runs alongside the Python simulation engine on each run's Compute
// Engine instance (PRD Section 6.0, Section 9). It tails the engine's local JSON-lines
// event-log buffer (python/freewill/storage/event_log.py's staging file) and ships
// batches to two destinations, per PRD Section 6.5:
//
//   - Cloud Logging, as structured entries on the "freewill-events" log, labeled by
//     run_id/tick/event_type/mechanism for Log Explorer queries (PRD Section 7).
//   - Cloud Storage, as the durable, full-fidelity archive (PRD Section 6.5) — Cloud
//     Logging's own retention is not meant to be the only copy of the event history.
//
// Local development (docker-compose.yml): Cloud Logging has no official local emulator
// (unlike Cloud Storage, which internal/gcs just points at fake-gcs-server via
// STORAGE_EMULATOR_HOST with no code changes needed). The -local flag skips Cloud
// Logging entirely and logs each shipped event to stdout instead; the Cloud Storage
// side is unaffected and ships to the emulator exactly as it would to the real thing.
package main

import (
	"bufio"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"os"
	"strings"
	"time"

	"cloud.google.com/go/logging"

	"github.com/th3nic3guy/th30bs3rv3r/go/internal/gcs"
)

const eventsLogID = "freewill-events"

// eventRecord mirrors the JSON-lines shape python/freewill/storage/event_log.py.Event
// writes (PRD Section 6.5's example record). Only the fields used as Cloud Logging
// labels are named; anything else round-trips through Payload unparsed.
type eventRecord struct {
	RunID     string `json:"run_id"`
	Tick      int    `json:"tick"`
	EventType string `json:"event_type"`
	Mechanism string `json:"mechanism"`
}

type config struct {
	project      string
	stagingPath  string
	bucket       string
	runID        string
	batchSize    int
	pollInterval time.Duration
	local        bool
}

func main() {
	var cfg config
	flag.StringVar(&cfg.project, "project", "", "GCP project ID (ignored with -local)")
	flag.StringVar(&cfg.stagingPath, "staging-path", "", "path to the engine's local JSON-lines event-log staging file")
	flag.StringVar(&cfg.bucket, "bucket", "", "Cloud Storage bucket for the event-log archive (PRD 6.5: freewill-event-logs)")
	flag.StringVar(&cfg.runID, "run-id", "", "run_id being shipped")
	flag.IntVar(&cfg.batchSize, "batch-size", 500, "lines per shipped batch (matches the engine's EventLogBuffer flush_every)")
	flag.DurationVar(&cfg.pollInterval, "poll-interval", 5*time.Second, "how often to check the staging file for new lines")
	flag.BoolVar(&cfg.local, "local", false, "skip Cloud Logging (no local emulator exists) and log events to stdout instead; "+
		"set STORAGE_EMULATOR_HOST to point the Cloud Storage side at docker-compose's gcs-emulator service")
	flag.Parse()

	if cfg.stagingPath == "" || cfg.bucket == "" || cfg.runID == "" {
		log.Fatal("logshipper: -staging-path, -bucket, and -run-id are all required")
	}

	ctx := context.Background()
	if err := run(ctx, cfg); err != nil {
		log.Fatalf("logshipper: %v", err)
	}
}

func run(ctx context.Context, cfg config) error {
	var logger *logging.Logger
	if !cfg.local {
		logClient, err := logging.NewClient(ctx, cfg.project)
		if err != nil {
			return fmt.Errorf("logshipper: creating logging client: %w", err)
		}
		defer logClient.Close()
		logger = logClient.Logger(eventsLogID)
	}

	gcsClient, err := gcs.New(ctx, cfg.bucket)
	if err != nil {
		return fmt.Errorf("logshipper: creating gcs client: %w", err)
	}
	defer gcsClient.Close()

	var offset int64
	var batchSeq int
	ticker := time.NewTicker(cfg.pollInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-ticker.C:
			newOffset, shipped, err := shipNewLines(ctx, cfg, logger, gcsClient, offset, batchSeq)
			if err != nil {
				log.Printf("logshipper: batch failed, will retry next tick: %v", err)
				continue
			}
			offset = newOffset
			if shipped {
				batchSeq++
			}
		}
	}
}

// shipNewLines reads any lines appended to the staging file since `offset`, ships
// them as one Cloud Logging batch + one Cloud Storage archive object (PRD 6.5), and
// returns the new read offset.
func shipNewLines(
	ctx context.Context,
	cfg config,
	logger *logging.Logger,
	gcsClient *gcs.Client,
	offset int64,
	batchSeq int,
) (newOffset int64, shipped bool, err error) {
	f, err := os.Open(cfg.stagingPath)
	if err != nil {
		if os.IsNotExist(err) {
			// Engine hasn't created the staging file yet; nothing to do this tick.
			return offset, false, nil
		}
		return offset, false, fmt.Errorf("opening staging file: %w", err)
	}
	defer f.Close()

	if _, err := f.Seek(offset, io.SeekStart); err != nil {
		return offset, false, fmt.Errorf("seeking staging file: %w", err)
	}

	var batch strings.Builder
	scanner := bufio.NewScanner(f)
	scanner.Buffer(make([]byte, 0, 64*1024), 1024*1024)
	lineCount := 0
	var bytesRead int64

	for scanner.Scan() {
		line := scanner.Text()
		bytesRead += int64(len(line)) + 1 // +1 for the newline the scanner strips

		var rec eventRecord
		if err := json.Unmarshal([]byte(line), &rec); err != nil {
			log.Printf("logshipper: skipping malformed line: %v", err)
			continue
		}

		if logger != nil {
			logger.Log(logging.Entry{
				Payload: json.RawMessage(line),
				Labels: map[string]string{
					"run_id":     rec.RunID,
					"event_type": rec.EventType,
					"mechanism":  rec.Mechanism,
				},
			})
		} else {
			log.Printf("[event] run=%s type=%s mechanism=%s", rec.RunID, rec.EventType, rec.Mechanism)
		}

		batch.WriteString(line)
		batch.WriteByte('\n')
		lineCount++
	}
	if err := scanner.Err(); err != nil {
		return offset, false, fmt.Errorf("scanning staging file: %w", err)
	}

	if lineCount == 0 {
		return offset, false, nil
	}

	if logger != nil {
		if err := logger.Flush(); err != nil {
			return offset, false, fmt.Errorf("flushing cloud logging batch: %w", err)
		}
	}

	// TODO: a periodic compaction job should merge these per-batch objects into the
	// single gs://{bucket}/{run_id}/events.jsonl archive PRD Section 6.5 describes;
	// GCS objects aren't independently appendable, so batches land as separate
	// objects here and compaction is a downstream concern.
	objectPath := fmt.Sprintf("%s/batches/events-%06d.jsonl", cfg.runID, batchSeq)
	if _, err := gcsClient.UploadObject(ctx, objectPath, strings.NewReader(batch.String())); err != nil {
		return offset, false, fmt.Errorf("uploading batch to gcs: %w", err)
	}

	return offset + bytesRead, true, nil
}
