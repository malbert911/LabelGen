//go:build !windows
// +build !windows

package main

import "fmt"

func writeRawZPLToWindowsPrinter(printerName string, data []byte) error {
	return fmt.Errorf("raw Windows printer write only supported on Windows")
}
