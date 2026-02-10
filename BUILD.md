# LabelGen Build Guide

This guide explains how to build standalone executables for both the Django backend and the Go printer bridge.

## Building Windows Executables

### Django Backend (.exe with System Tray)

**Requirements:**
- Python 3.14+
- Windows (or cross-compile setup)

**Steps:**

1. **Install build dependencies:**
   ```bash
   cd backend
   pip install -r requirements-build.txt
   ```

2. **Run the build script:**
   ```bash
   python build_exe.py
   ```

3. **Output:**
   - `dist/LabelGen.exe` - Standalone Django application with system tray
   - `dist/README.txt` - User instructions

**What it includes:**
- Django web server
- SQLite database
- All templates and static files
- System tray application
- Auto-start server on launch

**How it works:**
- Double-click `LabelGen.exe` to start
- System tray icon appears (bottom-right of screen)
- Right-click tray icon for menu options:
  - Open LabelGen (launches browser)
  - Admin Panel
  - Printer Settings
  - Start/Stop Server
  - Quit

### Go Printer Bridge (.exe)

**Requirements:**
- Go 1.21+

**Steps:**

1. **Build for Windows (from any platform):**
   ```bash
   cd bridge
   GOOS=windows GOARCH=amd64 go build -o bridge.exe main.go
   ```

2. **Build for current platform:**
   ```bash
   cd bridge
   go build -o labelgen-bridge main.go
   ```

3. **Output:**
   - `bridge.exe` (Windows)
   - `labelgen-bridge` (macOS/Linux)

## Distribution Package

To create a complete distribution package:

### Windows Package

1. **Build both executables:**
   ```bash
   # Build Django backend
   cd backend
   python build_exe.py
   
   # Build printer bridge
   cd ../bridge
   GOOS=windows GOARCH=amd64 go build -o bridge.exe main.go
   ```

2. **Create distribution folder:**
   ```
   LabelGen-v1.0/
   ├── LabelGen.exe          # Django backend (from backend/dist/)
   ├── bridge.exe            # Printer bridge
   ├── README.txt            # User guide
   └── QUICKSTART.txt        # Quick start guide
   ```

3. **Create QUICKSTART.txt:**
   ```txt
   LabelGen Quick Start
   ====================
   
   1. Start the Django Server:
      - Double-click LabelGen.exe
      - A system tray icon will appear (blue "LG")
      - Right-click icon → "Open LabelGen"
   
   2. Start the Printer Bridge:
      - Double-click bridge.exe
      - A console window will open showing "Printer Bridge starting..."
      - Leave this window open
   
   3. Configure Printers:
      - In LabelGen, click "Printer Settings"
      - Select your printers from the dropdown
      - Click Save
   
   4. Use the Application:
      - Bulk Generation: Generate serial numbers
      - Box Label: Print shipping labels
      - Admin: Manage UPCs and settings (password: admin)
   
   Troubleshooting:
   - If no printers appear, make sure bridge.exe is running
   - Change admin password in Admin → Change Password
   - Check console windows for error messages
   ```

4. **Package as ZIP:**
   ```bash
   zip -r LabelGen-v1.0-Windows.zip LabelGen-v1.0/
   ```

## Development vs Production

### Development Mode

```bash
# Django backend
cd backend
source venv/bin/activate
python manage.py runserver 8001

# Printer bridge (separate terminal)
cd bridge
go run main.go
```

### Production Mode (Executables)

```bash
# Django backend
./LabelGen.exe  # Windows
./LabelGen      # macOS/Linux (if built)

# Printer bridge (separate terminal)
./bridge.exe    # Windows
./labelgen-bridge  # macOS/Linux
```

## PyInstaller Details

### What gets bundled:

- ✅ Python interpreter
- ✅ Django framework
- ✅ All templates (HTML files)
- ✅ Static files (CSS, JS)
- ✅ Database migrations
- ✅ System tray application
- ✅ Required Python packages

### What doesn't get bundled:

- ❌ Database file (db.sqlite3) - **created on first run next to the executable**
- ❌ Log files
- ❌ User uploads (if any)
- ❌ Debug ZPL files (/tmp/labelgen/ or %TEMP%\labelgen)

**Important**: The database file (db.sqlite3) will be created in the same directory as the executable. This ensures your data persists across runs and makes backups easy - just copy the .db file!

### Customization

Edit `backend/labelgen.spec` to:
- Add an icon: `icon='icon.ico'`
- Include additional files
- Exclude unnecessary modules
- Change exe name

### Size Optimization

The default build is ~60-80 MB. To reduce:

1. **Use UPX compression** (already enabled):
   ```python
   upx=True,
   upx_exclude=[],
   ```

2. **Exclude unused modules:**
   ```python
   excludes=['tkinter', 'matplotlib', 'numpy'],
   ```

3. **One-folder build** (faster, larger):
   Change in spec file:
   ```python
   exe = EXE(
       # ... remove a.binaries, a.zipfiles, a.datas from here
   )
   
   coll = COLLECT(
       exe,
       a.binaries,
       a.zipfiles,
       a.datas,
       name='LabelGen',
   )
   ```

## Troubleshooting Build Issues

### "Module not found" errors:

Add to `hidden_imports` in `labelgen.spec`:
```python
hiddenimports=[
    'your.module.here',
]
```

### Missing template files:

Verify in spec file:
```python
datas=[
    ('inventory/templates', 'inventory/templates'),
]
```

### Database errors:

Make sure migrations are included:
```python
datas=[
    ('inventory/migrations', 'inventory/migrations'),
]
```

**First Run**: On first run, the executable will:
1. Create `db.sqlite3` in the same directory as the executable
2. **Automatically apply all migrations** (no manual `migrate` command needed!)
3. Create an initial Config object with defaults (serial starts at 500, 6 digits)
4. Start the Django server

Migrations are checked and applied on every startup, so updates are handled automatically.

### Tray icon doesn't appear:

Check that `pystray` and `Pillow` are installed:
```bash
pip install pystray Pillow
```

## Auto-Start on Windows

To make LabelGen start automatically:

1. **Create shortcut:**
   - Right-click `LabelGen.exe` → Create shortcut

2. **Add to Startup folder:**
   - Press `Win+R`
   - Type: `shell:startup`
   - Move shortcut to this folder

3. **Same for bridge.exe** if desired

## Platform-Specific Notes

### Windows
- `.exe` files work directly
- No administrator rights needed
- Firewall may ask for permission (allow it)

### macOS
- PyInstaller can create `.app` bundles
- May need to sign for Gatekeeper
- Bridge binary needs executable permission: `chmod +x labelgen-bridge`

### Linux
- PyInstaller creates ELF binaries
- May need to install system dependencies
- Bridge should work out of the box

## Version Information

To add version info to Windows .exe:

1. Create `version_info.txt`:
   ```
   VSVersionInfo(
     ffi=FixedFileInfo(
       filevers=(1, 0, 0, 0),
       prodvers=(1, 0, 0, 0),
       # ...
     )
   )
   ```

2. Add to spec file:
   ```python
   exe = EXE(
       # ...
       version='version_info.txt',
   )
   ```

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Build Executables

on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.14'
      - name: Build Django exe
        run: |
          cd backend
          pip install -r requirements-build.txt
          python build_exe.py
      - name: Build Bridge exe
        uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      - run: |
          cd bridge
          go build -o bridge.exe main.go
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: LabelGen-Windows
          path: |
            backend/dist/LabelGen.exe
            bridge/bridge.exe
```

---

**Questions?** Check the main README.md or open an issue.
