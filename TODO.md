# LabelGen Project Roadmap

## Project Status (Updated: Feb 9, 2026)

**Phases 1-5**: ✅ Complete  
**Phase 6**: 📋 Ready to Start (Testing & Deployment)

---

## Phase 1: Core Foundation ✅ COMPLETE (Completed: Jan 2026)

### Achievements
- Django 6.0.2 project initialized with Python 3.14.3
- SQLite database with migrations applied
- Bulma.io 1.0.0 CSS framework integrated
- Models created: Product, SerialNumber, Config
- Django admin configured (now hidden from users)
- Monorepo structure: backend/ and bridge/ directories

---

## Phase 2: Core Business Logic ✅ COMPLETE (Completed: Jan 2026)

### Achievements
- **SerialNumberGenerator**: Atomic serial generation with `select_for_update()`
- **BulkScanParser**: Parse alternating part/quantity scans
- **BulkGenerationService**: Orchestrate bulk generation workflow
- Auto-product creation with NULL UPC
- Denormalized UPC in SerialNumber for fast printing
- Thread-safe serial increment prevents collisions

---

## Phase 3: User Interface Pages ✅ COMPLETE (Completed: Feb 7, 2026)

### Pages Implemented
- [x] **Home Page** (`/`) - Feature cards with navigation
- [x] **Bulk Generation** (`/generate/`)
  - Hands-free scanning with auto-focus chain
  - Dynamic rows (always one empty row ahead)
  - Real-time serial range calculation
  - requestAnimationFrame for reliable focus management
- [x] **Box Label** (`/box-label/`)
  - Serial number lookup
  - Display part number and UPC
- [x] **Reprint** (`/reprint/`)
  - Serial number search and reprint
- [x] **Printer Settings** (`/printer-settings/`)
  - Browser localStorage for per-client config
  - Two printer types: serial and box
  - Connection status indicator
  - Fetches printers from bridge
- [x] **Admin Login** (`/admin-login/`)
  - Session-based authentication
  - Auto-logout when navigating away
- [x] **Admin UPC Management** (`/admin-upc/`)
  - Serial number configuration (digits, next serial)
  - Password change form (separate from config)
  - CSV upload with template download
  - Manual UPC editing with AJAX save
  - Hidden Django admin interface

### UI/UX Features
- [x] Dark mode with system preference detection
- [x] Theme toggle with localStorage persistence
- [x] Enhanced navigation bar with all main features
- [x] Printer bridge status indicator (green/red chip)
- [x] Mobile-responsive burger menu
- [x] Comprehensive dark mode CSS for Bulma components

---

## Phase 4: Go Printer Bridge ✅ COMPLETE (Completed: Feb 9, 2026)

**Status**: 100% Complete  
**Purpose**: Local service to communicate with physical printers

### Completed ✅
- [x] Set up Go project in `bridge/` directory
- [x] Implement HTTP server on localhost:5001
- [x] Create `/health` endpoint for status checks
- [x] Create `/printers` endpoint with **real printer discovery**
  - [x] Windows: PowerShell Get-Printer + wmic fallback
  - [x] macOS/Linux: CUPS lpstat integration
  - [x] Detects USB, Network (TCP/IP), Network (WSD) printers
  - [x] Identifies thermal printers by driver keywords
  - [x] Creates unique IDs for duplicate printer models (name + port/serial)
  - [x] Returns printer status (ready/offline/busy)
- [x] Create `/print` endpoint with **real printing**
  - [x] Windows: Direct write to `\\.\PrinterName`
  - [x] macOS/Linux: CUPS `lpr -o raw`
  - [x] Accepts ZPL in data.zpl field
  - [x] Returns job ID
  - [x] Full error handling
- [x] Add CORS support for Django frontend
- [x] Cross-platform detection (runtime.GOOS)
- [x] Comprehensive error handling and logging
- [x] Code cleanup (432 lines, production-ready)

---

## Phase 4.5: ZPL Label Templates ✅ COMPLETE (Completed: Feb 9, 2026)

**Purpose**: Editable ZPL templates for label printing

### Completed ✅
- [x] Add ZPL template fields to Config model
- [x] Create migrations for template fields
- [x] Create LabelTemplateForm for admin editing
- [x] Add template editor to admin_upc.html with preview
- [x] Implement Labelary API integration for ZPL→PNG preview
- [x] Create default ZPL templates (4x2" serial, 4x3" box)
- [x] Add /api/generate-label-zpl/ endpoint
- [x] Variable substitution: {{serial}}, {{part}}, {{upc_full}}, {{upc_11_digits}}
- [x] UPC-A barcode implementation (11-digit format)

---

## Phase 5: UI Print Integration ✅ COMPLETE (Completed: Feb 9, 2026)

**Status**: 100% Complete  
**Purpose**: Add print buttons and full integration to UI pages

### Achievements ✅
- [x] Architecture clarified: Browser orchestrates between Django (ZPL gen) and Bridge (printing)
- [x] localStorage keys include Django URL for multi-server support
- [x] Created PrinterBridge JavaScript utility in base.html
  - [x] getPrinters() with 5-second timeout and error handling
  - [x] printLabel() with silent mode parameter (4th param)
  - [x] printBatch() for bulk printing without notification spam
  - [x] getSelectedPrinter() for localStorage retrieval
- [x] Updated bulk_generate.html with full print integration
  - [x] Single-click generate+print workflow
  - [x] Auto-reset form after printing
  - [x] Spacebar keyboard shortcut
  - [x] Silent batch printing
  - [x] Next Serial display updates after generation
  - [x] Code cleanup: removed dead code, extracted constants, arrow functions
- [x] Updated box_label.html with print integration
  - [x] Enter/Tab key support for barcode scanners
  - [x] \"Lookup and Print\" button
  - [x] Auto-print after lookup
  - [x] Auto-reset for continuous scanning
- [x] Updated reprint.html with print button
- [x] Updated printer_settings.html with timeout handling
- [x] Debug printer implementation
  - [x] Always included in printer list
  - [x] Saves ZPL to /tmp/labelgen/ (macOS/Linux) or %TEMP%\\labelgen (Windows)
  - [x] Timestamped filenames for easy tracking
- [x] Error handling for bridge connectivity
- [x] Loading states and visual feedback
- [x] Cross-platform Windows .exe compilation tested

### Code Quality Improvements ✅
- Removed ~100 lines of dead code from bulk_generate.html
- Extracted BUTTON_DEFAULT_HTML constant (DRY principle)
- Simplified checkGenerateButton() with Array.some()
- Converted to arrow functions where appropriate
- Added section comments for code organization
- Added JSDoc comments to key functions
- Reduced bulk_generate.html from 491 to ~400 lines

---

## Phase 6: Testing & Deployment 📋 READY TO START

**Status**: Not Started  
**Purpose**: Ensure reliability and production readiness

### Priority Tasks
- [ ] **Hardware Testing**
  - [ ] Test with actual Datamax O'Neil E-4204B printer
  - [ ] Verify ZPL output quality and label dimensions
  - [ ] Test barcode scannability (Code 128 and UPC-A)
  - [ ] Validate 4x2" serial labels and 4x3" box labels
  - [ ] Test complete workflow: scan → generate → print → verify
- [ ] **Windows Deployment**
  - [ ] Compile Go bridge: `GOOS=windows GOARCH=amd64 go build -o bridge.exe`
  - [ ] Test bridge.exe on Windows workstation
  - [ ] Verify debug printer works on Windows (%TEMP%\\labelgen)
  - [ ] Test real printer discovery on Windows (PowerShell + wmic)
  - [ ] Create Windows deployment guide
- [ ] **Multi-User Testing**
  - [ ] Test concurrent serial generation (verify no collisions)
  - [ ] Verify localStorage printer selection works per workstation
  - [ ] Test multiple workstations printing simultaneously
- [ ] **Documentation**
  - [ ] User manual for warehouse staff (bulk generation, box labels, reprint)
  - [ ] Admin guide (UPC management, ZPL templates, serial config)
  - [ ] IT deployment guide (Django + Bridge setup, network requirements)
  - [ ] Printer setup and troubleshooting guide

### Optional Polish
- [ ] Add helpful tooltips for first-time users
- [ ] Consider audio feedback for successful scans
- [ ] Add keyboard shortcut reference page
- [ ] Print job history view
- [ ] CSV export of serial numbers
- [ ] Dashboard with statistics

---

## Future Enhancements (Post-Launch)

- Barcode quality validation before printing
- Integration with existing ERP/WMS systems
- Support for other printer brands (Brother, Dymo, etc.)
- Mobile app for field scanning
- Advanced reporting dashboard
  - Daily/weekly serial generation stats
  - Printer usage analytics
  - UPC coverage reports
- Backup/restore functionality
- Multi-warehouse support
- Role-based access control (multiple admin levels)

---

## 🎯 Quick Reference

**System Architecture:**
- Django (central server, port 8001): Data management, ZPL generation
- Go Bridge (per workstation, port 5001): Printer discovery and printing
- Browser: Orchestrates between Django and Bridge

**Key Workflows:**
1. **Bulk Generation**: Scan part/qty → Spacebar → Generate+Print → Auto-reset
2. **Box Label**: Scan serial → Auto-lookup+print → Auto-reset
3. **Reprint**: Search serial → Click reprint button

**Keyboard Shortcuts:**
- Spacebar: Generate and print labels (bulk generate page)
- Enter/Tab: Submit input (all scanning pages)

---

## ✅ Testing Checklist

### Completed ✅
- [x] Printer selection in settings persists across reloads
- [x] Print requests reach bridge successfully
- [x] UI shows appropriate feedback (loading, success, errors)
- [x] Auto-focus chain works hands-free
- [x] Dynamic row addition in bulk generation
- [x] Serial number generation is atomic (no collisions)
- [x] Debug printer creates timestamped ZPL files
- [x] Timeout handling for offline bridge
- [x] Silent batch printing (no notification spam)
- [x] Auto-reset workflows

### Pending Hardware Testing
- [ ] Real printer accepts ZPL commands
- [ ] Barcode scanning works on printed labels
- [ ] Label dimensions match physical labels
- [ ] Print queue handles multiple jobs

---

## ⚠️ Known Issues

- None currently - all Phase 1-5 features working as designed
- Need hardware testing with actual Datamax printer (Phase 6)

---

## 📝 Important Notes

- **Printer settings**: Stored in localStorage (never in database) for multi-workstation support
- **Django admin**: Disabled - custom admin interface at /admin-upc/ used instead
- **Serial numbers**: Leading zeros based on configurable digit count (default 6)
- **Config model**: Singleton pattern enforced in save() method
- **Debug printer**: Always available for testing, saves to /tmp/labelgen/ or %TEMP%\\labelgen
- **Migrations applied**: 0001_initial, 0002_config_admin_password
- **Browser orchestration**: Critical - Django never calls Bridge (different networks)
