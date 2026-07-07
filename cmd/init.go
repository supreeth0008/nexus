package cmd

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"

	"github.com/supreeth0008/nexus/internal/config"
)

var initName string

var initCmd = &cobra.Command{
	Use:   "init",
	Short: "Scaffold a new Nexus project configuration",
	Long: `Create a nexus.yaml configuration file in the current directory
with sensible defaults. I refuse to overwrite an existing file so a
project configuration is never lost by accident.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		path := "nexus.yaml"
		if _, err := os.Stat(path); err == nil {
			return fmt.Errorf("%s already exists; remove it first if you want to re-initialize", path)
		}

		content := config.DefaultYAML(initName)
		if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
			return fmt.Errorf("writing %s: %w", path, err)
		}

		fmt.Printf("Created %s for project %q\n", path, initName)
		fmt.Println("Next steps:")
		fmt.Println("  1. Review nexus.yaml and adjust the database settings")
		fmt.Println("  2. Run 'nexus status' to verify the configuration loads")
		return nil
	},
}

func init() {
	initCmd.Flags().StringVar(&initName, "name", "my-project", "project name")
	rootCmd.AddCommand(initCmd)
}
