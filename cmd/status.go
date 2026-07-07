package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
)

var statusCmd = &cobra.Command{
	Use:   "status",
	Short: "Show Nexus system status",
	Long: `Show the current status of the Nexus control plane: loaded
configuration, configured targets, and autonomy level. In Phase 0 this
reports configuration state only; live cycle health arrives with the
engine in later phases.`,
	RunE: func(_ *cobra.Command, _ []string) error {
		fmt.Printf("Project:        %s\n", cfg.Project.Name)
		fmt.Printf("Autonomy level: %d (%s)\n", cfg.Autonomy.Level, cfg.Autonomy.LevelName())
		fmt.Printf("Database:       %s\n", cfg.Database.RedactedDSN())

		if len(cfg.Targets) == 0 {
			fmt.Println("Targets:        No targets configured")
			fmt.Println()
			fmt.Println("Add a target in nexus.yaml under 'targets' to begin observing infrastructure.")
			return nil
		}

		fmt.Printf("Targets:        %d configured\n", len(cfg.Targets))
		for _, t := range cfg.Targets {
			fmt.Printf("  - %s (%s) %s\n", t.Name, t.Provider, t.Endpoint)
		}
		return nil
	},
}

func init() {
	rootCmd.AddCommand(statusCmd)
}
