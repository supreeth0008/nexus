package db

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"

	"github.com/supreeth0008/nexus/internal/model"
)

// TargetStore persists observed infrastructure targets.
type TargetStore struct {
	db *DB
}

// NewTargetStore creates a target store backed by db.
func NewTargetStore(db *DB) *TargetStore {
	return &TargetStore{db: db}
}

// Create inserts a new target.
func (s *TargetStore) Create(ctx context.Context, t *model.Target) error {
	regions, err := json.Marshal(t.Regions)
	if err != nil {
		return fmt.Errorf("marshalling regions: %w", err)
	}
	auth, err := json.Marshal(t.Auth)
	if err != nil {
		return fmt.Errorf("marshalling auth: %w", err)
	}

	_, err = s.db.pool.ExecContext(ctx, `
		INSERT INTO targets (id, name, provider, regions, endpoint, auth, status, created_at, updated_at)
		VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)`,
		t.ID, t.Name, t.Provider, regions, t.Endpoint, auth, t.Status,
		t.CreatedAt, t.UpdatedAt,
	)
	if err != nil {
		return fmt.Errorf("inserting target: %w", err)
	}
	return nil
}

// Get fetches one target by ID.
func (s *TargetStore) Get(ctx context.Context, id string) (*model.Target, error) {
	row := s.db.pool.QueryRowContext(ctx, `
		SELECT id, name, provider, regions, endpoint, auth, status, created_at, updated_at
		FROM targets WHERE id = $1`, id)
	t, err := scanTarget(row)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, ErrNotFound
	}
	return t, err
}

// List returns all targets ordered by name.
func (s *TargetStore) List(ctx context.Context) ([]*model.Target, error) {
	rows, err := s.db.pool.QueryContext(ctx, `
		SELECT id, name, provider, regions, endpoint, auth, status, created_at, updated_at
		FROM targets ORDER BY name`)
	if err != nil {
		return nil, fmt.Errorf("listing targets: %w", err)
	}
	defer rows.Close()

	var out []*model.Target
	for rows.Next() {
		t, err := scanTarget(rows)
		if err != nil {
			return nil, err
		}
		out = append(out, t)
	}
	return out, rows.Err()
}

// Delete removes a target by ID.
func (s *TargetStore) Delete(ctx context.Context, id string) error {
	res, err := s.db.pool.ExecContext(ctx, `DELETE FROM targets WHERE id = $1`, id)
	if err != nil {
		return fmt.Errorf("deleting target: %w", err)
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		return ErrNotFound
	}
	return nil
}

func scanTarget(sc scanner) (*model.Target, error) {
	var t model.Target
	var regions, auth []byte

	err := sc.Scan(&t.ID, &t.Name, &t.Provider, &regions, &t.Endpoint,
		&auth, &t.Status, &t.CreatedAt, &t.UpdatedAt)
	if err != nil {
		return nil, err
	}

	if err := json.Unmarshal(regions, &t.Regions); err != nil {
		return nil, fmt.Errorf("unmarshalling regions: %w", err)
	}
	if err := json.Unmarshal(auth, &t.Auth); err != nil {
		return nil, fmt.Errorf("unmarshalling auth: %w", err)
	}
	return &t, nil
}
