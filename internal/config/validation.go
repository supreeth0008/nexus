package config

import (
	"fmt"
	"time"
)

// validProviders lists the target providers Nexus understands today.
var validProviders = map[string]bool{
	"aws":        true,
	"azure":      true,
	"gcp":        true,
	"kubernetes": true,
	"localstack": true,
}

// Validate checks a Config for structural problems. I validate eagerly
// at load time so every command can trust the configuration it receives.
func Validate(cfg *Config) error {
	if cfg.Project.Name == "" {
		return fmt.Errorf("project.name must not be empty")
	}

	if cfg.Autonomy.Level < 0 || cfg.Autonomy.Level > 4 {
		return fmt.Errorf("autonomy.level must be between 0 and 4, got %d", cfg.Autonomy.Level)
	}

	if cfg.Engine.CycleInterval != "" {
		if _, err := time.ParseDuration(cfg.Engine.CycleInterval); err != nil {
			return fmt.Errorf("engine.cycle_interval %q is not a valid duration: %w", cfg.Engine.CycleInterval, err)
		}
	}

	if cfg.Engine.HTTPPort < 1 || cfg.Engine.HTTPPort > 65535 {
		return fmt.Errorf("engine.http_port must be between 1 and 65535, got %d", cfg.Engine.HTTPPort)
	}

	seen := map[string]bool{}
	for i, t := range cfg.Targets {
		if t.Name == "" {
			return fmt.Errorf("targets[%d].name must not be empty", i)
		}
		if seen[t.Name] {
			return fmt.Errorf("duplicate target name %q", t.Name)
		}
		seen[t.Name] = true

		if !validProviders[t.Provider] {
			return fmt.Errorf("targets[%d] (%s): unknown provider %q", i, t.Name, t.Provider)
		}
		if t.Endpoint == "" {
			return fmt.Errorf("targets[%d] (%s): endpoint must not be empty", i, t.Name)
		}
	}

	return nil
}
