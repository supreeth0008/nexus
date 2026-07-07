package utils

import (
	"context"
	"errors"
	"testing"
	"time"
)

func fastConfig(attempts int) RetryConfig {
	return RetryConfig{
		MaxAttempts:  attempts,
		InitialDelay: time.Millisecond,
		MaxDelay:     5 * time.Millisecond,
		Multiplier:   2.0,
	}
}

func TestRetrySucceedsFirstTry(t *testing.T) {
	calls := 0
	err := Retry(context.Background(), fastConfig(3), func() error {
		calls++
		return nil
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if calls != 1 {
		t.Errorf("calls = %d, want 1", calls)
	}
}

func TestRetryEventuallySucceeds(t *testing.T) {
	calls := 0
	err := Retry(context.Background(), fastConfig(5), func() error {
		calls++
		if calls < 3 {
			return errors.New("transient")
		}
		return nil
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if calls != 3 {
		t.Errorf("calls = %d, want 3", calls)
	}
}

func TestRetryExhaustsAttempts(t *testing.T) {
	calls := 0
	err := Retry(context.Background(), fastConfig(3), func() error {
		calls++
		return errors.New("permanent")
	})
	if err == nil {
		t.Fatal("expected error, got nil")
	}
	if calls != 3 {
		t.Errorf("calls = %d, want 3", calls)
	}
}

func TestRetryRespectsContextCancel(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	err := Retry(ctx, fastConfig(3), func() error {
		return errors.New("should not matter")
	})
	if err == nil {
		t.Fatal("expected cancellation error, got nil")
	}
}
