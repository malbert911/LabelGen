# LabelGen Release Guide

This document explains how to create and publish releases for LabelGen.

## Automated Releases with GitHub Actions

LabelGen uses GitHub Actions to automatically build executables for all platforms and attach them to releases.

### Creating a Release

#### Method 1: GitHub Web Interface (Recommended)

1. Go to your repository on GitHub
2. Click on "Releases" in the right sidebar
3. Click "Draft a new release"
4. Click "Choose a tag" and create a new tag (e.g., `v1.0.0`)
5. Fill in the release title (e.g., "LabelGen v1.0.0")
6. Add release notes describing changes
7. Click "Publish release"

The GitHub Actions workflow will automatically:
- Build Django executables for Windows, macOS (ARM64), and Linux
- Build Go bridge executables for all platforms
- Create distribution packages with README files
- Attach all executables to the release

#### Method 2: GitHub CLI

```bash
# Install GitHub CLI if needed
# macOS: brew install gh
# Windows: winget install GitHub.cli

# Create and publish a release
gh release create v1.0.0 \
  --title "LabelGen v1.0.0" \
  --notes "Release notes here"

# The workflow will automatically build and upload assets
```

#### Method 3: Git Command Line

```bash
# Create and push a tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# Then create the release on GitHub web interface
```

### Release Assets

After the workflow completes, the release will include:

**Individual Executables:**
- `LabelGen-windows-amd64.exe` - Django app for Windows
- `LabelGen-darwin-arm64` - Django app for macOS (Apple Silicon)
- `LabelGen-linux-amd64` - Django app for Linux
- `bridge-windows-amd64.exe` - Printer bridge for Windows
- `bridge-darwin-arm64` - Printer bridge for macOS (Apple Silicon)
- `bridge-darwin-amd64` - Printer bridge for macOS (Intel)
- `bridge-linux-amd64` - Printer bridge for Linux

**Distribution Packages (ZIP):**
- `LabelGen-windows-amd64.zip` - Complete package for Windows
- `LabelGen-darwin-arm64.zip` - Complete package for macOS (Apple Silicon)
- `LabelGen-linux-amd64.zip` - Complete package for Linux

Each ZIP contains:
- Platform-specific LabelGen executable
- Platform-specific bridge executable
- README.txt with setup instructions

## Manual Builds

If you need to build locally without using GitHub Actions:

### Windows

```cmd
# Build both Django and Go executables
build-windows.bat

# Output will be in: backend\dist\
```

### macOS/Linux

```bash
# Build for current platform + Windows bridge
./build.sh

# Output will be in: backend/dist/
```

### Cross-Platform Go Builds

The Go bridge can be built for any platform:

```bash
cd bridge

# Windows
GOOS=windows GOARCH=amd64 go build -o bridge.exe main.go

# macOS (Apple Silicon)
GOOS=darwin GOARCH=arm64 go build -o bridge-darwin-arm64 main.go

# macOS (Intel)
GOOS=darwin GOARCH=amd64 go build -o bridge-darwin-amd64 main.go

# Linux
GOOS=linux GOARCH=amd64 go build -o bridge-linux-amd64 main.go
```

### Django Executable

PyInstaller can only build for the current platform. To create executables for all platforms, you need to run the build on each platform:

```bash
cd backend
python build_exe.py
```

## Version Numbering

LabelGen follows [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes

### Current Version

The version is defined in:
- `bridge/main.go` - Line 440 (in version field)
- GitHub release tag (e.g., `v1.0.0`)

Update both when creating a release.

## Release Checklist

Before creating a release:

- [ ] All tests pass
- [ ] Documentation is up to date (README.md, BUILD.md, etc.)
- [ ] PROGRESS.md reflects current state
- [ ] Version number updated in bridge/main.go
- [ ] CHANGELOG or release notes prepared
- [ ] Manual testing completed on target platforms
- [ ] Database migrations tested
- [ ] Printer integration tested (debug printer minimum)

## Testing Releases

### Local Testing Before Release

1. **Build locally:**
   ```bash
   ./build.sh  # macOS/Linux
   build-windows.bat  # Windows
   ```

2. **Test the executable:**
   ```bash
   cd backend/dist
   ./LabelGen  # macOS/Linux
   LabelGen.exe  # Windows
   ```

3. **Verify:**
   - System tray icon appears
   - Web interface opens (http://localhost:8001)
   - Database created (db.sqlite3)
   - Migrations applied automatically
   - Config created with defaults
   - Debug printer works

### Testing GitHub Release Assets

1. Download the ZIP for your platform from the release
2. Extract to a clean directory
3. Run the executable
4. Verify all functionality works

## Troubleshooting

### Workflow Fails to Build

Check the Actions tab on GitHub for error logs:
- Python/Go installation issues
- Dependency installation failures
- Build script errors

### Missing Executables in Release

Verify that:
- The workflow completed successfully
- All jobs finished (check Actions tab)
- The GITHUB_TOKEN has permission to upload release assets

### Manual Upload Required

If automated upload fails, you can manually upload:

```bash
# Build locally
./build.sh

# Upload using GitHub CLI
gh release upload v1.0.0 backend/dist/LabelGen
gh release upload v1.0.0 bridge/bridge
```

## CI/CD Integration

The workflow can be extended for:

### Automated Testing Before Release

Add a test job before building:

```yaml
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.12'
    - run: |
        pip install -r backend/requirements.txt
        cd backend
        python manage.py test
```

### Pre-release Builds

Trigger builds on push to main:

```yaml
on:
  push:
    branches: [main]
  release:
    types: [created]
```

### Nightly Builds

Create nightly pre-releases:

```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight
```

## Distribution

### For End Users

Provide these download options:

1. **Easy Install (Recommended):** Download platform-specific ZIP
2. **Individual Files:** Download LabelGen and bridge executables separately
3. **Source Code:** Clone repository and build manually

### For Enterprises

Consider creating:
- MSI installer for Windows (using WiX Toolset)
- DMG installer for macOS (using create-dmg)
- .deb/.rpm packages for Linux
- Docker container for server deployment

## Support

- **Issues:** Report bugs at https://github.com/your-username/LabelGen/issues
- **Discussions:** Ask questions in GitHub Discussions
- **Documentation:** See BUILD.md, README.md, and SETUP.md
