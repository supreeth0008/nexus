package cmd

import (
	"fmt"

	"github.com/spf13/cobra"

	"github.com/supreeth0008/nexus/internal/utils"
)

var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Print the Nexus version",
	Long:  "Print the Nexus version, commit hash, and build date.",
	Run: func(_ *cobra.Command, _ []string) {
		info := utils.BuildInfo()
		fmt.Printf("Nexus %s\n", info.Version)
		fmt.Printf("  commit:     %s\n", info.Commit)
		fmt.Printf("  built:      %s\n", info.Date)
		fmt.Printf("  go version: %s\n", info.GoVersion)
	},
}

func init() {
	rootCmd.AddCommand(versionCmd)
}
