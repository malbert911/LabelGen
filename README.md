# LabelGen 🏷️

Django-based inventory management and label printing system for warehouse operations.

## Overview

LabelGen is a warehouse scanning system that converts bulk part number scans into sequential serial numbers and prints labels. Built as a monorepo with:
- **Django 6.x backend** (Python 3.14) - Web UI and database  
- **Go printer bridge** - Local service for printer communication

## Features

### ✅ Completed (Phases 1-3)
- **Bulk Serial Generation**: Hands-free scanning interface that generates sequential serial numbers
- **Box Label Printing**: Scan serial numbers to print shipping labels
- **Serial Reprint**: Look up and reprint existing serial number labels
- **Admin Interface**: Password-protected UPC management with CSV upload and manual editing
- **Dark Mode**: Auto-detecting theme with manual toggle
- **Printer Settings**: Browser-based printer selection (localStorage per workstation)
- **Printer Bridge Status**: Real-time connection indicator in navbar

### 🚧 In Progress (Phase 4)
- **Go Printer Bridge**: Stubbed service running on localhost:5001
  - `/health` - Health check endpoint
  - `/printers` - List available printers (2 stubbed Zebra printers)
  - `/print` - Accept print jobs (stubbed)

### 📋 Upcoming (Phases 5-6)
- ZPL label template engine
- Real printer discovery (USB/network)
- Print integration in UI pages
- Testing and polish

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
```

Bridge will be running at http://localhost:5001/

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
- `POST /api/process-bulk-scans/` - Generate serial numbers
- `GET /api/lookup-serial/?serial=000500` - Look up serial number

**Admin Pages** (password-protected)
- `GET /admin-login/` - Admin login
- `GET /admin-upc/` - UPC management
- `POST /api/admin-upload-csv/` - Bulk UPC upload
- `POST /api/admin-update-upc/` - Update single UPC

### Printer Bridge (http://localhost:5001)

- `GET /health` - Health check
- `GET /printers` - List available printers
- `POST /print` - Send print job

**Example Print Request**:
```json
{
  "printer_id": "zebra-zd421",
  "label_type": "inventory_label",
  "data": {
    "serial_number": "000500",
    "part_number": "232-9983",
    "upc": "012345678901"
  }
}
```

## Development Notes

### Current State (Feb 7, 2026)
- Django backend fully functional (Phases 1-3 complete)
- Go bridge running with stubbed printers
- Printer settings UI complete
- Navigation enhanced with status indicators
- Ready for print integration

### Next Steps
See [TODO.md](TODO.md) for detailed roadmap and [AI_CONTEXT.md](AI_CONTEXT.md) for comprehensive technical details.

## Contributing

This project is under active development. See TODO.md for current priorities.

## License

Internal project - not for public distribution.
