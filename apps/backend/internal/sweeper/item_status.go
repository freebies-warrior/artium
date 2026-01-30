package sweeper

import (
	"context"
	"database/sql"
	"log"
	"time"
)

const lockID int64 = 67 // for pg advisory lock identification

func SweepOnce(ctx context.Context, db *sql.DB) error {
	start := time.Now()

	// Ensure only one instance sweeps (important if you ever scale replicas)
	var locked bool
	if err := db.QueryRowContext(ctx, `SELECT pg_try_advisory_lock($1)`, lockID).Scan(&locked); err != nil {
		return err
	}
	if !locked {
		return nil
	}
	defer func() { _, _ = db.ExecContext(context.Background(), `SELECT pg_advisory_unlock($1)`, lockID) }()

	var ended, activated int
	if err := db.QueryRowContext(ctx, `SELECT ended_count, activated_count FROM public.sweep_item_statuses()`).Scan(&ended, &activated); err != nil {
		return err
	}

	// Log only when something changed
	if ended+activated > 0 {
		log.Printf("status_sweeper: activated=%d ended=%d duration=%s", activated, ended, time.Since(start))
	}
	return nil
}

func Start(ctx context.Context, db *sql.DB, interval time.Duration) {
	ticker := time.NewTicker(interval)
	go func() {
		defer ticker.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				if err := SweepOnce(ctx, db); err != nil {
					log.Printf("status_sweeper error: %v", err)
				}
			}
		}
	}()
}
