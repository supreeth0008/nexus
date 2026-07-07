// Package config loads and validates the Nexus configuration.
//
// I use Viper for file discovery and environment variable binding, then
// unmarshal into a strongly typed struct so the rest of the codebase
// never touches Viper directly.
package config

import (
	"fmt"
	"net/url"
	"os"
	"strings"

	"github.com/spf13/viper"
)

// Config is the root configuration for the Nexus control plane.
type Config struct {
	Project  ProjectConfig  `mapstructure:"project"`
	Autonomy AutonomyConfig `mapstructure:"autonomy"`
	Database DatabaseConfig `mapstructure:"database"`
	Engine   EngineConfig   `mapstructure:"engine"`
	Targets  []TargetConfig `mapstructure:"targets"`
}

// ProjectConfig identifies the project this Nexus instance manages.
type ProjectConfig struct {
	Name        string `mapstructure:"name"`
	Environment string `mapstructure:"environment"`
}

// AutonomyConfig controls how much freedom Nexus has to act.
type AutonomyConfig struct {
	// Level 0 observes only; 1 recommends via PR; 2 auto-fixes low risk;
	// 3 auto-fixes behind a policy gate; 4 is full autonomy.
	Level int `mapstructure:"level"`
}

// LevelName returns a human-readable name for the autonomy level.
func (a AutonomyConfig) LevelName() string {
	switch a.Level {
	case 0:
		return "observe only"
	case 1:
		return "recommend"
	case 2:
		return "auto-fix low risk"
	case 3:
		return "auto-fix with policy gate"
	case 4:
		return "full autonomy"
	default:
		return "unknown"
	}
}

// DatabaseConfig configures the PostgreSQL connection.
type DatabaseConfig struct {
	DSN string `mapstructure:"dsn"`
}

// RedactedDSN returns the DSN with any password removed, safe for logs
// and status output.
func (d DatabaseConfig) RedactedDSN() string {
	if d.DSN == "" {
		return "(not configured)"
	}
	u, err := url.Parse(d.DSN)
	if err != nil || u.User == nil {
		return d.DSN
	}
	if _, has := u.User.Password(); has {
		u.User = url.UserPassword(u.User.Username(), "REDACTED")
	}
	return u.String()
}

// EngineConfig controls the closed-loop cycle engine.
type EngineConfig struct {
	// CycleInterval is a Go duration string, for example "5m".
	CycleInterval string `mapstructure:"cycle_interval"`
	// HTTPPort is the port for the Nexus HTTP API.
	HTTPPort int `mapstructure:"http_port"`
}

// TargetConfig describes one piece of observed infrastructure.
type TargetConfig struct {
	Name     string `mapstructure:"name"`
	Provider string `mapstructure:"provider"`
	Endpoint string `mapstructure:"endpoint"`
	Region   string `mapstructure:"region"`
}

// Load reads configuration from the given path, or discovers nexus.yaml
// in the working directory when path is empty. Environment variables
// with the NEXUS_ prefix override file values.
func Load(path string) (*Config, error) {
	v := viper.New()

	setDefaults(v)

	v.SetEnvPrefix("NEXUS")
	v.SetEnvKeyReplacer(strings.NewReplacer(".", "_", "-", "_"))
	v.AutomaticEnv()

	// I resolve the config file explicitly rather than letting Viper
	// search: Viper's extensionless search can accidentally match the
	// compiled "nexus" binary in the working directory.
	if path == "" {
		if _, err := os.Stat("nexus.yaml"); err == nil {
			path = "nexus.yaml"
		}
	}

	if path != "" {
		v.SetConfigFile(path)
		if err := v.ReadInConfig(); err != nil {
			return nil, fmt.Errorf("reading config: %w", err)
		}
	}
	// With no config file, defaults apply; commands like init and
	// version work without one.

	var cfg Config
	if err := v.Unmarshal(&cfg); err != nil {
		return nil, fmt.Errorf("parsing config: %w", err)
	}

	if err := Validate(&cfg); err != nil {
		return nil, err
	}

	return &cfg, nil
}
