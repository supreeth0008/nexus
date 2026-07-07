package db

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"

	"github.com/supreeth0008/nexus/internal/model"
)

// ErrNotFound is returned when a requested row does not exist.
var ErrNotFound = errors.New("not found")

// IncidentStore persists incidents.
type IncidentStore struct {
	db *DB
}

// NewIncidentStore creates an incident store backed by db.
func NewIncidentStore(db *DB) *IncidentStore {
	return &IncidentStore{db: db}
}

// Create inserts a new incident.
func (s *IncidentStore) Create(ctx context.Context, inc *model.Incident) error {
	meta, err := json.Marshal(inc.Metadata)
	if err != nil {
		return fmt.Errorf("marshalling metadata: %w", err)
	}
	logJSON := inc.Log
	if len(logJSON) == 0 {
		logJSON = []byte("[]")
	}

	_, err = s.db.pool.ExecContext(ctx, `
		INSERT INTO incidents (
			id, type, severity, status, probe_id, target_id, source_signal,
			detected_at, root_cause, confidence, fix_generated, fix_pr_url,
			fix_branch, fix_summary, mttr_seconds, cycle_id, log, metadata
		) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18)`,
		inc.ID, inc.Type, inc.Severity, inc.Status, inc.ProbeID, inc.TargetID,
		inc.SourceSignal, inc.DetectedAt, inc.RootCause, inc.Confidence,
		inc.FixGenerated, inc.FixPR, inc.FixBranch, inc.FixSummary,
		inc.MTTRSeconds, inc.CycleID, logJSON, meta,
	)
	if err != nil {
		return fmt.Errorf("inserting incident: %w", err)
	}
	return nil
}

// Get fetches one incident by ID.
func (s *IncidentStore) Get(ctx context.Context, id string) (*model.Incident, error) {
	row := s.db.pool.QueryRowContext(ctx, `
		SELECT id, type, severity, status, probe_id, target_id, source_signal,
		       detected_at, diagnosed_at, fixed_at, verified_at, resolved_at,
		       root_cause, confidence, fix_generated, fix_pr_url, fix_branch,
		       fix_summary, verified, mttr_seconds, cycle_id, log, metadata
		FROM incidents WHERE id = $1`, id)

	inc, err := scanIncident(row)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, ErrNotFound
	}
	return inc, err
}

// List returns incidents ordered newest first, optionally filtered by
// status, up to limit rows.
func (s *IncidentStore) List(ctx context.Context, status model.IncidentStatus, limit int) ([]*model.Incident, error) {
	if limit <= 0 {
		limit = 50
	}

	query := `
		SELECT id, type, severity, status, probe_id, target_id, source_signal,
		       detected_at, diagnosed_at, fixed_at, verified_at, resolved_at,
		       root_cause, confidence, fix_generated, fix_pr_url, fix_branch,
		       fix_summary, verified, mttr_seconds, cycle_id, log, metadata
		FROM incidents`
	args := []any{}
	if status != "" {
		query += ` WHERE status = $1 ORDER BY detected_at DESC LIMIT $2`
		args = append(args, status, limit)
	} else {
		query += ` ORDER BY detected_at DESC LIMIT $1`
		args = append(args, limit)
	}

	rows, err := s.db.pool.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("listing incidents: %w", err)
	}
	defer rows.Close()

	var out []*model.Incident
	for rows.Next() {
		inc, err := scanIncident(rows)
		if err != nil {
			return nil, err
		}
		out = append(out, inc)
	}
	return out, rows.Err()
}

// UpdateStatus transitions an incident to a new status, enforcing the
// state machine defined in the model package.
func (s *IncidentStore) UpdateStatus(ctx context.Context, id string, to model.IncidentStatus) error {
	inc, err := s.Get(ctx, id)
	if err != nil {
		return err
	}
	if !inc.CanTransition(to) {
		return fmt.Errorf("illegal status transition %s -> %s for incident %s", inc.Status, to, id)
	}

	_, err = s.db.pool.ExecContext(ctx,
		`UPDATE incidents SET status = $1 WHERE id = $2`, to, id)
	if err != nil {
		return fmt.Errorf("updating incident status: %w", err)
	}
	return nil
}

// scanner abstracts *sql.Row and *sql.Rows.
type scanner interface {
	Scan(dest ...any) error
}

func scanIncident(sc scanner) (*model.Incident, error) {
	var inc model.Incident
	var meta []byte

	err := sc.Scan(
		&inc.ID, &inc.Type, &inc.Severity, &inc.Status, &inc.ProbeID,
		&inc.TargetID, &inc.SourceSignal, &inc.DetectedAt, &inc.DiagnosedAt,
		&inc.FixedAt, &inc.VerifiedAt, &inc.ResolvedAt, &inc.RootCause,
		&inc.Confidence, &inc.FixGenerated, &inc.FixPR, &inc.FixBranch,
		&inc.FixSummary, &inc.Verified, &inc.MTTRSeconds, &inc.CycleID,
		&inc.Log, &meta,
	)
	if err != nil {
		return nil, err
	}

	if len(meta) > 0 {
		if err := json.Unmarshal(meta, &inc.Metadata); err != nil {
			return nil, fmt.Errorf("unmarshalling incident metadata: %w", err)
		}
	}
	return &inc, nil
}
