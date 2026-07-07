package model

import "time"

// Target is a piece of infrastructure that Nexus observes.
type Target struct {
	ID        string        `json:"id" db:"id"`
	Name      string        `json:"name" db:"name"`
	Provider  CloudProvider `json:"provider" db:"provider"`
	Regions   []string      `json:"regions" db:"regions"`
	Endpoint  string        `json:"endpoint" db:"endpoint"`
	Auth      TargetAuth    `json:"auth" db:"auth"`
	Status    TargetStatus  `json:"status" db:"status"`
	CreatedAt time.Time     `json:"created_at" db:"created_at"`
	UpdatedAt time.Time     `json:"updated_at" db:"updated_at"`
}

// TargetAuth describes how Nexus authenticates to a target. Credentials
// themselves never live here; only the method and non-secret hints.
type TargetAuth struct {
	Method  string `json:"method"` // env, iam, oidc, static
	Profile string `json:"profile,omitempty"`
	Region  string `json:"region,omitempty"`
}

// CloudProvider identifies the platform backing a target.
type CloudProvider string

const (
	ProviderAWS        CloudProvider = "aws"
	ProviderAzure      CloudProvider = "azure"
	ProviderGCP        CloudProvider = "gcp"
	ProviderK8s        CloudProvider = "kubernetes"
	ProviderLocalStack CloudProvider = "localstack"
)

// TargetStatus reflects connectivity health for a target.
type TargetStatus string

const (
	TargetStatusActive      TargetStatus = "active"
	TargetStatusUnreachable TargetStatus = "unreachable"
	TargetStatusDisabled    TargetStatus = "disabled"
)
