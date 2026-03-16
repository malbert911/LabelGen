//go:build windows
// +build windows

package main

import (
	"fmt"
	"syscall"
	"unsafe"
)

func writeRawZPLToWindowsPrinter(printerName string, data []byte) error {
	spooler := syscall.NewLazyDLL("winspool.drv")
	openPrinter := spooler.NewProc("OpenPrinterW")
	closePrinter := spooler.NewProc("ClosePrinter")
	startDocPrinter := spooler.NewProc("StartDocPrinterW")
	endDocPrinter := spooler.NewProc("EndDocPrinter")
	startPagePrinter := spooler.NewProc("StartPagePrinter")
	endPagePrinter := spooler.NewProc("EndPagePrinter")
	writePrinter := spooler.NewProc("WritePrinter")

	var handle uintptr
	namePtr, err := syscall.UTF16PtrFromString(printerName)
	if err != nil {
		return err
	}
	r1, _, err := openPrinter.Call(uintptr(unsafe.Pointer(namePtr)), uintptr(unsafe.Pointer(&handle)), 0)
	if r1 == 0 {
		return fmt.Errorf("OpenPrinter failed: %v", err)
	}
	defer closePrinter.Call(handle)

	docNamePtr, _ := syscall.UTF16PtrFromString("LabelGen ZPL")
	dataTypePtr, _ := syscall.UTF16PtrFromString("RAW")
	docInfo := struct {
		pDocName    *uint16
		pOutputFile *uint16
		pDatatype   *uint16
	}{
		pDocName:    docNamePtr,
		pOutputFile: nil,
		pDatatype:   dataTypePtr,
	}

	r1, _, err = startDocPrinter.Call(handle, 1, uintptr(unsafe.Pointer(&docInfo)))
	if r1 == 0 {
		return fmt.Errorf("StartDocPrinter failed: %v", err)
	}
	defer endDocPrinter.Call(handle)

	r1, _, err = startPagePrinter.Call(handle)
	if r1 == 0 {
		return fmt.Errorf("StartPagePrinter failed: %v", err)
	}
	defer endPagePrinter.Call(handle)

	var written uint32
	r1, _, err = writePrinter.Call(handle, uintptr(unsafe.Pointer(&data[0])), uintptr(len(data)), uintptr(unsafe.Pointer(&written)))
	if r1 == 0 {
		return fmt.Errorf("WritePrinter failed: %v", err)
	}
	if int(written) != len(data) {
		return fmt.Errorf("WritePrinter wrote %d/%d bytes", written, len(data))
	}

	return nil
}
