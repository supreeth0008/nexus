// Package db provides the PostgreSQL connection layer and an embedded
// migrations framework.
//
// I embed the SQL migration files into the binary so a Nexus deployment
// is always self-contained: the binary carries the exact schema it
// expects and applies pending migrations at startup.
package db

import (
	"context"
	"database/sql"
	"embed"
	"fmt"
	"io/fs"
	"log/slog"
	"sort"
	"strings"
	"time"

	_ "github.com/jackc/pgx/v5/stdlib" // registers the "pgx" driver
)

//go:embed migrations/*.sql
var migrationFS embed.FS

// DB wraps the SQL connection pool.
type DB struct {
	pool *sql.DB
}

// Connect opens a PostgreSQL connection pool and verifies connectivity.
func Connect(ctx context.Context, dsn string) (*DB, error) {
	if dsn == "" {
		return nil, fmt.Errorf("database DSN is empty; set database.dsn in nexus.yaml or NEXUS_DATABASE_DSN")
	}

	pool, err := sql.Open("pgx", dsn)
	if err != nil {
		return nil, fmt.Errorf("opening database: %w", err)
	}

	pool.SetMaxOpenConns(10)
	pool.SetMaxIdleConns(5)
	pool.SetConnMaxLifetime(30 * time.Minute)

	pingCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	if err := pool.PingContext(pingCtx); err != nil {
		pool.Close()
		return nil, fmt.Errorf("pinging database: %w", err)
	}

	return &DB{pool: pool}, nil
}

// Close releases the connection pool.
func (d *DB) Close() error {
	return d.pool.Close()
}

// Pool exposes the underlying pool for the store packages.
func (d *DB) Pool() *sql.DB {
	return d.pool
}

// Migrate applies all pending migrations in filename order. Each file
// runs inside its own transaction and is recorded in schema_migrations,
// so a partially failed migration never leaves the tracking table
// inconsistent.
func (d *DB) Migrate(ctx context.Context) error {
	if _, err := d.pool.ExecContext(ctx, `
		CREATE TABLE IF NOT EXISTS schema_migrations (
			version    TEXT PRIMARY KEY,
			applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
		)`); err != nil {
		return fmt.Errorf("creating schema_migrations: %w", err)
	}

	applied := map[string]bool{}
	rows, err := d.pool.QueryContext(ctx, `SELECT version FROM schema_migrations`)
	if err != nil {
		return fmt.Errorf("reading applied migrations: %w", err)
	}
	defer rows.Close()
	for rows.Next() {
		var v string
		if err := rows.Scan(&v); err != nil {
			return err
		}
		applied[v] = true
	}
	if err := rows.Err(); err != nil {
		return err
	}

	entries, err := fs.Glob(migrationFS, "migrations/*.sql")
	if err != nil {
		return fmt.Errorf("listing migrations: %w", err)
	}
	sort.Strings(entries)

	for _, path := range entries {
		version := strings.TrimSuffix(strings.TrimPrefix(path, "migrations/"), ".sql")
		if applied[version] {
			continue
		}

		content, err := migrationFS.ReadFile(path)
		if err != nil {
			return fmt.Errorf("reading migration %s: %w", version, err)
		}

		tx, err := d.pool.BeginTx(ctx, nil)
		if err != nil {
			return fmt.Errorf("starting transaction for %s: %w", version, err)
		}

		if _, err := tx.ExecContext(ctx, string(content)); err != nil {
			tx.Rollback()
			return fmt.Errorf("applying migration %s: %w", version, err)
		}
		if _, err := tx.ExecContext(ctx, `INSERT INTO schema_migrations (version) VALUES ($1)`, version); err != nil {
			tx.Rollback()
			return fmt.Errorf("recording migration %s: %w", version, err)
		}
		if err := tx.Commit(); err != nil {
			return fmt.Errorf("committing migration %s: %w", version, err)
		}

		slog.Info("applied migration", "version", version)
	}

	return nil
}
