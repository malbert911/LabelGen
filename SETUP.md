# LabelGen - Setup Complete! 🎉

## Monorepo Structure

```
LabelGen/
├── backend/          # Django 6.x application
├── bridge/           # Go printer bridge (coming in Phase 4)
└── [docs]            # README, REQUIREMENTS, TODO, etc.
```

## Phase 1: Core Foundation ✅ COMPLETED

Django 6.x project has been successfully set up with the following components:

### ✅ Completed Setup

1. **Virtual Environment**: Python 3.14 venv created and configured
2. **Django 6.x**: Installed and initialized
3. **Project Structure**: 
   - Project name: `labelgen`
   - App name: `inventory`
4. **Database Models**:
   - `Product` (PartNumber PK, UPC nullable)
   - `SerialNumber` (SerialNumber PK, PartNumber FK, UPC denormalized, CreatedAt)
   - `Config` (serial_start, serial_digits, current_serial)
5. **Frontend**: Bulma.io CSS framework integrated in base template
6. **Django Admin**: Configured with custom admin classes for all models
7. **Migrations**: Created and applied successfully

### 📂 Project Structure

```
LabelGen/
├── venv/                           # Python virtual environment
├── labelgen/                       # Django project settings
│   ├── settings.py                 # Main configuration
│   ├── urls.py                     # URL routing
│   └── wsgi.py / asgi.py          # Server configs
├── inventory/                      # Main Django app
│   ├── models.py                   # Product, SerialNumber, Config models
│   ├── admin.py                    # Django admin configuration
│   ├── views.py                    # View functions
│   ├── urls.py                     # App URL patterns
│   ├── templates/inventory/        # HTML templates
│   │   ├── base.html              # Bulma.io base template
│   │   └── home.html              # Home page
│   └── static/inventory/          # Static files (CSS, JS, images)
├── manage.py                       # Django management script
└── db.sqlite3                     # SQLite database
```

### 🚀 Quick Start

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Activate Virtual Environment**:
   ```bash
   source venv/bin/activate.fish  # or activate, activate.bat on Windows
   ```

3. **Create Superuser** (for admin access):
   ```bash
   python manage.py createsuperuser
   ```

4. **Run Development Server**:
   ```bash
   python manage.py runserver
   ```

5. **Access the Application**:
   - Home Page: http://127.0.0.1:8000/
   - Admin Panel: http://127.0.0.1:8000/admin/

### 📊 Database Models

#### Product Model
- **part_number** (Primary Key): Part identifier (e.g., "232-9983")
- **upc** (Nullable): 12-digit UPC code

#### SerialNumber Model
- **serial_number** (Primary Key): Sequential number with leading zeros
- **part_number** (Foreign Key): Links to Product
- **upc** (Nullable): Denormalized UPC for fast label printing
- **created_at**: Timestamp

#### Config Model
- **serial_start**: Starting number for serial generation (default: 500)
- **serial_digits**: Digit count for serial numbers (default: 6)
- **current_serial**: Auto-incrementing counter

### 🎨 Features

**Base Template** ([inventory/templates/inventory/base.html](inventory/templates/inventory/base.html)):
- Bulma.io CSS framework (v1.0.0)
- Font Awesome icons
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
