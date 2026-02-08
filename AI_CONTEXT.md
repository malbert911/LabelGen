# AI Context Document for LabelGen

**Last Updated**: February 7, 2026  
**Project Status**: Phase 4 In Progress (50% complete)

## Project Overview

LabelGen is a warehouse inventory management system that converts bulk part number scans into sequential serial numbers and prints labels. Built for hands-free operation with barcode scanners.

### Technology Stack
- **Backend**: Django 6.0.2 (Python 3.14.3)
- **Database**: SQLite (migrations applied)
- **Frontend**: Bulma.io 1.0.0 CSS framework + Vanilla JavaScript
- **Printer Bridge**: Go 1.21+ HTTP service
- **Icons**: Font Awesome 6.5.1

### Architecture
Monorepo structure:
- `backend/` - Django web application (port 8001)
- `bridge/` - Go printer service (port 5001)
- `venv/` - Python virtual environment

## Key Design Decisions

### 1. Monorepo Structure
Decided to reorganize as monorepo to accommodate both Django backend and Go printer bridge in one repository.

### 2. Printer Selection via localStorage
**Critical**: Printer settings are stored in browser localStorage, NOT in the database. This is because the Django app runs centrally for many clients, and each workstation needs its own printer configuration.

Two localStorage keys:
- `labelgen_serial_printer` - For inventory serial number labels
- `labelgen_box_printer` - For shipping box labels

### 3. Denormalized UPC in SerialNumber
UPC is copied from Product to SerialNumber at creation time for fast label printing without joins.

### 4. Atomic Serial Generation
Uses Django's `select_for_update()` to prevent serial number collisions in multi-user scenarios.

### 5. Auto-Product Creation
Products are automatically created with NULL UPC when first scanned. UPC codes can be added later via admin interface.

### 6. Session-Based Admin Auth
Simple password-protected admin (not Django's built-in admin) with auto-logout when navigating away.

## Database Schema

### Product
- `part_number` (PK, CharField) - e.g., "232-9983"
- `upc` (CharField, nullable) - 12-digit UPC

### SerialNumber
- `serial_number` (PK, CharField) - e.g., "000500" with leading zeros
- `part_number` (FK to Product)
- `upc` (CharField, nullable) - Denormalized from Product
- `created_at` (DateTimeField)

### Config (Singleton)
- `serial_digits` (IntegerField) - Number of digits (default: 6)
- `current_serial` (IntegerField) - Next serial to generate (default: 500)
- `admin_password` (CharField) - Admin password (default: "admin")

## File Structure

### Backend (Django)

**Models** (`backend/inventory/models.py`)
- Product, SerialNumber, Config models
- Config enforces singleton pattern

**Services** (`backend/inventory/services.py`)
- `SerialNumberGenerator` - Atomic serial generation with select_for_update()
- `BulkScanParser` - Parse multi-line scan input
- `BulkGenerationService` - Orchestrate bulk generation

**Views** (`backend/inventory/views.py`)
- 7 public pages: home, bulk_generate, box_label, reprint, printer_settings, admin_login, admin_upc
- 6 API endpoints: process_bulk_scans, lookup_serial, admin_upload_csv, admin_update_upc, admin_download_template, admin_logout

**Forms** (`backend/inventory/forms.py`)
- `AdminLoginForm` - Login form (NOT the same as AdminPasswordChangeForm!)
- `ConfigForm` - Serial number configuration (serial_digits, current_serial)
- `AdminPasswordChangeForm` - Change admin password (new_password, confirm_password)
- `UPCUploadForm` - CSV file upload with parse_csv() method
- `ProductUPCForm` - Individual UPC editing

**Templates** (`backend/inventory/templates/inventory/`)
- `base.html` - Navigation, theme toggle, printer status indicator, shared JS
- `home.html` - Landing page with feature cards
- `bulk_generate.html` - Hands-free scanning with dynamic rows
- `box_label.html` - Serial number lookup for shipping
- `reprint.html` - Serial number reprint
- `printer_settings.html` - Printer selection UI with localStorage
- `admin_login.html` - Admin password form
- `admin_upc.html` - UPC management with CSV upload and manual editing

### Bridge (Go)

**Main** (`bridge/main.go`)
- HTTP server on port 5001
- CORS enabled for localhost:8001
- Endpoints:
  - `GET /health` - Health check
  - `GET /printers` - List available printers (stubbed)
  - `POST /print` - Accept print jobs (stubbed)

## Important Implementation Details

### Bulk Generation Page
- Auto-focus chain: part number → quantity → next row
- Uses `requestAnimationFrame` for DOM focus to avoid timing issues
- Always maintains one empty row ahead for continuous scanning
- Cumulative serial range calculation
- JavaScript prevents Enter key default form submission

### Admin Interface
- Auto-logout implemented via JavaScript click handlers on non-admin links
- Removed `beforeunload` event to prevent logout during form submission
- Separate forms for config and password to avoid conflicts
- Form naming was critical: `AdminLoginForm` vs `AdminPasswordChangeForm`

### Printer Settings
- Fetches printers from bridge on page load
- Displays connection status (online/offline/checking)
- Manual refresh button
- Dropdown shows printer name and connection type
- Save button stores to localStorage with visual feedback

### Navigation Bar
- Shows all main features (Bulk Gen, Box Label, Reprint, Printers, Admin)
- Printer bridge status chip (green/red/checking)
- One-time health check on page load (no polling)
- Theme toggle button
- Mobile burger menu

### Dark Mode
- Auto-detects system preference
- Manual toggle stored in localStorage
- Comprehensive CSS for Bulma components
- Applies to tables, inputs, boxes, cards, etc.

## Common Pitfalls

1. **Form Naming Conflicts**: Had duplicate `AdminPasswordForm` - renamed to `AdminLoginForm` and `AdminPasswordChangeForm`

2. **Config Reloading**: Must reload config from database after save to avoid stale data:
   ```python
   config.save()
   config = SerialNumberGenerator.get_config()  # Reload!
   ```

3. **Auto-Logout Interference**: `beforeunload` event caused logout during form submissions - removed it, only logout on link clicks

4. **Serial Start vs Current Serial**: Removed confusing `serial_start` field, simplified to just `current_serial` (next serial number)

5. **Printer Storage**: NEVER store printer selection in database - must be localStorage for per-client config

## Development Workflow

### Running the Project

**Terminal 1 - Django**:
```bash
cd backend
source ../venv/bin/activate.fish  # or .../venv/bin/activate
python manage.py runserver 8001
```

**Terminal 2 - Go Bridge**:
```bash
cd bridge
go run main.go
```

### Migrations
```bash
cd backend
python manage.py makemigrations inventory
python manage.py migrate
```

### Current Migrations
- `0001_initial.py` - Product, SerialNumber, Config models
- `0002_config_admin_password.py` - Added admin_password field

## Next Steps (When Resuming)

### Immediate Priority: Print Integration

1. **Add Print Helper to base.html**
   ```javascript
   async function printLabel(printerType, labelType, data) {
     const printerKey = `labelgen_${printerType}_printer`;
     const printerId = localStorage.getItem(printerKey);
     
     if (!printerId) {
       showNotification('No printer selected', 'warning');
       return;
     }
     
     const response = await fetch('http://localhost:5001/print', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({
         printer_id: printerId,
         label_type: labelType,
         data: data
       })
     });
     // Handle response...
   }
   ```

2. **Update bulk_generate.html**
   - Add "Print All Labels" button after generation
   - Call `printLabel('serial', 'inventory_label', {...})` for each row
   - Show progress indicator

3. **Update box_label.html**
   - Add "Print Box Label" button after lookup
   - Call `printLabel('box', 'box_label', {...})`

4. **Update reprint.html**
   - Similar to box_label

### ZPL Template Research
- Study Zebra ZPL II format
- Create templates for 2-inch and 4-inch labels
- Code 128 barcode for serial numbers
- UPC-A barcode for product codes

### Real Printer Discovery
- Research CUPS integration on macOS
- USB printer detection
- Network printer mDNS/Bonjour scanning
- Replace stubbed printers in Go

## URLs

- Django: http://127.0.0.1:8001/
- Go Bridge: http://localhost:5001/
- Admin: http://127.0.0.1:8001/admin-upc/ (password: "admin")
- Printer Settings: http://127.0.0.1:8001/printer-settings/

## Testing Credentials

- Admin password: `admin` (can be changed in admin interface)
- No other authentication required

## Known Issues / Notes

- Django admin is disabled (commented out in urls.py) - users access custom admin instead
- Port 5000 was already in use, switched bridge to port 5001
- Serial numbers preserve leading zeros based on `serial_digits` setting
- Config model is a singleton (only one record allowed)
- UPC field is optional everywhere (nullable)

## Browser Compatibility

- Tested in Chrome/Safari with dark mode
- Uses modern JavaScript (async/await, fetch API)
- Requires localStorage support
- AbortSignal.timeout() for health check (modern browsers)

## Future Considerations

- Consider Redis for config caching if performance becomes issue
- May need print queue if high volume
- Could add WebSocket for real-time printer status
- Consider PWA for offline support

---

**Note for AI**: When resuming this project, start by reading this file, then check TODO.md for current phase. The printer bridge is stubbed and ready for integration. Focus on adding print functionality to the UI pages first, then work on real printer discovery and ZPL templates.
