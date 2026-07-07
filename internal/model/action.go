package model

import "time"

// Action is a single remediation step Nexus generated for an incident.
type Action struct {
	ID         string       `json:"id" db:"id"`
	IncidentID string       `json:"incident_id" db:"incident_id"`
	Kind       ActionKind   `json:"kind" db:"kind"`
	Summary    string       `json:"summary" db:"summary"`
	Diff       string       `json:"diff" db:"diff"` // rendered diff of the proposed change
	Risk       ActionRisk   `json:"risk" db:"risk"`
	Status     ActionStatus `json:"status" db:"status"`
	PRURL      string       `json:"pr_url,omitempty" db:"pr_url"`
	CreatedAt  time.Time    `json:"created_at" db:"created_at"`
	AppliedAt  *time.Time   `json:"applied_at,omitempty" db:"applied_at"`
}

// ActionKind identifies the remediation mechanism.
type ActionKind string

const (
	ActionOpenTofu ActionKind = "opentofu"
	ActionK8s      ActionKind = "kubernetes"
	ActionHelm     ActionKind = "helm"
)

// ActionRisk classifies blast radius; policy gates key off this.
type ActionRisk string

const (
	RiskLow    ActionRisk = "low"
	RiskMedium ActionRisk = "medium"
	RiskHigh   ActionRisk = "high"
)

// ActionStatus tracks the lifecycle of a remediation action.
type ActionStatus string

const (
	ActionProposed   ActionStatus = "proposed"
	ActionValidated  ActionStatus = "validated"
	ActionApplied    ActionStatus = "applied"
	ActionRejected   ActionStatus = "rejected"
	ActionRolledBack ActionStatus = "rolled_back"
)
