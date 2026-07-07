// Nexus is an autonomous infrastructure control plane.
//
// I built this entry point to be intentionally thin: all command wiring
// lives in the cmd package, and all business logic lives under internal.
package main

import (
	"os"

	"github.com/supreeth0008/nexus/cmd"
)

func main() {
	if err := cmd.Execute(); err != nil {
		os.Exit(1)
	}
}
