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
	"regexp"
	"runtime"
	"strings"
	"time"

	"github.com/rs/cors"
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

	zplData, ok := req.Data["zpl"].(string)
	if !ok || zplData == "" {
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
	file, err := os.OpenFile(fmt.Sprintf(`\\.\%s`, printerName), os.O_WRONLY, 0)
	if err != nil {
		return fmt.Errorf("failed to open printer: %w", err)
	}
	defer file.Close()

	if _, err := io.WriteString(file, zplData); err != nil {
		return fmt.Errorf("failed to write: %w", err)
	}
	log.Printf("Printed %d bytes to %s", len(zplData), printerName)
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

func main() {
	mux := http.NewServeMux()

	// Register routes
	mux.HandleFunc("/health", HealthCheck)
	mux.HandleFunc("/printers", GetPrinters)
	mux.HandleFunc("/print", Print)

	// Setup CORS to allow requests from Django (localhost:8001)
	c := cors.New(cors.Options{
		AllowedOrigins:   []string{"http://localhost:8001", "http://127.0.0.1:8001"},
		AllowedMethods:   []string{"GET", "POST", "OPTIONS"},
		AllowedHeaders:   []string{"Content-Type", "Accept"},
		AllowCredentials: true,
	})

	handler := c.Handler(mux)

	port := ":5001"
	log.Printf("🖨️  LabelGen Printer Bridge starting on http://localhost%s", port)
	log.Printf("📋 Operating System: %s", runtime.GOOS)
	log.Println("📋 Available endpoints:")
	log.Println("   GET  /health   - Health check")
	log.Println("   GET  /printers - List available printers")
	log.Println("   POST /print    - Send print job")

	if err := http.ListenAndServe(port, handler); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}
