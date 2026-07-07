package model

import "time"

// Policy is an OPA policy governing autonomous actions.
type Policy struct {
	ID          string      `json:"id" db:"id"`
	Name        string      `json:"name" db:"name"`
	Description string      `json:"description" db:"description"`
	Rego        string      `json:"rego" db:"rego"`
	Scope       PolicyScope `json:"scope" db:"scope"`
	Autonomy    int         `json:"autonomy" db:"autonomy"` // maximum autonomy level this policy permits
	Enabled     bool        `json:"enabled" db:"enabled"`
	Version     int         `json:"version" db:"version"`
	CreatedAt   time.Time   `json:"created_at" db:"created_at"`
	UpdatedAt   time.Time   `json:"updated_at" db:"updated_at"`
}

// PolicyScope narrows where a policy applies. Empty slices mean "all".
type PolicyScope struct {
	IncidentTypes []IncidentType `json:"incident_types,omitempty"`
	Targets       []string       `json:"targets,omitempty"`
	Providers     []string       `json:"providers,omitempty"`
	TimeWindow    string         `json:"time_window,omitempty"` // for example "09:00-17:00" or "always"
}

// PolicyDecision is the outcome of evaluating a policy gate.
type PolicyDecision string

const (
	DecisionAllow           PolicyDecision = "allow"
	DecisionDeny            PolicyDecision = "deny"
	DecisionRequireApproval PolicyDecision = "require_approval"
)
