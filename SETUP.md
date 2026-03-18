# LabelGen - Setup Complete! 🎉

**Status**: Development Complete - Ready for Hardware Testing  
**Last Updated**: February 9, 2026

## Monorepo Structure

```
LabelGen/
├── backend/          # Django 6.x application (central server)
├── bridge/           # Go printer bridge (runs on workstations)
└── venv/             # Python virtual environment
```

## Phases 1-5: COMPLETED ✅

### ✅ Implemented Features

**Phase 1-3: Core Application**
1. Django 6.0.2 backend with Python 3.14.3
2. SQLite database with migrations
3. Bulma.io CSS framework with dark mode
4. Models: Product, SerialNumber, Config (singleton)
5. Business logic: SerialNumberGenerator, BulkScanParser, BulkGenerationService
6. All user pages: Bulk Generation, Box Label, Reprint, Printer Settings, Admin

**Phase 4: Go Printer Bridge**
1. HTTP server on localhost:5001 with CORS
2. Real printer discovery (Windows PowerShell/wmic, macOS/Linux CUPS)
3. Direct raw ZPL printing (no drivers needed)
4. Debug printer for testing (saves to /tmp/labelgen/ or %TEMP%\\labelgen)
5. Cross-platform support

**Phase 4.5: ZPL Templates**
1. Editable ZPL templates in admin interface
2. Live Labelary API preview (ZPL → PNG)
3. Variable substitution: {{serial}}, {{part}}, {{upc_full}}, {{upc_11_digits}}
4. Code 128 and UPC-A barcode support

**Phase 5: Print Integration**
1. PrinterBridge JavaScript utility in base.html
2. Single-click generate+print workflows
3. Auto-reset forms for continuous scanning
4. Keyboard shortcuts (Spacebar, Enter, Tab)
5. Silent batch printing (no notification spam)
6. localStorage printer selection per workstation
7. Optimized code (removed dead code, extracted constants)

### 📂 Current Project Structure

```
LabelGen/
├── venv/                                # Python virtual environment
├── backend/
│   ├── labelgen/                       # Django project settings
│   │   ├── settings.py                 # Configuration
│   │   ├── urls.py                     # URL routing
│   │   └── wsgi.py / asgi.py          # Server configs
│   ├── inventory/                      # Main Django app
│   │   ├── models.py                   # Product, SerialNumber, Config
│   │   ├── services.py                 # Business logic
│   │   ├── views.py                    # View functions (12 views)
│   │   ├── forms.py                    # Admin forms
│   │   ├── urls.py                     # App URL patterns
│   │   ├── templates/inventory/        # HTML templates
│   │   │   ├── base.html              # PrinterBridge utility
│   │   │   ├── home.html              # Landing page
│   │   │   ├── bulk_generate.html     # Bulk serial generation
│   │   │   ├── box_label.html         # Box label printing
│   │   │   ├── reprint.html           # Serial reprint
│   │   │   ├── printer_settings.html  # Printer configuration
│   │   │   ├── admin_login.html       # Admin authentication
│   │   │   └── admin_upc.html         # Admin interface
│   │   └── static/inventory/          # Static files
│   ├── manage.py                       # Django management
│   └── db.sqlite3                      # SQLite database
├── bridge/
│   ├── main.go                         # HTTP server (474 lines)
│   ├── go.mod                          # Dependencies
│   └── README.md                       # Bridge documentation
└── [docs]/                             # README, TODO, PROGRESS, etc.
```

### 🚀 Quick Start

**1. Start Django Backend**:
```bash
cd backend
source ../venv/bin/activate  # or venv/bin/activate.fish for fish shell
python manage.py runserver 8001
```

**2. Start Printer Bridge** (in new terminal):
```bash
cd bridge
go run main.go

# Or build and run binary:
go build -o labelgen-bridge
./labelgen-bridge
```

**3. Access Application**:
- Home Page: http://127.0.0.1:8001/
- Admin Panel: http://127.0.0.1:8001/admin-upc/ (password: "admin")
- Printer Settings: http://127.0.0.1:8001/printer-settings/

**4. Configure Printers**:
- Go to Printer Settings
- Select printer for serial labels (or use "DEBUG: Save ZPL to File")
- Select printer for box labels
- Settings save automatically to browser localStorage

**5. Test Workflow**:
- Bulk Generation: Scan part → qty → Spacebar → Auto-print → Auto-reset
- Box Label: Scan serial → Enter → Auto-print → Auto-reset

### 📊 Database Models

#### Product Model
- **part_number** (Primary Key): Part identifier (e.g., "232-9983")
- **upc** (Nullable): 12-digit UPC code

#### SerialNumber Model
- **serial_number** (Primary Key): Sequential with leading zeros (e.g., "000500")
- **part_number** (Foreign Key): Links to Product
- **upc** (Nullable): Denormalized for fast label printing
- **created_at**: Timestamp

#### Config Model (Singleton)
- **serial_digits**: Digit count (default: 6, configurable)
- **current_serial**: Next serial to generate (auto-increments)
- **admin_password**: Admin interface password (default: "admin")
- **serial_label_zpl**: ZPL template for 4x2" serial labels
- **box_label_zpl**: ZPL template for 4x3" box labels
- **label_dpi**: DPI selector (203/300/600)

### 🖨️ Printer Bridge Features

**Endpoints**:
- `GET /health` - Health check
- `GET /printers` - List available printers (with debug printer)
- `POST /print` - Send ZPL to printer

**Platform Support**:
- Windows: PowerShell Get-Printer + wmic fallback
- macOS/Linux: CUPS lpstat integration
- Direct raw ZPL printing (no drivers needed)

**Debug Printer**:
- Always available for testing
- Saves ZPL to /tmp/labelgen/ (macOS/Linux) or %TEMP%\\labelgen (Windows)
- Timestamped filenames: label-20260209-122727.040.zpl

### 🎨 Key Features

**Browser Orchestration**:
- Django (central server, port 8001): Data + ZPL generation
- Bridge (workstation, port 5001): Printer discovery + printing
- Browser coordinates between both services

**Hands-Free Workflows**:
- Auto-focus chain for continuous scanning
- Enter/Tab/Spacebar keyboard shortcuts
- Auto-reset forms after printing
- Dynamic row addition in bulk generation

**Smart Printing**:
- localStorage printer selection per workstation
- Silent batch printing (no notification spam)
- 5-second timeout with helpful error messages
- Debug printer for testing without hardware

### 🔐 Admin Features

**Admin Interface** (http://127.0.0.1:8001/admin-upc/):
- Password-protected (default: "admin")
- Serial number configuration
- CSV upload for bulk UPC assignment
- Manual inline UPC editing with AJAX
- ZPL template editor with live Labelary preview
- Password change functionality

### 📋 Next Steps

**Phase 6 - Testing & Deployment**:
1. Test with actual Datamax O'Neil E-4204B printer
2. Verify barcode scannability on printed labels
3. Compile Windows bridge: `GOOS=windows GOARCH=amd64 go build -o bridge.exe`
4. Multi-workstation concurrent testing
5. Create deployment documentation
6. User training materials

### 💡 Useful Commands

**Django**:
```bash
cd backend
source ../venv/bin/activate.fish

# Run server
python manage.py runserver 8001

# Database operations
python manage.py makemigrations
python manage.py migrate

# Django shell
python manage.py shell
```

**Go Bridge**:
```bash
cd bridge

# Run in development
go run main.go

# Build binary
go build -o labelgen-bridge

# Build for Windows (from macOS/Linux)
GOOS=windows GOARCH=amd64 go build -o bridge.exe

# Build for Linux (from macOS/Windows)
GOOS=linux GOARCH=amd64 go build -o labelgen-bridge
```

**Testing Debug Printer**:
```bash
# Check saved ZPL files
ls -lt /tmp/labelgen/           # macOS/Linux
dir %TEMP%\labelgen\            # Windows

# View ZPL content
cat /tmp/labelgen/label-*.zpl   # macOS/Linux
type %TEMP%\labelgen\label-*.zpl  # Windows
```

---

**Development Status**: Phases 1-5 Complete ✅  
**Ready For**: Hardware Testing (Phase 6)  
**Last Updated**: February 9, 2026  
**Django**: 6.0.2  
**Python**: 3.14.3  
**Go**: 1.21+
- Responsive navbar
- Large scannable input styling
- Notification system
- Industrial/warehouse-appropriate design

**Django Admin Customizations**:
- Product list with serial count
- SerialNumber list with filtering and search
- Config with formatted serial display
- Restrictions to prevent accidental data corruption

### ⚙️ Configuration

**Serial Number Settings**:
- Configurable via Django admin (`/admin/inventory/config/`)
- Defaults: Start at 500, 6 digits → "000500"
- Leading zeros preserved based on digit count
- Can be changed to support 10, 12, or more digits

### 📝 Next Steps (Phase 2)

See [TODO.md](TODO.md) for the implementation roadmap. Next phase includes:

1. **Core Business Logic**:
   - Serial number generator with atomic increment
   - Bulk scan parser (Part/Qty pairing)
   - Product auto-creation logic
   - SerialNumber batch creation

2. **User Interface Pages**:
   - Bulk Serial Generation page (`/generate/`)
   - Box Label Printing page (`/box-label/`)
   - Serial Reprint page (`/reprint/`)
   - Admin UPC Management page

3. **Printing Integration** (Go Bridge):
   - Go binary for local printer communication
   - Label templates (format TBD based on printer model)

### 🛠️ Development Commands

```bash
# Activate virtual environment
source venv/bin/activate.fish

# Run development server
python manage.py runserver

# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Open Django shell
python manage.py shell

# Run tests
python manage.py test
```

### 📚 Key Files

- **Requirements**: [REQUIREMENTS.md](REQUIREMENTS.md) - Full specifications
- **Roadmap**: [TODO.md](TODO.md) - Implementation phases
- **Architecture**: [README.md](README.md) - High-level overview
- **AI Context**: [.ai-context.md](.ai-context.md) - Development guidelines

---

**Status**: Phase 1 Complete ✅  
**Date**: February 7, 2026  
**Django Version**: 6.0.2  
**Python Version**: 3.14.3
