package main

import (
	"fmt"
	"hooks/installer"
	"hooks/rest"
	"os"

	"github.com/spf13/cobra"
	"github.com/syncloud/golib/log"
)

func main() {
	logger := log.Logger()

	var rootCmd = &cobra.Command{
		Use:          "webui",
		SilenceUsage: true,
	}

	rootCmd.AddCommand(&cobra.Command{
		Use:  "unix [socket]",
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			return rest.NewServer(installer.New(logger), args[0], logger).Start()
		},
	})

	err := rootCmd.Execute()
	if err != nil {
		fmt.Print(err)
		os.Exit(1)
	}
}
