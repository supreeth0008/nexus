// Package cmd defines the Nexus command line interface.
//
// I follow the standard Cobra plus Viper layout used across the
// cloud-native ecosystem: a root command that loads configuration and
// sets up logging, with subcommands registered in their own files.
package cmd

import (
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"

	"github.com/supreeth0008/nexus/internal/config"
	"github.com/supreeth0008/nexus/internal/utils"
)

var (
	cfgFile   string
	logLevel  string
	logFormat string

	// cfg holds the loaded configuration for the lifetime of a command.
	cfg *config.Config
)

// rootCmd is the base command that all subcommands attach to.
var rootCmd = &cobra.Command{
	Use:   "nexus",
	Short: "Nexus is an autonomous infrastructure control plane",
	Long: `Nexus observes multi-cloud infrastructure, detects anomalies,
diagnoses root causes, generates infrastructure-as-code fixes, validates
them in shadow environments, applies them through GitOps pull requests,
verifies recovery, and learns from every incident.

This build covers Phase 0: CLI scaffolding, configuration loading,
structured logging, data models, and the database layer.`,
	SilenceUsage:  true,
	SilenceErrors: true,
	PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
		utils.InitLogger(logLevel, logFormat)

		loaded, err := config.Load(cfgFile)
		if err != nil {
			return fmt.Errorf("loading configuration: %w", err)
		}
		cfg = loaded
		return nil
	},
}

// Execute runs the root command. I keep this as the single entry point
// so main.go stays free of CLI details.
func Execute() error {
	err := rootCmd.Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
	}
	return err
}

func init() {
	rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "path to config file (default ./nexus.yaml)")
	rootCmd.PersistentFlags().StringVar(&logLevel, "log-level", "info", "log level: debug, info, warn, error")
	rootCmd.PersistentFlags().StringVar(&logFormat, "log-format", "text", "log format: text or json")

	viper.SetEnvPrefix("NEXUS")
	viper.SetEnvKeyReplacer(strings.NewReplacer(".", "_", "-", "_"))
	viper.AutomaticEnv()
}
