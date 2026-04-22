//go:build windows
// +build windows

package main

import (
	"syscall"
)

func hideConsoleWindow() {
	// Hide the console window on Windows
	kernel32 := syscall.NewLazyDLL("kernel32.dll")
	user32 := syscall.NewLazyDLL("user32.dll")
	getConsoleWindow := kernel32.NewProc("GetConsoleWindow")
	showWindow := user32.NewProc("ShowWindow")

	hwnd, _, _ := getConsoleWindow.Call()
	if hwnd != 0 {
		showWindow.Call(hwnd, 0) // 0 = SW_HIDE
	}
}
