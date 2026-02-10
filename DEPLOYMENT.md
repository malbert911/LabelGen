# LabelGen Deployment Guide

**Target Environment**: Windows Workstations + Central Server  
**Status**: Ready for Phase 6 Testing  
**Last Updated**: February 9, 2026

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Central Server (Linux/Windows)                             │
│  - Django 6.0.2 on port 8001                                │
│  - SQLite database                                          │
│  - Generates ZPL, manages data                              │
│  - Accessible from all workstations                         │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ HTTP requests
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼───────┐   ┌───────▼───────┐   ┌───────▼───────┐
│ Workstation 1 │   │ Workstation 2 │   │ Workstation 3 │
│               │   │               │   │               │
│ • Browser     │   │ • Browser     │   │ • Browser     │
│ • Bridge:5001 │   │ • Bridge:5001 │   │ • Bridge:5001 │
│ • Printer(s)  │   │ • Printer(s)  │   │ • Printer(s)  │
└───────────────┘   └───────────────┘   └───────────────┘
```

**Key Points**:
- Django runs ONCE on central server
- Bridge runs on EACH workstation with printers
- Browser orchestrates: Django (data/ZPL) + local Bridge (printing)
- Each workstation has independent printer settings in localStorage

---

## Prerequisites

### Central Server
- Python 3.14+ (or 3.10+ recommended)
- Git (for deployment)
- SQLite (included with Python)
- Network accessible to all workstations

### Each Workstation
- Chrome/Edge/Firefox browser
- Go 1.21+ (for building bridge) OR pre-compiled bridge.exe
- USB thermal printer (Datamax, Zebra, or ZPL-compatible)
- Network access to central server

---

## Central Server Deployment

### 1. Clone Repository
```bash
git clone <repository-url> /opt/labelgen
cd /opt/labelgen
```

### 2. Setup Python Environment
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

cd backend
pip install django==6.0.2
```

### 3. Initialize Database
```bash
# Run migrations
python manage.py migrate

# Create config record
python manage.py shell
>>> from inventory.models import Config
>>> Config.objects.create()
>>> exit()
```

### 4. Run Django (Production)

**Option A: Development Server** (for testing):
```bash
python manage.py runserver 0.0.0.0:8001
```

**Option B: Production with Gunicorn** (recommended):
```bash
pip install gunicorn
gunicorn labelgen.wsgi:application --bind 0.0.0.0:8001 --workers 3
```

**Option C: systemd Service** (Linux):
Create `/etc/systemd/system/labelgen.service`:
```ini
[Unit]
Description=LabelGen Django Application
After=network.target

[Service]
Type=notify
User=labelgen
Group=labelgen
WorkingDirectory=/opt/labelgen/backend
Environment="PATH=/opt/labelgen/venv/bin"
ExecStart=/opt/labelgen/venv/bin/gunicorn labelgen.wsgi:application --bind 0.0.0.0:8001 --workers 3

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable labelgen
sudo systemctl start labelgen
sudo systemctl status labelgen
```

### 5. Firewall Configuration
```bash
# Allow port 8001
sudo ufw allow 8001/tcp  # Ubuntu/Debian
# or
sudo firewall-cmd --permanent --add-port=8001/tcp  # CentOS/RHEL
sudo firewall-cmd --reload
```

---

## Workstation Deployment

### 1. Build Go Bridge

**On macOS/Linux** (for Windows workstations):
```bash
cd bridge
GOOS=windows GOARCH=amd64 go build -o bridge.exe
```

**On Windows**:
```bash
cd bridge
go build -o bridge.exe
```

### 2. Install Bridge on Workstation

Copy `bridge.exe` to workstation, e.g., `C:\LabelGen\bridge.exe`

### 3. Run Bridge Automatically

**Option A: Startup Folder** (simplest):
1. Press `Win+R`, type `shell:startup`, press Enter
2. Create shortcut to `C:\LabelGen\bridge.exe`
3. Bridge starts automatically on login

**Option B: Windows Service** (using NSSM):
```powershell
# Download NSSM from https://nssm.cc/
nssm install LabelGenBridge "C:\LabelGen\bridge.exe"
nssm set LabelGenBridge AppDirectory "C:\LabelGen"
nssm start LabelGenBridge
```

**Option C: Task Scheduler**:
1. Open Task Scheduler
2. Create Basic Task → "LabelGen Bridge"
3. Trigger: "At log on"
4. Action: Start Program → `C:\LabelGen\bridge.exe`
5. Settings: "Run whether user is logged on or not"

### 4. Test Bridge
Open browser: http://localhost:5001/health

Should return: `{"status":"healthy"}`

### 5. Configure Printer Settings

1. Open browser: `http://<server-ip>:8001/printer-settings/`
2. Click "Refresh Printers"
3. Select printer for Serial Labels
4. Select printer for Box Labels
5. Settings save automatically to browser localStorage

---

## Testing Checklist

### Central Server
- [ ] Django server running and accessible from workstations
- [ ] Admin login works: `http://<server-ip>:8001/admin-upc/` (password: "admin")
- [ ] Database has Config record
- [ ] No firewall blocking port 8001

### Workstation Setup
- [ ] Bridge.exe running on localhost:5001
- [ ] Bridge health check returns healthy
- [ ] "Refresh Printers" shows actual printer(s) + debug printer
- [ ] Printer selection persists after page reload
- [ ] Can access Django from workstation browser

### End-to-End Workflow
- [ ] Bulk Generation:
  - [ ] Scan part number → auto-advance to quantity
  - [ ] Scan quantity → auto-advance to next part
  - [ ] Press Spacebar → generates serials + prints labels
  - [ ] Form auto-resets after printing
  - [ ] "Next Serial" display updates
  - [ ] Actual labels print from thermal printer
  - [ ] Barcodes are scannable
- [ ] Box Label:
  - [ ] Scan serial → Enter → auto-lookup + auto-print
  - [ ] Form auto-resets for next scan
  - [ ] Box label prints correctly
- [ ] Reprint:
  - [ ] Search serial → displays record
  - [ ] Click Reprint → label prints

### Multi-User Testing
- [ ] Multiple workstations can generate serials simultaneously
- [ ] No serial number collisions (check database)
- [ ] Each workstation maintains own printer settings
- [ ] Concurrent printing works without conflicts

---

## Troubleshooting

### Django Not Accessible from Workstations

**Check server IP**:
```bash
ip addr show  # Linux
ipconfig      # Windows
```

**Check Django is listening on 0.0.0.0**:
```bash
netstat -tulnp | grep 8001  # Linux
netstat -an | findstr 8001  # Windows
```

**Test from workstation**:
```bash
curl http://<server-ip>:8001/
# or open in browser
```

### Bridge Not Finding Printers

**Windows PowerShell Error**:
- Open PowerShell as Administrator
- Run: `Get-Printer` manually to verify printers exist
- Check printer is powered on and connected

**Printer Not Showing**:
- Verify printer is installed in Windows Devices and Printers
- Check printer status (not offline/error)
- Restart Print Spooler: `net stop spooler && net start spooler`

**Debug Printer Not Working**:
- Check folder exists: `/tmp/labelgen/` or `%TEMP%\labelgen`
- Check write permissions

### Print Jobs Not Reaching Printer

**Check Bridge Logs**:
- Bridge prints to console/terminal
- Look for errors like "Failed to open printer" or "Access denied"

**Verify Printer Name**:
- Bridge uses exact printer name from Windows
- Check Devices and Printers for correct name
- Printer name is case-sensitive

**Test Manual Print** (Windows):
```powershell
# Create test ZPL file: test.zpl
echo "^XA^FO50,50^A0N,50,50^FDTest^FS^XZ" > test.zpl

# Send to printer
copy test.zpl \\.\PrinterName /b
```

### localStorage Settings Not Persisting

- Check browser not in Private/Incognito mode
- Clear browser cache and reconfigure
- Verify localStorage is enabled in browser settings
- Different browsers have separate settings (Chrome vs Firefox)

---

## Security Considerations

### Change Admin Password
1. Login: http://<server-ip>:8001/admin-upc/
2. Scroll to "Change Admin Password" section
3. Enter new password (twice)
4. Click "Update Password"

### Network Security
- Consider VPN or internal network only (don't expose to internet)
- Use HTTPS with reverse proxy (nginx/Apache) for production
- Restrict Django to internal IPs only in settings.py

### Database Backups
```bash
# Backup SQLite database
cp backend/db.sqlite3 backup/db-$(date +%Y%m%d).sqlite3

# Restore
cp backup/db-20260209.sqlite3 backend/db.sqlite3
```

---

## Maintenance

### Check Logs
- Django: Check terminal/service logs
- Bridge: Check terminal output
- Printer: Check Windows Print Spooler logs

### Update ZPL Templates
1. Login to admin: http://<server-ip>:8001/admin-upc/
2. Scroll to "ZPL Label Templates"
3. Edit template with proper ZPL syntax
4. Click "Preview" to test
5. Click "Save Templates"

### Export/Import UPC Data

**Export**:
```python
# Django shell
python manage.py shell
>>> from inventory.models import Product
>>> import csv
>>> with open('upc_export.csv', 'w', newline='') as f:
...     writer = csv.writer(f)
...     writer.writerow(['PartNumber', 'UPC'])
...     for p in Product.objects.all():
...         writer.writerow([p.part_number, p.upc or ''])
>>> exit()
```

**Import**:
Use CSV upload in admin interface

---

## Performance Tuning

### Django
- Use Gunicorn with multiple workers (3-5)
- Consider PostgreSQL for high-volume (replace SQLite)
- Add database indexes if queries slow down

### Bridge
- One bridge per workstation is optimal
- Bridge is lightweight, minimal resources needed
- Restart bridge if memory usage grows (shouldn't happen)

---

## Rollback Plan

If deployment fails:

1. **Stop services**:
   ```bash
   sudo systemctl stop labelgen  # Central server
   # Kill bridge.exe on workstations
   ```

2. **Restore database backup**:
   ```bash
   cp backup/db.sqlite3 backend/db.sqlite3
   ```

3. **Revert code** (if using git):
   ```bash
   git checkout <previous-commit>
   ```

4. **Restart services**

---

## Support Contacts

- **IT Admin**: [Contact Info]
- **Warehouse Manager**: [Contact Info]
- **Developer**: [Contact Info]

---

**Deployment Checklist Status**: Ready for Phase 6 ✅  
**Hardware Requirements**: Datamax O'Neil E-4204B or compatible ZPL printer  
**Next Step**: Hardware testing with actual printer
