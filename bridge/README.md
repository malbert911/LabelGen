# LabelGen Printer Bridge (Go)

## Overview

This directory will contain the Go-based local printer bridge that listens on `localhost:5000` and communicates with system printers.

## Planned Features

- **Printer Discovery**: List available system printers
- **Print Command Handler**: Accept label print commands from Django backend
- **Cross-Platform Support**: Windows `.exe`, macOS, and Linux binaries

## Status

🚧 **Coming Soon** - Will be implemented in Phase 4

## Endpoints (Planned)

- `GET /printers` - List available system printers
- `POST /print` - Send print command to selected printer

## Development Notes

- Port: `5000`
- Format: ZPL (pending client confirmation on printer model)
- CORS: Enabled for `localhost` Django requests
