package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
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

// GetPrinters returns a list of available printers (stubbed)
func GetPrinters(w http.ResponseWriter, r *http.Request) {
	log.Println("GET /printers - Discovering printers...")

	// Stubbed printers for testing
	printers := []Printer{
		{
			ID:          "zebra-zd421",
			Name:        "Zebra ZD421",
			Type:        "thermal",
			Connection:  "USB",
			Status:      "ready",
			Description: "2-inch thermal label printer",
		},
		{
			ID:          "zebra-zt230",
			Name:        "Zebra ZT230",
			Type:        "thermal",
			Connection:  "Network (192.168.1.100)",
			Status:      "ready",
			Description: "4-inch industrial thermal printer",
		},
	}

	response := PrintersResponse{
		Success:  true,
		Printers: printers,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// Print handles print requests (stubbed)
func Print(w http.ResponseWriter, r *http.Request) {
	log.Println("POST /print - Received print request")

	var req PrintRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		log.Printf("Error decoding request: %v", err)
		response := PrintResponse{
			Success: false,
			Error:   "Invalid request format",
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(response)
		return
	}

	// Validate printer ID
	validPrinters := map[string]bool{
		"zebra-zd421": true,
		"zebra-zt230": true,
	}

	if !validPrinters[req.PrinterID] {
		log.Printf("Invalid printer ID: %s", req.PrinterID)
		response := PrintResponse{
			Success: false,
			Error:   fmt.Sprintf("Unknown printer: %s", req.PrinterID),
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(response)
		return
	}

	// Generate a job ID
	jobID := fmt.Sprintf("job-%d", time.Now().Unix())

	// Log the print request (stub)
	log.Printf("Print job %s: Printer=%s, LabelType=%s, Data=%+v",
		jobID, req.PrinterID, req.LabelType, req.Data)

	// Simulate successful print
	response := PrintResponse{
		Success: true,
		Message: fmt.Sprintf("Print job sent to %s", req.PrinterID),
		JobID:   jobID,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
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
	log.Println("📋 Available endpoints:")
	log.Println("   GET  /health   - Health check")
	log.Println("   GET  /printers - List available printers")
	log.Println("   POST /print    - Send print job")

	if err := http.ListenAndServe(port, handler); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}
