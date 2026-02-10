# LabelGen Distribution Checklist

This checklist helps ensure successful deployment to production workstations.

## Pre-Build Checklist

### Django Backend
- [ ] Update version number in code if needed
- [ ] Change default admin password or document it clearly
- [ ] Test all features in development mode
- [ ] Verify database migrations are up to date
- [ ] Test with debug printer (check /tmp/labelgen/ or %TEMP%\labelgen)
- [ ] Review ZPL templates in admin interface
- [ ] Export critical data (UPC CSV if needed)

### Printer Bridge
- [ ] Test printer discovery on Windows
- [ ] Test actual printing with physical printer
- [ ] Verify debug printer creates files correctly
- [ ] Test with multiple printer models

## Build Process

### Windows Build
- [ ] Run `build-windows.bat` or `build.sh`
- [ ] Verify `backend/dist/LabelGen.exe` created (~60-80 MB)
- [ ] Verify `bridge/bridge.exe` created
- [ ] Test executables on build machine
- [ ] Check for any missing files or errors

### Distribution Package
- [ ] Create distribution folder (e.g., `LabelGen-v1.0`)
- [ ] Copy `LabelGen.exe` from `backend/dist/`
- [ ] Copy `bridge.exe` from `bridge/`
- [ ] Include README.txt with instructions
- [ ] Include QUICKSTART.txt with basic steps
- [ ] Add LICENSE file if applicable
- [ ] Create ZIP archive for easy distribution

## Testing (Before Distribution)

### Fresh Machine Test
- [ ] Test on clean Windows VM/machine (no Python/Go)
- [ ] Verify both executables run without errors
- [ ] Test system tray icon appears
- [ ] Test browser opens correctly
- [ ] Test printer discovery works
- [ ] Test actual label printing
- [ ] Test admin login (password: admin)
- [ ] Test all main workflows:
  - [ ] Bulk serial generation
  - [ ] Box label printing
  - [ ] Serial reprint
  - [ ] UPC management
  - [ ] Printer settings

### Network Test
- [ ] Test multiple workstations accessing same Django server
- [ ] Verify localStorage works independently per workstation
- [ ] Test concurrent serial generation (no collisions)
- [ ] Test firewall doesn't block ports 8001 or 5001

## Deployment Steps

### Central Server (if using network deployment)
```
Option A: Run Django on central server
- [ ] Install on server or use existing development setup
- [ ] Configure for production (see Django deployment docs)
- [ ] Set up auto-start on boot
- [ ] Configure firewall to allow port 8001
- [ ] Test access from workstations

Option B: Run Django on each workstation
- [ ] LabelGen.exe runs locally on each machine
- [ ] Each workstation has own database
- [ ] Simpler but less centralized
```

### Each Workstation
- [ ] Copy distribution package
- [ ] Place in permanent location (e.g., `C:\LabelGen\`)
- [ ] Run `LabelGen.exe` - verify tray icon appears
- [ ] Run `bridge.exe` - verify console shows "Printer Bridge starting"
- [ ] Open LabelGen from tray menu
- [ ] Configure printers in Printer Settings
- [ ] Test print with debug printer first
- [ ] Test print with actual printer
- [ ] Create shortcuts if desired
- [ ] Optional: Add to Windows Startup folder

## User Training

### Documentation to Provide
- [ ] Quick Start Guide (basic workflow)
- [ ] Printer Setup Instructions
- [ ] Admin Guide (UPC management, password change)
- [ ] Troubleshooting Guide
- [ ] Keyboard Shortcuts Reference:
  - Spacebar: Generate & Print (bulk page)
  - Enter/Tab: Submit scan inputs
  - Ctrl+D: Toggle dark mode

### Training Topics
- [ ] How to start the application (tray icon)
- [ ] Bulk serial generation workflow
- [ ] Box label printing workflow
- [ ] How to handle printer errors
- [ ] When to contact support

## Post-Deployment

### Verification
- [ ] Monitor first day of usage
- [ ] Check for error patterns
- [ ] Verify barcode scannability on printed labels
- [ ] Collect user feedback
- [ ] Check database growth rate

### Maintenance Plan
- [ ] Document backup procedure for database
- [ ] Set up regular database backups (db.sqlite3)
- [ ] Plan for UPC updates (CSV export/import)
- [ ] Monitor disk space for debug ZPL files
- [ ] Schedule periodic template review

## Common Issues & Solutions

### Issue: Executables won't run
- Windows Defender/Antivirus blocking
- Solution: Add exclusion for LabelGen.exe and bridge.exe

### Issue: No printers appear
- Bridge not running or crashed
- Solution: Restart bridge.exe, check console for errors

### Issue: Can't connect to Django
- Firewall blocking port 8001
- LabelGen.exe not running
- Solution: Check tray icon, check Windows Firewall

### Issue: Labels not printing
- Printer offline or out of paper
- Wrong printer selected
- Solution: Check printer status, verify printer settings

### Issue: Database locked
- Multiple LabelGen.exe instances running
- Solution: Quit all instances from tray, restart one

## Rollback Plan

If deployment fails:

1. **Stop all executables**
   - Right-click tray icon → Quit
   - Close bridge.exe console

2. **Backup database**
   ```
   copy db.sqlite3 db.sqlite3.backup
   ```

3. **Restore previous version**
   - Replace executables with previous working version
   - Restore database backup if needed

4. **Document the issue**
   - What went wrong?
   - Error messages?
   - Which workstations affected?

## Version Tracking

- [ ] Document version number
- [ ] Date of build
- [ ] Changes from previous version
- [ ] Known issues
- [ ] Compatible printer models

## Support Information

Provide users with:
- [ ] Support contact (email/phone)
- [ ] Issue reporting method
- [ ] Expected response time
- [ ] Escalation procedure

---

**Deployment Date**: _______________  
**Version**: _______________  
**Deployed By**: _______________  
**Number of Workstations**: _______________  
**Notes**: 
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
