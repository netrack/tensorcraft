package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

func main() {
	cmd := cobra.Command{
		Use:   "tensorcraft [OPTIONS] COMMAND [ARG...]",
		Short: "Inference server for ONNX models",
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println("go")
		},
	}

	err := cmd.Execute()
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
