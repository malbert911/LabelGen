package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"
	"sync"
	"time"

	"github.com/getlantern/systray"
	"github.com/rs/cors"
	"gopkg.in/natefinch/lumberjack.v2"
)

var (
	logFile    *lumberjack.Logger
	httpServer *http.Server
	serverMu   sync.Mutex
)

// Printer represents a printer device
type Printer struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	Type        string `json:"type"`
	Connection  string `json:"connection"`
	Status      string `json:"status"`
	Description string `json:"description"`
}

// PrintRequest represents a print job request
type PrintRequest struct {
	PrinterID string                 `json:"printer_id"`
	LabelType string                 `json:"label_type"`
	Data      map[string]interface{} `json:"data"`
	ZPL       string                 `json:"zpl"` // Raw ZPL code (optional, takes precedence)
}

// PrintResponse represents the response from a print request
type PrintResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
	JobID   string `json:"job_id,omitempty"`
	Error   string `json:"error,omitempty"`
}

// PrintersResponse represents the list of available printers
type PrintersResponse struct {
	Success  bool      `json:"success"`
	Printers []Printer `json:"printers"`
}

func GetPrinters(w http.ResponseWriter, r *http.Request) {
	log.Println("GET /printers")
	printers, err := discoverPrinters()
	if err != nil {
		log.Printf("Discovery error: %v", err)
		printers = []Printer{}
	}

	// Always add debug printer for testing
	printers = append(printers, Printer{
		ID:          "debug_file_printer",
		Name:        "DEBUG: Save ZPL to File",
		Type:        "debug",
		Connection:  "File System",
		Status:      "ready",
		Description: "Saves ZPL commands to /tmp/labelgen/ for testing",
	})

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(PrintersResponse{
		Success:  true, // Always succeed even if no real printers
		Printers: printers,
	})
}

func discoverPrinters() ([]Printer, error) {
	switch runtime.GOOS {
	case "windows":
		return discoverWindowsPrinters()
	case "darwin", "linux":
		return discoverCUPSPrinters()
	default:
		return nil, fmt.Errorf("unsupported OS: %s", runtime.GOOS)
	}
}

func discoverWindowsPrinters() ([]Printer, error) {
	if printers, err := discoverWindowsPrintersPowerShell(); err == nil && len(printers) > 0 {
		return printers, nil
	}
	log.Println("PowerShell failed, trying wmic...")
	return discoverWindowsPrintersWMIC()
}

func discoverWindowsPrintersPowerShell() ([]Printer, error) {
	psCmd := `Get-Printer | Select-Object Name,PortName,DriverName,PrinterStatus | ConvertTo-Csv -NoTypeInformation`
	output, err := exec.Command("powershell", "-Command", psCmd).CombinedOutput()
	if err != nil {
		return nil, err
	}

	var printers []Printer
	for i, line := range strings.Split(string(output), "\n") {
		if i == 0 || strings.TrimSpace(line) == "" {
			continue
		}

		fields := parseCSVLine(line)
		if len(fields) < 4 {
			continue
		}

		name := strings.Trim(fields[0], `"`)
		port := strings.Trim(fields[1], `"`)
		driver := strings.Trim(fields[2], `"`)
		statusStr := strings.Trim(fields[3], `"`)

		printers = append(printers, Printer{
			ID:          sanitizePrinterID(name, port),
			Name:        name,
			Type:        detectPrinterType(driver),
			Connection:  getConnectionType(port),
			Status:      normalizeStatus(statusStr),
			Description: fmt.Sprintf("%s (%s)", name, getConnectionType(port)),
		})
	}
	return printers, nil
}

func discoverWindowsPrintersWMIC() ([]Printer, error) {
	output, err := exec.Command("wmic", "printer", "get", "Name,PortName,DriverName", "/format:csv").CombinedOutput()
	if err != nil {
		return nil, err
	}

	var printers []Printer
	for i, line := range strings.Split(string(output), "\n") {
		if i == 0 || strings.TrimSpace(line) == "" {
			continue
		}

		fields := strings.Split(line, ",")
		if len(fields) < 4 {
			continue
		}

		name := strings.TrimSpace(fields[2])
		port := strings.TrimSpace(fields[3])
		driver := strings.TrimSpace(fields[1])

		if name != "" {
			printers = append(printers, Printer{
				ID:          sanitizePrinterID(name, port),
				Name:        name,
				Type:        detectPrinterType(driver),
				Connection:  getConnectionType(port),
				Status:      "ready",
				Description: fmt.Sprintf("%s (%s)", name, getConnectionType(port)),
			})
		}
	}
	return printers, nil
}

func parseCSVLine(line string) []string {
	var fields []string
	var current strings.Builder
	inQuotes := false

	for _, char := range line {
		if char == '"' {
			inQuotes = !inQuotes
			current.WriteRune(char)
		} else if char == ',' && !inQuotes {
			fields = append(fields, current.String())
			current.Reset()
		} else {
			current.WriteRune(char)
		}
	}
	fields = append(fields, current.String())
	return fields
}

func detectPrinterType(driver string) string {
	driver = strings.ToLower(driver)
	thermal := []string{"zebra", "datamax", "sato", "tsc", "godex", "intermec", "honeywell", "citizen", "zpl", "epl"}
	for _, keyword := range thermal {
		if strings.Contains(driver, keyword) {
			return "thermal"
		}
	}
	return "standard"
}

func getConnectionType(port string) string {
	switch {
	case strings.HasPrefix(port, "USB"):
		return "USB"
	case strings.HasPrefix(port, "WSD"):
		return "Network (WSD)"
	case strings.Contains(port, "IP_"), strings.HasPrefix(port, "ipp://"), strings.HasPrefix(port, "http://"):
		return "Network"
	case strings.HasPrefix(port, "COM"), strings.HasPrefix(port, "LPT"):
		return "Serial/Parallel"
	case strings.HasPrefix(port, "lpd://"):
		return "LPD/Network"
	default:
		return "Unknown"
	}
}

func normalizeStatus(status string) string {
	status = strings.ToLower(status)
	switch {
	case strings.Contains(status, "normal"), strings.Contains(status, "idle"), strings.Contains(status, "ready"):
		return "ready"
	case strings.Contains(status, "offline"), strings.Contains(status, "error"), strings.Contains(status, "disabled"):
		return "offline"
	case strings.Contains(status, "printing"), strings.Contains(status, "processing"):
		return "busy"
	default:
		return "unknown"
	}
}

func sanitizePrinterID(name, identifier string) string {
	id := name

	if strings.Contains(identifier, "serial=") {
		if parts := strings.Split(identifier, "serial="); len(parts) > 1 {
			serial := strings.Split(strings.Split(parts[1], "&")[0], "?")[0]
			id = fmt.Sprintf("%s_%s", name, serial)
		}
	} else if identifier != "" {
		uriPart := strings.NewReplacer("usb://", "", "/", "_", "?", "_", "\\", "_", ":", "_").Replace(identifier)
		if len(uriPart) > 20 {
			uriPart = uriPart[:20]
		}
		id = fmt.Sprintf("%s_%s", name, uriPart)
	}

	id = strings.ToLower(strings.NewReplacer(" ", "_", ".", "_").Replace(id))
	if len(id) > 64 {
		id = id[:64]
	}
	return id
}

func discoverCUPSPrinters() ([]Printer, error) {
	output, err := exec.Command("lpstat", "-v").CombinedOutput()
	if err != nil {
		return nil, err
	}

	statusOutput, _ := exec.Command("lpstat", "-p").CombinedOutput()
	statusMap := parsePrinterStatus(string(statusOutput))

	var printers []Printer
	re := regexp.MustCompile(`device for ([^:]+):\s+(.+)`)

	for _, line := range strings.Split(string(output), "\n") {
		if matches := re.FindStringSubmatch(line); len(matches) == 3 {
			name := strings.TrimSpace(matches[1])
			uri := strings.TrimSpace(matches[2])
			status := "unknown"
			if s, ok := statusMap[name]; ok {
				status = s
			}

			printers = append(printers, Printer{
				ID:          sanitizePrinterID(name, uri),
				Name:        name,
				Type:        "thermal",
				Connection:  getConnectionType(uri),
				Status:      status,
				Description: fmt.Sprintf("%s (%s)", name, getConnectionType(uri)),
			})
		}
	}
	return printers, nil
}

func parsePrinterStatus(output string) map[string]string {
	statusMap := make(map[string]string)
	re := regexp.MustCompile(`printer\s+([^\s]+)\s+(is\s+)?(.+)`)

	for _, line := range strings.Split(output, "\n") {
		if matches := re.FindStringSubmatch(line); len(matches) >= 3 {
			statusMap[matches[1]] = normalizeStatus(matches[len(matches)-1])
		}
	}
	return statusMap
}

func Print(w http.ResponseWriter, r *http.Request) {
	log.Println("POST /print")

	var req PrintRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		respondError(w, http.StatusBadRequest, "Invalid request format")
		return
	}

	printerName, err := getPrinterNameByID(req.PrinterID)
	if err != nil {
		respondError(w, http.StatusBadRequest, fmt.Sprintf("Printer not found: %v", err))
		return
	}

	zplData := strings.TrimSpace(req.ZPL)
	if zplData == "" {
		if zplFromData, ok := req.Data["zpl"].(string); ok {
			zplData = strings.TrimSpace(zplFromData)
		}
	}
	if zplData == "" {
		respondError(w, http.StatusBadRequest, "No ZPL data provided")
		return
	}

	if err := sendZPLToPrinter(printerName, zplData); err != nil {
		log.Printf("Print failed: %v", err)
		respondError(w, http.StatusInternalServerError, fmt.Sprintf("Print failed: %v", err))
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(PrintResponse{
		Success: true,
		Message: fmt.Sprintf("Sent %d bytes to %s", len(zplData), printerName),
		JobID:   fmt.Sprintf("job-%d", time.Now().Unix()),
	})
}

func respondError(w http.ResponseWriter, code int, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(PrintResponse{
		Success: false,
		Error:   message,
	})
}

func getPrinterNameByID(printerID string) (string, error) {
	// Handle debug printer
	if printerID == "debug_file_printer" {
		return "DEBUG: Save ZPL to File", nil
	}

	printers, err := discoverPrinters()
	if err != nil {
		return "", err
	}
	for _, p := range printers {
		if p.ID == printerID {
			return p.Name, nil
		}
	}
	return "", fmt.Errorf("printer ID '%s' not found", printerID)
}

func sendZPLToPrinter(printerName, zplData string) error {
	// Handle debug printer
	if printerName == "DEBUG: Save ZPL to File" {
		return saveZPLToDebugFile(zplData)
	}

	switch runtime.GOOS {
	case "windows":
		return sendZPLToPrinterWindows(printerName, zplData)
	case "darwin", "linux":
		return sendZPLToPrinterCUPS(printerName, zplData)
	default:
		return fmt.Errorf("unsupported OS: %s", runtime.GOOS)
	}
}

func sendZPLToPrinterWindows(printerName, zplData string) error {
	if err := writeRawZPLToWindowsPrinter(printerName, []byte(zplData)); err != nil {
		return fmt.Errorf("raw spooler print failed: %w", err)
	}
	log.Printf("Printed %d bytes to %s (raw spooler)", len(zplData), printerName)
	return nil
}

func sendZPLToPrinterCUPS(printerName, zplData string) error {
	tmpFile, err := os.CreateTemp("", "label-*.zpl")
	if err != nil {
		return err
	}
	defer os.Remove(tmpFile.Name())

	if _, err := tmpFile.WriteString(zplData); err != nil {
		tmpFile.Close()
		return err
	}
	tmpFile.Close()

	var stderr bytes.Buffer
	cmd := exec.Command("lpr", "-P", printerName, "-o", "raw", tmpFile.Name())
	cmd.Stderr = &stderr

	if err := cmd.Run(); err != nil {
		return fmt.Errorf("lpr failed: %w (%s)", err, stderr.String())
	}
	log.Printf("Printed to %s", printerName)
	return nil
}

func saveZPLToDebugFile(zplData string) error {
	// Create debug directory
	debugDir := "/tmp/labelgen"
	if runtime.GOOS == "windows" {
		debugDir = os.TempDir() + "\\labelgen"
	}

	if err := os.MkdirAll(debugDir, 0755); err != nil {
		return fmt.Errorf("failed to create debug directory: %w", err)
	}

	// Create file with timestamp
	filename := fmt.Sprintf("%s/label-%s.zpl", debugDir, time.Now().Format("20060102-150405.000"))
	if err := os.WriteFile(filename, []byte(zplData), 0644); err != nil {
		return fmt.Errorf("failed to write debug file: %w", err)
	}

	log.Printf("✓ Saved ZPL to %s (%d bytes)", filename, len(zplData))
	return nil
}

// HealthCheck endpoint
func HealthCheck(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":  "healthy",
		"service": "labelgen-printer-bridge",
		"version": "1.0.0",
	})
}

func setupLogger() error {
	exePath, err := os.Executable()
	if err != nil {
		return fmt.Errorf("failed to get executable path: %w", err)
	}

	logDir := filepath.Dir(exePath)
	logPath := filepath.Join(logDir, "labelgen-bridge.log")

	logFile = &lumberjack.Logger{
		Filename:   logPath,
		MaxSize:    1, // 1 MB
		MaxBackups: 3,
		MaxAge:     7, // 7 days
		Compress:   true,
	}

	// Create a multi-writer that writes to both file and stdout
	mw := io.MultiWriter(logFile, os.Stdout)
	log.SetOutput(mw)
	log.SetFlags(log.Ldate | log.Ltime | log.Lshortfile)

	return nil
}

func startHTTPServer() error {
	mux := http.NewServeMux()

	// Register routes
	mux.HandleFunc("/health", HealthCheck)
	mux.HandleFunc("/printers", GetPrinters)
	mux.HandleFunc("/print", Print)

	// Setup CORS to allow requests from Django (localhost:8001)
	c := cors.New(cors.Options{
		AllowedOrigins:   []string{"http://localhost:8001", "http://127.0.0.1:8001", "http://10.127.205.187:8001", "http://10.127.205.113:8001"},
		AllowedMethods:   []string{"GET", "POST", "OPTIONS"},
		AllowedHeaders:   []string{"Content-Type", "Accept"},
		AllowCredentials: true,
	})

	handler := c.Handler(mux)

	port := ":5001"
	httpServer = &http.Server{
		Addr:    port,
		Handler: handler,
	}

	log.Printf("🖨️  Starting HTTP server on http://localhost%s", port)
	go func() {
		if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Printf("HTTP server error: %v", err)
		}
	}()

	return nil
}

func createTrayIcon() []byte {
	// Create a minimal 16x16 PNG icon (white square for printer icon representation)
	// This is a very small valid PNG file
	return []byte{
		0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
		0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00, 0x10,
		0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x91, 0x68, 0x36, 0x00, 0x00, 0x00,
		0x1F, 0x74, 0x45, 0x58, 0x74, 0x53, 0x6F, 0x66, 0x74, 0x77, 0x61, 0x72,
		0x65, 0x00, 0x41, 0x64, 0x6F, 0x62, 0x65, 0x20, 0x49, 0x6D, 0x61, 0x67,
		0x65, 0x52, 0x65, 0x61, 0x64, 0x79, 0x71, 0xC9, 0x65, 0x3C, 0x00, 0x00,
		0x00, 0x2A, 0x49, 0x44, 0x41, 0x54, 0x78, 0xDA, 0xEC, 0xC1, 0x01, 0x0D,
		0x00, 0x00, 0x00, 0xC2, 0xA0, 0xF5, 0x4F, 0xED, 0x61, 0x0D, 0xA0, 0x00,
		0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
		0x00, 0x00, 0x3C, 0x7E, 0x41, 0x8B, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45,
		0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82,
	}
}

func onReady() {
	if runtime.GOOS != "windows" {
		systray.SetIcon(createTrayIcon())
	}
	systray.SetTitle("LabelGen Bridge")
	systray.SetTooltip("LabelGen Printer Bridge - Running")

	// Create menu items
	mStatus := systray.AddMenuItem("Status: Running", "Server Status")
	mStatus.Disable()

	systray.AddSeparator()

	mViewLogs := systray.AddMenuItem("View Logs", "Open log file")
	mOpenServer := systray.AddMenuItem("Open Web Interface", "Open http://localhost:5001")

	systray.AddSeparator()

	mQuit := systray.AddMenuItem("Quit", "Quit LabelGen Bridge")

	// Handle menu clicks
	go func() {
		for {
			select {
			case <-mViewLogs.ClickedCh:
				openLogFile()
			case <-mOpenServer.ClickedCh:
				openWebInterface()
			case <-mQuit.ClickedCh:
				log.Println("Quit requested from tray menu")
				systray.Quit()
				return
			}
		}
	}()
}

func openLogFile() {
	if logFile == nil {
		log.Println("Log file not available")
		return
	}

	logPath := logFile.Filename
	log.Printf("Opening log file: %s", logPath)

	switch runtime.GOOS {
	case "windows":
		exec.Command("cmd", "/c", "start", logPath).Run()
	case "darwin":
		exec.Command("open", logPath).Run()
	case "linux":
		exec.Command("xdg-open", logPath).Run()
	}
}

func openWebInterface() {
	url := "http://localhost:5001/health"
	log.Printf("Opening web interface: %s", url)

	switch runtime.GOOS {
	case "windows":
		exec.Command("cmd", "/c", "start", url).Run()
	case "darwin":
		exec.Command("open", url).Run()
	case "linux":
		exec.Command("xdg-open", url).Run()
	}
}

func onExit() {
	log.Println("Shutting down...")

	serverMu.Lock()
	if httpServer != nil {
		if err := httpServer.Close(); err != nil {
			log.Printf("Error closing HTTP server: %v", err)
		}
	}
	serverMu.Unlock()

	if logFile != nil {
		logFile.Close()
	}
}

func main() {
	// Initialize logger early
	if err := setupLogger(); err != nil {
		fmt.Fprintf(os.Stderr, "Failed to setup logger: %v\n", err)
		os.Exit(1)
	}

	log.Println("════════════════════════════════════════════════════════════")
	log.Println("🖨️  LabelGen Printer Bridge - System Tray Edition")
	log.Printf("📋 Starting on %s", time.Now().Format("2006-01-02 15:04:05"))
	log.Printf("📋 Operating System: %s", runtime.GOOS)
	log.Println("════════════════════════════════════════════════════════════")

	// Hide console window on Windows
	hideConsoleWindow()

	// Start HTTP server
	if err := startHTTPServer(); err != nil {
		log.Fatalf("Failed to start HTTP server: %v", err)
	}

	// Log available endpoints
	log.Println("📋 Available endpoints:")
	log.Println("   GET  /health   - Health check")
	log.Println("   GET  /printers - List available printers")
	log.Println("   POST /print    - Send print job")
	log.Println("════════════════════════════════════════════════════════════")

	// Start system tray application
	systray.Run(onReady, onExit)
}
