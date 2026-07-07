package utils

import (
	"context"
	"fmt"
	"math/rand"
	"time"
)

// RetryConfig controls the backoff behaviour of Retry.
type RetryConfig struct {
	// MaxAttempts is the total number of attempts, including the first.
	MaxAttempts int
	// InitialDelay is the delay before the first retry.
	InitialDelay time.Duration
	// MaxDelay caps the exponential backoff.
	MaxDelay time.Duration
	// Multiplier grows the delay after each attempt.
	Multiplier float64
	// Jitter adds up to this fraction of random variation to each delay
	// so concurrent retries do not synchronise.
	Jitter float64
}

// DefaultRetryConfig is the configuration I use for external API calls
// (cloud providers, GitHub, Prometheus).
func DefaultRetryConfig() RetryConfig {
	return RetryConfig{
		MaxAttempts:  5,
		InitialDelay: 500 * time.Millisecond,
		MaxDelay:     30 * time.Second,
		Multiplier:   2.0,
		Jitter:       0.2,
	}
}

// Retry runs fn until it succeeds, the attempts are exhausted, or the
// context is cancelled. It returns the last error on failure.
func Retry(ctx context.Context, cfg RetryConfig, fn func() error) error {
	if cfg.MaxAttempts < 1 {
		cfg.MaxAttempts = 1
	}

	delay := cfg.InitialDelay
	var lastErr error

	for attempt := 1; attempt <= cfg.MaxAttempts; attempt++ {
		if err := ctx.Err(); err != nil {
			return fmt.Errorf("retry cancelled: %w", err)
		}

		if lastErr = fn(); lastErr == nil {
			return nil
		}

		if attempt == cfg.MaxAttempts {
			break
		}

		sleep := delay
		if cfg.Jitter > 0 {
			jitter := time.Duration(rand.Float64() * cfg.Jitter * float64(delay))
			sleep += jitter
		}

		select {
		case <-ctx.Done():
			return fmt.Errorf("retry cancelled: %w", ctx.Err())
		case <-time.After(sleep):
		}

		delay = time.Duration(float64(delay) * cfg.Multiplier)
		if cfg.MaxDelay > 0 && delay > cfg.MaxDelay {
			delay = cfg.MaxDelay
		}
	}

	return fmt.Errorf("all %d attempts failed: %w", cfg.MaxAttempts, lastErr)
}
