//go:build !windows
// +build !windows

package main

func writeRawZPLToWindowsPrinter(printerName string, data []byte) error {
	return nil
}
