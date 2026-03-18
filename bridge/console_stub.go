//go:build !windows
// +build !windows

package main

// hideConsoleWindow is a no-op on non-Windows systems
func hideConsoleWindow() {
	// Windows console hiding is only needed on Windows
}
