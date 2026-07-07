package utils

import "runtime"

// These values are injected at build time via -ldflags. I keep the
// defaults meaningful so a plain 'go build' still reports something
// honest.
var (
	version = "v0.1.0-dev"
	commit  = "none"
	date    = "unknown"
)

// Info describes the running build.
type Info struct {
	Version   string
	Commit    string
	Date      string
	GoVersion string
}

// BuildInfo returns the build metadata for the current binary.
func BuildInfo() Info {
	return Info{
		Version:   version,
		Commit:    commit,
		Date:      date,
		GoVersion: runtime.Version(),
	}
}
