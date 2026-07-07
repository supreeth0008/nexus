// Package model defines the core data structures shared across Nexus.
//
// I keep these free of behaviour beyond simple helpers: probes,
// analyzers, remediators, and stores all communicate through these
// types, so they must stay dependency-free.
package model

import (
	"encoding/json"
	"time"
)

// Incident is a detected problem moving through the closed loop.
type Incident struct {
	ID       string         `json:"id" db:"id"`
	Type     IncidentType   `json:"type" db:"type"`
	Severity Severity       `json:"severity" db:"severity"`
	Status   IncidentStatus `json:"status" db:"status"`

	// Source
	ProbeID      string `json:"probe_id" db:"probe_id"`
	TargetID     string `json:"target_id" db:"target_id"`
	SourceSignal string `json:"source_signal" db:"source_signal"`

	// Timeline
	DetectedAt  time.Time  `json:"detected_at" db:"detected_at"`
	DiagnosedAt *time.Time `json:"diagnosed_at,omitempty" db:"diagnosed_at"`
	FixedAt     *time.Time `json:"fixed_at,omitempty" db:"fixed_at"`
	VerifiedAt  *time.Time `json:"verified_at,omitempty" db:"verified_at"`
	ResolvedAt  *time.Time `json:"resolved_at,omitempty" db:"resolved_at"`

	// Diagnosis
	RootCause  string  `json:"root_cause" db:"root_cause"`
	Confidence float64 `json:"confidence" db:"confidence"` // 0.0 to 1.0

	// Fix
	FixGenerated bool   `json:"fix_generated" db:"fix_generated"`
	FixPR        string `json:"fix_pr_url" db:"fix_pr_url"`
	FixBranch    string `json:"fix_branch" db:"fix_branch"`
	FixSummary   string `json:"fix_summary" db:"fix_summary"`

	// Verification
	Verified    *bool `json:"verified,omitempty" db:"verified"`
	MTTRSeconds int64 `json:"mttr_seconds" db:"mttr_seconds"`

	// Audit
	CycleID  string          `json:"cycle_id" db:"cycle_id"`
	Log      json.RawMessage `json:"log,omitempty" db:"log"`
	Metadata map[string]any  `json:"metadata,omitempty" db:"metadata"`
}

// IncidentType classifies what kind of problem was detected.
type IncidentType string

// Incident type values recognised by the analyzers.
const (
	IncidentCostSpike       IncidentType = "cost_spike"
	IncidentPerformance     IncidentType = "performance_degradation"
	IncidentSecurityDrift   IncidentType = "security_drift"
	IncidentComplianceDrift IncidentType = "compliance_drift"
	IncidentReliability     IncidentType = "reliability_degradation"
	IncidentScale           IncidentType = "scaling_bottleneck"
	IncidentConfigDrift     IncidentType = "configuration_drift"
	IncidentResourceExhaust IncidentType = "resource_exhaustion"
	IncidentErrorBurst      IncidentType = "error_burst"
	IncidentCustom          IncidentType = "custom"
)

// Severity ranks how urgent an incident is.
type Severity string

// Severity values ordered from most to least urgent.
const (
	SeverityCritical Severity = "critical"
	SeverityHigh     Severity = "high"
	SeverityMedium   Severity = "medium"
	SeverityLow      Severity = "low"
	SeverityInfo     Severity = "info"
)

// IncidentStatus tracks progress through the closed loop.
type IncidentStatus string

// Incident status values covering the closed-loop lifecycle.
const (
	StatusDetected   IncidentStatus = "detected"
	StatusDiagnosing IncidentStatus = "diagnosing"
	StatusDiagnosed  IncidentStatus = "diagnosed"
	StatusFixing     IncidentStatus = "fixing"
	StatusFixReady   IncidentStatus = "fix_ready" // PR open, awaiting approval
	StatusApplying   IncidentStatus = "applying"
	StatusVerifying  IncidentStatus = "verifying"
	StatusResolved   IncidentStatus = "resolved"
	StatusFailed     IncidentStatus = "failed"
	StatusEscalated  IncidentStatus = "escalated" // blocked by a policy gate
)

// validTransitions encodes the incident state machine. I enforce this
// centrally so no component can move an incident into an illegal state.
var validTransitions = map[IncidentStatus][]IncidentStatus{
	StatusDetected:   {StatusDiagnosing, StatusFailed, StatusEscalated},
	StatusDiagnosing: {StatusDiagnosed, StatusFailed, StatusEscalated},
	StatusDiagnosed:  {StatusFixing, StatusFailed, StatusEscalated},
	StatusFixing:     {StatusFixReady, StatusFailed, StatusEscalated},
	StatusFixReady:   {StatusApplying, StatusFailed, StatusEscalated},
	StatusApplying:   {StatusVerifying, StatusFailed, StatusEscalated},
	StatusVerifying:  {StatusResolved, StatusFailed, StatusEscalated},
	StatusResolved:   {},
	StatusFailed:     {StatusDiagnosing}, // allow a retry from diagnosis
	StatusEscalated:  {StatusFixReady, StatusFailed},
}

// CanTransition reports whether an incident may move from its current
// status to the requested one.
func (i *Incident) CanTransition(to IncidentStatus) bool {
	for _, allowed := range validTransitions[i.Status] {
		if allowed == to {
			return true
		}
	}
	return false
}
