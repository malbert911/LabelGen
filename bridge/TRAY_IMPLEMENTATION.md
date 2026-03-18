# LabelGen Bridge - Tray Application Upgrade

## Summary of Changes

The LabelGen Printer Bridge has been upgraded to run as a system tray application with file-based logging. The application now lives in the system tray, cannot be accidentally closed, and maintains rotating logs for debugging.

## Key Features

### 1. System Tray Integration
- **Cross-Platform Support**: Uses `github.com/getlantern/systray` for Windows, macOS, and Linux
- **Always Running**: The application runs invisibly in the system tray without a terminal window
- **Right-Click Menu** with options to:
  - View the current status
  - View/open the log file
  - Open the web interface
  - Cleanly quit the application
- **Prevents Accidental Closing**: No X button to accidentally close the app
- **Windows Console Hidden**: On Windows, the console window is automatically hidden

### 2. File-Based Logging
- **Location**: Logs are saved in the same directory as the executable as `labelgen-bridge.log`
- **Rotation**: Automatically rotates when reaching 1MB (`MaxSize: 1`)
- **Backup Management**: 
  - Keeps up to 3 backup log files (`MaxBackups: 3`)
  - Deletes logs older than 7 days (`MaxAge: 7`)
  - Automatically compresses rotated logs
- **Dual Output**: Logs are written to both file and console for debugging during development
- **Features**: Includes timestamps and file locations for each log entry

### 3. Dependencies Added
```
github.com/getlantern/systray v1.2.2  - System tray integration
gopkg.in/natefinch/lumberjack.v2 v2.2.1 - Log file rotation
```

## Files Modified/Created

### Modified Files:
1. **main.go** - Core application with:
   - Tray menu implementation (`onReady`, `onExit`)
   - HTTP server management in background goroutine
   - Logger setup with file rotation
   - Menu handlers for viewing logs and opening web interface

2. **go.mod** - Updated with new dependencies

### New Files:
1. **windows_console.go** - Windows-specific code (build-tagged)
   - Hides the console window on Windows startup
   - Uses `kernel32.dll` GetConsoleWindow and ShowWindow APIs

2. **console_stub.go** - Cross-platform stub (build-tagged)
   - No-op implementation for macOS and Linux
   - Ensures compilation on all platforms

## Build Instructions

### Local Build (Current System)
```bash
cd bridge
go build -o labelgen-bridge
```

### Cross-Platform Build
```bash
# Build for Windows (from any OS)
GOOS=windows GOARCH=amd64 go build -o bridge.exe

# Build for macOS ARM64
GOOS=darwin GOARCH=arm64 go build -o bridge

# Build for Linux
GOOS=linux GOARCH=amd64 go build -o bridge
```

### GitHub Actions
The existing GitHub Actions workflow in `.github/workflows/release.yml` automatically builds for all platforms and will work seamlessly with these changes. No modifications to the workflow are needed.

## Usage

### Starting the Application
Simply run the executable:
```bash
./labelgen-bridge        # macOS/Linux
bridge.exe              # Windows
```

### System Tray Menu
Right-click on the LabelGen Bridge icon in your system tray to access:
- **Status: Running** - Shows current status (read-only)
- **View Logs** - Opens the log file in your default editor
- **Open Web Interface** - Opens the health check endpoint
- **Quit** - Cleanly shut down the application

### Accessing the API
The application still exposes the same HTTP API on `localhost:5001`:
- `GET /health` - Health check endpoint
- `GET /printers` - List available printers
- `POST /print` - Send print jobs

## Log File Management

### Log File Location
- Windows: `%TEMP%\labelgen-bridge.exe` directory or same folder as executable
- macOS/Linux: Same directory as the `labelgen-bridge` executable

### Log Rotation Details
- **Max Size**: 1 MB per file
- **Max Backups**: 3 archived logs (e.g., `labelgen-bridge.log.1`, `.log.2`, `.log.3`)
- **Compression**: Old logs are gzip compressed
- **Retention**: Logs older than 7 days are automatically deleted

### Sample Log Output
```
2026-03-18 08:48:15 ════════════════════════════════════════════════════════════
2026-03-18 08:48:15 🖨️  LabelGen Printer Bridge - System Tray Edition
2026-03-18 08:48:15 📋 Starting on 2026-03-18 08:48:15
2026-03-18 08:48:15 📋 Operating System: darwin
2026-03-18 08:48:15 ════════════════════════════════════════════════════════════
2026-03-18 08:48:15 🖨️  Starting HTTP server on http://localhost:5001
2026-03-18 08:48:15 📋 Available endpoints:
2026-03-18 08:48:15    GET  /health   - Health check
2026-03-18 08:48:15    GET  /printers - List available printers
2026-03-18 08:48:15    POST /print    - Send print job
```

## Implementation Details

### Tray Icon
The application uses a minimal embedded PNG icon (16x16 pixels) that's generated at runtime. This ensures no external asset files are needed.

### Build Tags
- `windows_console.go`: Only compiles on Windows (`//go:build windows`)
- `console_stub.go`: Only compiles on non-Windows systems (`//go:build !windows`)

This ensures the code compiles cleanly across all platforms without conditional logic during runtime.

### Graceful Shutdown
When quitting via the tray menu:
1. HTTP server is closed (in-flight requests complete)
2. Log file is flushed and closed
3. System tray is cleaned up
4. Application exits cleanly

## Testing

On macOS/Linux, you can test the application (though the tray menu will only work with a proper GUI environment):
```bash
go build -o labelgen-bridge
./labelgen-bridge
```

For a quick test of functionality without running the full tray:
```bash
# In another terminal
curl http://localhost:5001/health
curl http://localhost:5001/printers
```

## Future Enhancements

Possible future improvements:
- Add "Start on Boot" functionality
- System notifications for print job completion
- Printer status in tray tooltip
- Configuration UI accessible from tray menu
- Performance metrics in log output

## Compatibility

- **Windows**: 7, 8, 8.1, 10, 11 (x86_64)
- **macOS**: 10.12+ (ARM64/Intel)
- **Linux**: Most distributions (x86_64)

## Troubleshooting

### Can't find the tray icon
- On Windows: Check the taskbar in the bottom-right corner
- On macOS: Check the menu bar in the top-right corner
- On Linux: Check your notification area (varies by desktop environment)

### Logs growing too large
The application automatically manages log rotation at 1MB. Old logs are compressed and deleted after 7 days.

### Need to debug without tray
Temporarily modify the `main()` function to comment out `systray.Run()` and use `log.Println()` for console output.
