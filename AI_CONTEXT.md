# AI Context Document for LabelGen

**Last Updated**: February 9, 2026  
**Project Status**: Phase 4 Complete, Phase 5 Ready

## Project Overview

LabelGen is a warehouse inventory management system that converts bulk part number scans into sequential serial numbers and prints labels. Built for hands-free operation with barcode scanners.

### Technology Stack
- **Backend**: Django 6.0.2 (Python 3.14.3)
- **Database**: SQLite (migrations applied)
- **Frontend**: Bulma.io 1.0.0 CSS framework + Vanilla JavaScript
- **Printer Bridge**: Go 1.21+ HTTP service
- **Icons**: Font Awesome 6.5.1

### Architecture
**Critical**: Client-Server with Browser Orchestration
- `backend/` - Django web application (port 8001) - **Central server, generates ZPL only**
- `bridge/` - Go printer service (port 5001) - **Runs locally on each workstation**
- `venv/` - Python virtual environment

**Data Flow**:
1. Browser → Django: Get ZPL string (with serial/part/UPC data)
2. Browser → Local Bridge (localhost:5001): Get printers, send ZPL to print
3. **Django NEVER calls Bridge** - Browser orchestrates all communication

## Key Design Decisions

### 1. Monorepo Structure
Decided to reorganize as monorepo to accommodate both Django backend and Go printer bridge in one repository.

### 2. Printer Selection via localStorage
**Critical**: Printer settings are stored in browser localStorage, keyed by Django URL. This is because:
- Django app runs on central server
- Bridge runs locally on each workstation
- Each workstation has its own USB printers
- Browser needs to remember which local printer to use for that Django instance

localStorage keys:
- `labelgen_serial_printer_<django_url>` - Serial label printer for this Django server
- `labelgen_box_printer_<django_url>` - Box label printer for this Django server

Example: `labelgen_serial_printer_http://192.168.1.100:8001` = `datamax_usb001`

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
- `serial_label_zpl` (TextField) - ZPL template for 4x2" serial labels
- `box_label_zpl` (TextField) - ZPL template for 4x3" box labels
- `serial_label_width` (DecimalField) - Serial label width in inches (default: 4.0)
- `serial_label_height` (DecimalField) - Serial label height in inches (default: 2.0)
- `box_label_width` (DecimalField) - Box label width in inches (default: 4.0)
- `box_label_height` (DecimalField) - Box label height in inches (default: 3.0)
- `label_dpi` (IntegerField) - Printer DPI: 203, 300, or 600 (default: 203)

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
- API endpoints:
  - process_bulk_scans - Create serial numbers from scans
  - lookup_serial - Get serial number data
  - admin_upload_csv - Bulk UPC upload
  - admin_update_upc - Update single UPC
  - admin_download_template - CSV template download
  - preview_zpl - Preview ZPL via Labelary API
  - generate_label_zpl - **Generate ZPL string for serial/box labels** (browser sends this to local bridge)
  - admin_logout - Clear session

**Forms** (`backend/inventory/forms.py`)
- `AdminLoginForm` - Login form (NOT the same as AdminPasswordChangeForm!)
- `ConfigForm` - Serial number configuration (serial_digits, current_serial)
- `AdminPasswordChangeForm` - Change admin password (new_password, confirm_password)
- `UPCUploadForm` - CSV file upload with parse_csv() method
- `ProductUPCForm` - Individual UPC editing
- `LabelTemplateForm` - ZPL template editor (serial/box templates, dimensions, DPI)

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

**Main** (`bridge/main.go`) - **432 lines, production-ready**
- HTTP server on port 5001
- CORS enabled for localhost:8001 and 127.0.0.1:8001
- Cross-platform printer discovery and printing
- Endpoints:
  - `GET /health` - Health check
  - `GET /printers` - **List available printers** (real implementation)
    - Windows: PowerShell Get-Printer + wmic fallback
    - macOS/Linux: CUPS lpstat
    - Returns: printer ID, name, type (thermal/standard), connection (USB/Network), status
    - Unique IDs handle duplicate printer models (name + port/serial)
  - `POST /print` - **Send ZPL to printer** (real implementation)
    - Windows: Direct write to `\\.\PrinterName`
    - macOS/Linux: lpr with raw option
    - Accepts: printer_id, label_type, data.zpl
    - Returns: success, message, job_id

**Printer Discovery**:
- Automatically detects OS (Windows primary, macOS/Linux fallback)
- Windows: PowerShell for modern systems, wmic for legacy
- Detects thermal printers by driver keywords (Datamax, Zebra, Sato, TSC, etc.)
- Creates unique IDs from printer name + port/URI to distinguish identical models
- Parses connection type (USB, Network, Serial) from port/URI info

**Printing**:
- Windows: Opens `\\.\PrinterName` as file, writes raw ZPL bytes
- macOS/Linux: Creates temp file, sends via `lpr -o raw`
- No printer drivers needed - raw ZPL passthrough
- Works with any ZPL-compatible printer (Zebra, Datamax O'Neil, etc.)

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
- Separate forms for config, password, and label templates to avoid conflicts
- Form naming was critical: `AdminLoginForm` vs `AdminPasswordChangeForm`
- **ZPL Template Editor**: Live preview using Labelary API
  - Editable templates with monospace font
  - Preview button generates PNG from ZPL
  - Supports {{serial}}, {{part}}, {{upc_full}}, {{upc_11_digits}} variables
  - Separate templates and dimensions for serial vs box labels
  - DPI selector (203/300/600) affects preview quality

### Printer Settings
- Fetches printers from **local bridge** (localhost:5001) via JavaScript
- Displays connection status (online/offline/checking)
- Manual refresh button
- Dropdown shows printer name and connection type
- Save button stores to localStorage with visual feedback
- **localStorage key includes Django URL** for multi-server support

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

6. **Architecture Confusion**: Django CANNOT call the bridge - bridge runs on workstation localhost, Django on central server. Browser must orchestrate!

7. **UPC-A Barcode Format**: UPC-A requires 11 digits (not 12) - the 12th is check digit. Use {{upc_11_digits}} variable in ZPL.

8. **ZPL Template Syntax**: Django template tags conflict with ZPL {{}} syntax. Use `{% templatetag openvariable %}` for displaying literal {{ in templates.

## Development Workflow

### Running the Project

**Terminal 1 - Django**:
```bash
cd backend
source ../venv/bin/activate.fish  # or .../venv/bin/activate
python manage.py runserver 8001
```

**Terminal 2 - Go Bridge** (on each workstation):
```bash
cd bridge
go run main.go
# Or build binary:
go build -o labelgen-bridge
./labelgen-bridge
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
- `0003_config_box_label_zpl_config_label_dpi_and_more.py` - Added ZPL template fields
- `0004_remove_config_label_height_remove_config_label_width_and_more.py` - Separated serial/box dimensions
- `0005_update_zpl_templates.py` - Updated default templates with centered layout
- Multiple updates for UPC variable handling ({{upc_full}}, {{upc_11_digits}})

## Next Steps (When Resuming)

### Phase 5: UI Integration - Print Buttons

1. **Add Printer Dropdown to Pages**
   - bulk_generate.html, box_label.html, reprint.html
   - Fetch printers from localhost:5001/printers on page load
   - Remember selection in localStorage

2. **Add Print Functionality**
   ```javascript
   async function printLabel(serialNumber, partNumber, upc, labelType) {
     // 1. Get ZPL from Django
     const zplResp = await fetch('/api/generate-label-zpl/', {
       method: 'POST',
       headers: {'Content-Type': 'application/json'},
       body: JSON.stringify({
         serial_number: serialNumber,
         part_number: partNumber,
         upc: upc,
         label_type: labelType  // 'serial' or 'box'
       })
     });
     const {zpl} = await zplResp.json();
     
     // 2. Get selected printer from localStorage
     const printerKey = labelType === 'box' ? 'box_printer' : 'serial_printer';
     const printerId = localStorage.getItem(`labelgen_${printerKey}_${window.location.origin}`);
     
     // 3. Send ZPL to local bridge
     const printResp = await fetch('http://localhost:5001/print', {
       method: 'POST',
       headers: {'Content-Type': 'application/json'},
       body: JSON.stringify({
         printer_id: printerId,
         label_type: labelType,
         data: {zpl: zpl}
       })
     });
     return await printResp.json();
   }
   ```

3. **Update bulk_generate.html**
   - Add "Print All Labels" button after generation
   - Loop through generated serials, call printLabel() for each
   - Show progress ("Printing 3 of 25...")

4. **Update box_label.html**
   - Add "Print Box Label" button after lookup
   - Call printLabel() with box label type

5. **Update reprint.html**
   - Add "Reprint Label" button after lookup

### Phase 6: Testing & Polish

- Test with actual Datamax O'Neil E-4204B printer
- Test UPC-A barcode scanning
- Test Code 128 barcode scanning for serials
- Error handling (printer offline, bridge down, etc.)
- Loading states and visual feedback
- Cross-browser testing
- Windows deployment guide for bridge binary

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
- Datamax O'Neil E-4204B printer supports ZPL via PL-Z emulation mode
- Labelary API used for ZPL preview (converts ZPL to PNG)
- DPI to DPMM conversion: 203→8dpmm, 300→12dpmm, 600→24dpmm

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
- Compile Go bridge to Windows binary for deployment
- Add label design GUI (visual ZPL editor)
- Support other label formats (EPL, CPCL) if needed

---

**Note for AI**: When resuming this project, start by reading this file. Phase 4 is complete - printer bridge is fully functional with real Windows/macOS printer discovery and printing. Django generates ZPL strings. Browser orchestrates between Django (data/ZPL) and local bridge (printing). Next: Add print buttons to UI pages.
