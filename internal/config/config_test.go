package config

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestLoadDefaults(t *testing.T) {
	dir := t.TempDir()
	chdir(t, dir)

	cfg, err := Load("")
	if err != nil {
		t.Fatalf("Load with no file should use defaults, got error: %v", err)
	}
	if cfg.Project.Name != "nexus-project" {
		t.Errorf("default project name = %q, want nexus-project", cfg.Project.Name)
	}
	if cfg.Autonomy.Level != 0 {
		t.Errorf("default autonomy level = %d, want 0", cfg.Autonomy.Level)
	}
	if cfg.Engine.HTTPPort != 8080 {
		t.Errorf("default http port = %d, want 8080", cfg.Engine.HTTPPort)
	}
}

func TestLoadFromFile(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "nexus.yaml")
	content := `
project:
  name: test-project
autonomy:
  level: 2
targets:
  - name: demo
    provider: kubernetes
    endpoint: https://localhost:6443
`
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}

	cfg, err := Load(path)
	if err != nil {
		t.Fatalf("Load: %v", err)
	}
	if cfg.Project.Name != "test-project" {
		t.Errorf("project name = %q, want test-project", cfg.Project.Name)
	}
	if cfg.Autonomy.Level != 2 {
		t.Errorf("autonomy level = %d, want 2", cfg.Autonomy.Level)
	}
	if len(cfg.Targets) != 1 || cfg.Targets[0].Name != "demo" {
		t.Errorf("targets = %+v, want one target named demo", cfg.Targets)
	}
}

func TestValidateRejectsBadAutonomy(t *testing.T) {
	cfg := &Config{
		Project:  ProjectConfig{Name: "x"},
		Autonomy: AutonomyConfig{Level: 7},
		Engine:   EngineConfig{HTTPPort: 8080},
	}
	if err := Validate(cfg); err == nil {
		t.Error("expected error for autonomy level 7, got nil")
	}
}

func TestValidateRejectsUnknownProvider(t *testing.T) {
	cfg := &Config{
		Project:  ProjectConfig{Name: "x"},
		Autonomy: AutonomyConfig{Level: 0},
		Engine:   EngineConfig{HTTPPort: 8080},
		Targets: []TargetConfig{
			{Name: "bad", Provider: "digitalocean", Endpoint: "http://x"},
		},
	}
	if err := Validate(cfg); err == nil {
		t.Error("expected error for unknown provider, got nil")
	}
}

func TestValidateRejectsDuplicateTargets(t *testing.T) {
	cfg := &Config{
		Project:  ProjectConfig{Name: "x"},
		Autonomy: AutonomyConfig{Level: 0},
		Engine:   EngineConfig{HTTPPort: 8080},
		Targets: []TargetConfig{
			{Name: "a", Provider: "aws", Endpoint: "http://x"},
			{Name: "a", Provider: "gcp", Endpoint: "http://y"},
		},
	}
	if err := Validate(cfg); err == nil {
		t.Error("expected error for duplicate target names, got nil")
	}
}

func TestRedactedDSN(t *testing.T) {
	d := DatabaseConfig{DSN: "postgres://nexus:supersecret@localhost:5432/nexus"}
	got := d.RedactedDSN()
	if strings.Contains(got, "supersecret") {
		t.Errorf("RedactedDSN leaked the password: %s", got)
	}
	if !strings.Contains(got, "REDACTED") {
		t.Errorf("RedactedDSN should contain REDACTED, got %s", got)
	}
}

func TestAutonomyLevelNames(t *testing.T) {
	cases := map[int]string{
		0: "observe only",
		1: "recommend",
		4: "full autonomy",
		9: "unknown",
	}
	for level, want := range cases {
		got := AutonomyConfig{Level: level}.LevelName()
		if got != want {
			t.Errorf("LevelName(%d) = %q, want %q", level, got, want)
		}
	}
}

// chdir changes into dir for the duration of the test.
func chdir(t *testing.T, dir string) {
	t.Helper()
	old, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	if err := os.Chdir(dir); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = os.Chdir(old) })
}
