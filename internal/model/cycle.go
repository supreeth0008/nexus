package model

import "time"

// Cycle records one full run of the closed loop against a target.
type Cycle struct {
	ID          string       `json:"id" db:"id"`
	StartedAt   time.Time    `json:"started_at" db:"started_at"`
	CompletedAt *time.Time   `json:"completed_at,omitempty" db:"completed_at"`
	Trigger     CycleTrigger `json:"trigger" db:"trigger"`
	Status      CycleStatus  `json:"status" db:"status"`

	// Phase timestamps
	ObserveAt  *time.Time `json:"observe_at,omitempty" db:"observe_at"`
	DetectAt   *time.Time `json:"detect_at,omitempty" db:"detect_at"`
	DiagnoseAt *time.Time `json:"diagnose_at,omitempty" db:"diagnose_at"`
	GenerateAt *time.Time `json:"generate_at,omitempty" db:"generate_at"`
	ValidateAt *time.Time `json:"validate_at,omitempty" db:"validate_at"`
	ApplyAt    *time.Time `json:"apply_at,omitempty" db:"apply_at"`
	VerifyAt   *time.Time `json:"verify_at,omitempty" db:"verify_at"`

	// Results
	IncidentsDetected int      `json:"incidents_detected" db:"incidents_detected"`
	FixesApplied      int      `json:"fixes_applied" db:"fixes_applied"`
	Errors            []string `json:"errors,omitempty" db:"errors"`

	TargetID string `json:"target_id" db:"target_id"`
}

// CycleTrigger records what started a cycle.
type CycleTrigger string

const (
	TriggerScheduled CycleTrigger = "scheduled"
	TriggerEvent     CycleTrigger = "event"
	TriggerManual    CycleTrigger = "manual"
)

// CycleStatus reflects the overall state of a cycle run.
type CycleStatus string

const (
	CycleRunning   CycleStatus = "running"
	CycleCompleted CycleStatus = "completed"
	CycleFailed    CycleStatus = "failed"
	CycleAborted   CycleStatus = "aborted"
)
