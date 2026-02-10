# LabelGen 🏷️

Django-based inventory management and label printing system for warehouse operations.

## Overview

LabelGen is a warehouse scanning system that converts bulk part number scans into sequential serial numbers and prints labels. Built as a monorepo with:
- **Django 6.x backend** (Python 3.14) - Central web server for data & ZPL generation  
- **Go printer bridge** - Local service on each workstation for printer communication

**Critical Architecture**: Browser orchestrates between Django (central) and Bridge (local):
1. Browser → Django: Get data, generate ZPL strings
2. Browser → Bridge (localhost:5001): Discover printers, send ZPL to print
3. Django never calls Bridge - they run on different machines!

## Features

### ✅ Completed (Phases 1-4)
- **Bulk Serial Generation**: Hands-free scanning interface that generates sequential serial numbers
- **Box Label Printing**: Scan serial numbers to print shipping labels
- **Serial Reprint**: Look up and reprint existing serial number labels
- **Admin Interface**: Password-protected UPC management with CSV upload, manual editing, and ZPL template editor
- **Dark Mode**: Auto-detecting theme with manual toggle
- **Printer Settings**: Browser-based printer selection (localStorage per workstation)
- **Printer Bridge**: Fully functional cross-platform service
  - Windows: PowerShell Get-Printer + wmic fallback for printer discovery
  - macOS/Linux: CUPS lpstat for printer discovery
  - Direct raw ZPL printing to USB/network printers
  - Unique printer IDs handle duplicate models
- **ZPL Label Templates**: Editable templates with live preview
  - Serial labels (4x2") with Code 128 barcodes
  - Box labels (4x3") with UPC-A barcodes
  - Variable substitution: {{serial}}, {{part}}, {{upc_full}}, {{upc_11_digits}}
  - Labelary API integration for preview rendering

### 🚧 In Progress (Phase 5)
- **Print Button Integration**: Adding print functionality to UI pages
  - Printer dropdown selection
  - "Print" buttons on bulk generate, box label, reprint pages
  - Progress indicators for batch printing

### 📋 Upcoming (Phase 6)
- Testing with actual Datamax O'Neil E-4204B printer
- Error handling and edge cases
- Windows deployment guide
- Final polish

## Quick Start

### Prerequisites
- Python 3.14+ (for Django backend)
- Go 1.21+ (for printer bridge)
- SQLite (included with Python)

### Backend Setup (Django)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or venv/bin/activate.fish for fish shell

# Install dependencies
cd backend
pip install django==6.0.2

# Run migrations
python manage.py migrate

# Create default config (run Django shell)
python manage.py shell
>>> from inventory.models import Config
>>> Config.objects.create()
>>> exit()

# Start Django server
python manage.py runserver 8001
```

Django will be running at http://127.0.0.1:8001/

**Default admin password**: `admin` (change in Admin → Change Admin Password)

### Printer Bridge Setup (Go)

```bash
cd bridge

# Install dependencies
go mod download

# Run the bridge
go run main.go

# Or build a binary
go build -o labelgen-bridge
./labelgen-bridge  # or labelgen-bridge.exe on Windows
```

Bridge will be running at http://localhost:5001/

**Note**: The bridge must run on each workstation that has printers. It discovers local USB/network printers and handles raw ZPL printing.

### Usage

1. **Configure Printers**: Visit http://127.0.0.1:8001/printer-settings/
   - Select printer for serial labels
   - Select printer for box labels
   - Settings saved in browser localStorage

2. **Bulk Generation**: http://127.0.0.1:8001/generate/
   - Scan part number → Enter quantity → Repeat
   - Always one empty row ahead for continuous scanning
   - Generates sequential serial numbers

3. **Box Labels**: http://127.0.0.1:8001/box-label/
   - Scan serial number to print shipping label

4. **Admin**: http://127.0.0.1:8001/admin-upc/
   - Configure next serial number and digit count
   - Upload UPC codes via CSV
   - Edit UPC codes manually
   - Change admin password

## Architecture

### Critical: Browser Orchestration

```
┌─────────────────────────────────────────────────────────────┐
│  Browser (Workstation)                                      │
│                                                             │
│  1. GET /generate/  ────────────┐                          │
│  2. Fetch ZPL ─────────────────┐│                          │
│  3. GET /printers ──────┐      ││                          │
│  4. POST /print ────┐   │      ││                          │
│                     │   │      ││                          │
└─────────────────────┼───┼──────┼┼──────────────────────────┘
                      │   │      ││
                      │   │      ││
         ┌────────────┘   │      │└────────────────┐
         │                │      │                 │
         ▼                ▼      ▼                 ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Local Bridge     │  │ Django Server    │  │ Django Server    │
│ (localhost:5001) │  │ (192.168.1.100)  │  │ (192.168.1.100)  │
│                  │  │                  │  │                  │
│ • Discover USB   │  │ • Generate ZPL   │  │ • Serve HTML/JS  │
│   printers       │  │ • Lookup data    │  │                  │
│ • Send raw ZPL   │  │ • Manage DB      │  │                  │
│   to printer     │  │                  │  │                  │
└──────────────────┘  └──────────────────┘  └──────────────────┘
         │
         ▼
┌──────────────────┐
│ USB Printer      │
│ (Datamax/Zebra)  │
└──────────────────┘
```

**Key Points**:
- Django runs on central server (one instance for all workstations)
- Bridge runs locally on each workstation (with printers)
- Browser makes separate calls to Django (data) and Bridge (printing)
- Django NEVER calls Bridge - different networks!

### Monorepo Structure
```
LabelGen/
├── backend/          # Django web application
│   ├── labelgen/     # Project settings
│   ├── inventory/    # Main app
│   │   ├── models.py       # Product, SerialNumber, Config
│   │   ├── services.py     # Business logic layer
│   │   ├── views.py        # 7 pages + 6 admin views
│   │   ├── forms.py        # Admin forms
│   │   └── templates/      # Bulma.io templates
│   └── db.sqlite3    # SQLite database
│
├── bridge/           # Go printer service
│   ├── main.go       # HTTP server with CORS
│   └── go.mod        # Dependencies
│
└── venv/             # Python virtual environment
```

### Database Models

**Product** (Part Number PK)
- `part_number`: Primary key (e.g., "232-9983")
- `upc`: Optional 12-digit UPC code

**SerialNumber** (Serial Number PK)
- `serial_number`: Primary key with leading zeros (e.g., "000500")
- `part_number`: Foreign key to Product
- `upc`: Denormalized for fast label printing
- `created_at`: Timestamp

**Config** (Singleton)
- `serial_digits`: Number of digits (default: 6)
- `current_serial`: Next serial to generate (default: 500)
- `admin_password`: Admin interface password (default: "admin")

### Key Features

**Atomic Serial Generation**
- Uses Django `select_for_update()` for thread-safe serial number generation
- Prevents collisions in multi-user environments

**Auto-Product Creation**
- Products automatically created when first scanned
- UPC can be added later via admin interface

**Browser-Based Printer Selection**
- Printer settings stored in localStorage
- Each workstation has independent configuration
- Two printer types: serial labels and box labels

**Hands-Free Scanning**
- Auto-focus chain for continuous scanning
- Dynamic row addition (always one empty row ahead)
- Real-time serial range calculation

## API Endpoints

### Django Backend (http://127.0.0.1:8001)

**Public Pages**
- `GET /` - Home page
- `GET /generate/` - Bulk serial generation
- `GET /box-label/` - Box label printing
- `GET /reprint/` - Serial number reprint
- `GET /printer-settings/` - Printer configuration

**API Endpoints**
- `POST /api/process-bulk-scans/` - Generate serial numbers from scans
- `GET /api/lookup-serial/?serial=000500` - Look up serial number data
- `POST /api/generate-label-zpl/` - **Generate ZPL string** (browser sends to bridge)
  - Input: serial_number, part_number, upc, label_type ('serial' or 'box')
  - Output: {success, zpl: "^XA...^XZ", label_type}
- `POST /api/preview-zpl/` - Preview ZPL via Labelary API (admin only)

**Admin Pages** (password-protected)
- `GET /admin-login/` - Admin login
- `GET /admin-upc/` - UPC management + ZPL template editor
- `POST /api/admin-upload-csv/` - Bulk UPC upload
- `POST /api/admin-update-upc/` - Update single UPC

### Printer Bridge (http://localhost:5001)

- `GET /health` - Health check (returns {status: "healthy"})
- `GET /printers` - **List available printers**
  - Windows: Runs PowerShell Get-Printer or wmic
  - macOS/Linux: Runs lpstat -v and lpstat -p
  - Returns: {success, printers: [{id, name, type, connection, status, description}]}
- `POST /print` - **Send ZPL to printer**
  - Input: {printer_id, label_type, data: {zpl: "..."}}
  - Returns: {success, message, job_id}

**Example Print Request**:
```json
{
  "printer_id": "datamax_usb001",
  "label_type": "serial",
  "data": {
    "zpl": "^XA^FO100,50^A0N,30,30^FD000500^FS^XZ"
  }
}
```

**Platform Support**:
- Windows: Direct write to `\\.\PrinterName` (no drivers needed)
- macOS/Linux: CUPS `lpr -o raw` command

## Development Notes

### Current State (Feb 9, 2026)
- Django backend fully functional (Phases 1-3 complete)
- Go bridge production-ready with real printer discovery and printing (Phase 4 complete)
- ZPL templates implemented with live preview
- Ready for UI print button integration (Phase 5)

### Printer Support
- **Tested**: Datamax O'Neil eClass Mark III E-4204B (via PL-Z/ZPL emulation)
- **Compatible**: Any ZPL or ZPL-compatible printer (Zebra, Datamax, Sato, TSC, etc.)
- **Connection**: USB, Network (TCP/IP), Network (WSD)
- **OS**: Windows (primary), macOS/Linux (development)

### Next Steps
See [TODO.md](TODO.md) for detailed roadmap and [AI_CONTEXT.md](AI_CONTEXT.md) for comprehensive technical details.

## Contributing

This project is under active development. See TODO.md for current priorities.

## License

Internal project - not for public distribution.
