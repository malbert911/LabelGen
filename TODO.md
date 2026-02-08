# LabelGen Project Roadmap

## Project Status (Updated: Feb 7, 2026)

**Phases 1-3**: ✅ Complete  
**Phase 4**: 🚧 In Progress (50% complete)  
**Phases 5-6**: 📋 Planned

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

## Phase 4: Go Printer Bridge 🚧 IN PROGRESS

**Status**: 50% Complete (Started: Feb 7, 2026)  
**Purpose**: Local service to communicate with physical printers

### Completed ✅
- [x] Set up Go project in `bridge/` directory
- [x] Implement HTTP server on localhost:5001
- [x] Create `/health` endpoint for status checks
- [x] Create `/printers` endpoint with stubbed printers
  - [x] Returns 2 stubbed Zebra printers (ZD421, ZT230)
  - [x] JSON response with printer metadata
- [x] Create `/print` endpoint (stubbed)
  - [x] Accepts printer_id, label_type, and data
  - [x] Validates printer ID
  - [x] Returns job ID
  - [x] Logs print requests
- [x] Add CORS support for Django frontend (localhost:8001)
- [x] Basic error handling and logging

### Remaining Tasks
- [ ] Real printer discovery
  - [ ] USB printer detection (CUPS/direct access)
  - [ ] Network printer scanning (mDNS/Bonjour)
  - [ ] Printer capability detection
- [ ] ZPL template engine
  - [ ] Create label templates for serial numbers
  - [ ] Create templates for box labels
  - [ ] Variable substitution
- [ ] Actual print job execution
  - [ ] Send ZPL to Zebra printers
  - [ ] Handle printer responses
  - [ ] Error recovery
- [ ] Print queue management (optional)
- [ ] Printer status monitoring (paper, errors, etc.)

---

## Phase 5: Integration & Label Templates 📋 PLANNED

**Status**: Not Started  
**Purpose**: Connect all pieces and create label designs

### Preparation Done ✅
- [x] Printer settings page created (`/printer-settings/`)
- [x] Browser localStorage for per-client printer config
- [x] Two printer types: serial labels and box labels
- [x] Printer bridge status indicator in navbar
- [x] Health check on page load

### Remaining Tasks
- [ ] Design ZPL label templates
  - [ ] Serial number label (2-inch format for small labels)
  - [ ] Box shipping label (4-inch format for shipping)
  - [ ] Include Code 128 barcodes for serial numbers
  - [ ] Include UPC-A barcodes for product codes
  - [ ] Human-readable text for part numbers
- [ ] Create JavaScript print controller utility
  - [ ] Shared print helper in base.html
  - [ ] Get selected printer from localStorage
  - [ ] Validate printer is online before printing
  - [ ] Send print requests to bridge
  - [ ] Show success/error notifications
- [ ] Integrate print functionality
  - [ ] **bulk_generate.html**: Add "Print Labels" button after generation
    - Sends all generated serials to bridge
    - Uses `labelgen_serial_printer` from localStorage
  - [ ] **box_label.html**: Auto-print after serial lookup
    - Uses `labelgen_box_printer` from localStorage
  - [ ] **reprint.html**: Add "Reprint" button after lookup
    - Uses `labelgen_serial_printer` from localStorage
- [ ] Test print jobs with actual Zebra printers
- [ ] Handle edge cases
  - [ ] Printer offline → show error notification
  - [ ] No printer selected → redirect to settings
  - [ ] Bridge down → show connection warning

---

## Phase 6: Testing & Polish 📋 PLANNED

**Status**: Not Started  
**Purpose**: Ensure reliability and usability

### Tasks
- [ ] End-to-end testing
  - [ ] Test complete workflow from scan to print
  - [ ] Test with multiple concurrent users
  - [ ] Verify serial number uniqueness under load
  - [ ] Test printer failover scenarios
- [ ] Error handling improvements
  - [ ] Add user-friendly error messages
  - [ ] Implement retry logic for failed prints
  - [ ] Add audit logging for admin actions
  - [ ] Log all print jobs for tracking
- [ ] UI/UX improvements
  - [ ] Add keyboard shortcuts for common actions
  - [ ] Improve mobile responsiveness
  - [ ] Add audio feedback for successful scans (optional)
  - [ ] Loading states for async operations
  - [ ] Better validation feedback
- [ ] Documentation
  - [ ] User manual for warehouse staff
  - [ ] Admin guide for UPC management
  - [ ] IT deployment instructions
  - [ ] Printer setup guide
- [ ] Performance optimization
  - [ ] Database query optimization
  - [ ] Add database indexes where needed
  - [ ] Consider caching for config data
  - [ ] Optimize print queue throughput
- [ ] Additional Features (Nice-to-have)
  - [ ] CSV export of serial numbers
  - [ ] Dashboard with statistics
  - [ ] Print history view
  - [ ] Multi-language support
  - [ ] Custom label templates per product

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

## 🎯 Next Session - Where to Start

**Priority 1: Complete Print Integration**

1. **Start in `bulk_generate.html`** - Add print functionality
   - Add "Print All Labels" button after generation
   - Fetch `labelgen_serial_printer` from localStorage
   - Call bridge `/print` endpoint for each serial
   - Show progress indicator during printing

2. **Create shared print helper in `base.html`**
   ```javascript
   async function printLabel(printerType, labelType, data) {
     // Get printer from localStorage
     // Validate printer exists
     // Call bridge API
     // Show notifications
   }
   ```

3. **Update `box_label.html` and `reprint.html`** similarly

**Priority 2: ZPL Templates**

1. Research ZPL format for Zebra printers
2. Create templates in bridge/templates/ (or inline)
3. Implement template rendering in Go

**Priority 3: Real Printer Discovery**

1. Research USB printer detection on macOS
2. Implement network printer scanning
3. Replace stubbed printers with real discovery

---

## 📂 Files to Focus On

- `backend/inventory/templates/inventory/bulk_generate.html` - Add print button
- `backend/inventory/templates/inventory/base.html` - Add print helper function
- `bridge/main.go` - Add ZPL template rendering
- `bridge/printers.go` (new) - Real printer discovery

---

## ✅ Testing Checklist

- [ ] Can select printers in settings
- [ ] Settings persist across page reloads
- [ ] Print button appears after generation
- [ ] Print request reaches bridge
- [ ] Bridge returns success/error correctly
- [ ] UI shows appropriate feedback

---

## ⚠️ Known Issues

- None currently - all Phase 1-3 features working
- Need to test with actual Zebra printers once integration complete

---

## 📝 Important Notes

- Printer settings MUST be in localStorage, never in database (multi-client setup)
- Django admin is disabled - custom admin interface used instead
- Serial numbers use leading zeros based on configurable digit count
- Config model is singleton (enforced in save method)
- All migrations applied: 0001_initial, 0002_config_admin_password
