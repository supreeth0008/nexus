package db

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"

	"github.com/supreeth0008/nexus/internal/model"
)

// CycleStore persists cycle history.
type CycleStore struct {
	db *DB
}

// NewCycleStore creates a cycle store backed by db.
func NewCycleStore(db *DB) *CycleStore {
	return &CycleStore{db: db}
}

// Create inserts a new cycle record.
func (s *CycleStore) Create(ctx context.Context, c *model.Cycle) error {
	errs, err := json.Marshal(c.Errors)
	if err != nil {
		return fmt.Errorf("marshalling errors: %w", err)
	}

	_, err = s.db.pool.ExecContext(ctx, `
		INSERT INTO cycles (
			id, started_at, completed_at, trigger, status,
			observe_at, detect_at, diagnose_at, generate_at, validate_at,
			apply_at, verify_at, incidents_detected, fixes_applied, errors, target_id
		) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16)`,
		c.ID, c.StartedAt, c.CompletedAt, c.Trigger, c.Status,
		c.ObserveAt, c.DetectAt, c.DiagnoseAt, c.GenerateAt, c.ValidateAt,
		c.ApplyAt, c.VerifyAt, c.IncidentsDetected, c.FixesApplied, errs, c.TargetID,
	)
	if err != nil {
		return fmt.Errorf("inserting cycle: %w", err)
	}
	return nil
}

// Get fetches one cycle by ID.
func (s *CycleStore) Get(ctx context.Context, id string) (*model.Cycle, error) {
	row := s.db.pool.QueryRowContext(ctx, `
		SELECT id, started_at, completed_at, trigger, status,
		       observe_at, detect_at, diagnose_at, generate_at, validate_at,
		       apply_at, verify_at, incidents_detected, fixes_applied, errors, target_id
		FROM cycles WHERE id = $1`, id)
	c, err := scanCycle(row)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, ErrNotFound
	}
	return c, err
}

// List returns the most recent cycles up to limit.
func (s *CycleStore) List(ctx context.Context, limit int) ([]*model.Cycle, error) {
	if limit <= 0 {
		limit = 50
	}
	rows, err := s.db.pool.QueryContext(ctx, `
		SELECT id, started_at, completed_at, trigger, status,
		       observe_at, detect_at, diagnose_at, generate_at, validate_at,
		       apply_at, verify_at, incidents_detected, fixes_applied, errors, target_id
		FROM cycles ORDER BY started_at DESC LIMIT $1`, limit)
	if err != nil {
		return nil, fmt.Errorf("listing cycles: %w", err)
	}
	defer func() { _ = rows.Close() }()

	var out []*model.Cycle
	for rows.Next() {
		c, err := scanCycle(rows)
		if err != nil {
			return nil, err
		}
		out = append(out, c)
	}
	return out, rows.Err()
}

func scanCycle(sc scanner) (*model.Cycle, error) {
	var c model.Cycle
	var errs []byte

	err := sc.Scan(&c.ID, &c.StartedAt, &c.CompletedAt, &c.Trigger, &c.Status,
		&c.ObserveAt, &c.DetectAt, &c.DiagnoseAt, &c.GenerateAt, &c.ValidateAt,
		&c.ApplyAt, &c.VerifyAt, &c.IncidentsDetected, &c.FixesApplied,
		&errs, &c.TargetID)
	if err != nil {
		return nil, err
	}

	if err := json.Unmarshal(errs, &c.Errors); err != nil {
		return nil, fmt.Errorf("unmarshalling cycle errors: %w", err)
	}
	return &c, nil
}
