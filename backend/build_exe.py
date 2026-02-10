#!/usr/bin/env python
"""
LabelGen Build Script

Builds Windows .exe using PyInstaller with all necessary files.
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path
import importlib.util


def check_package(package_name, install_name=None):
    """Check if a package is installed without importing it."""
    if install_name is None:
        install_name = package_name
    
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        print(f"\n[ERROR] {install_name} not installed!")
        print(f"Install with: pip install {install_name}")
        return False
    return True


def main():
    """Build the executable"""
    print("=" * 60)
    print("LabelGen Build Script")
    print("=" * 60)
    
    base_dir = Path(__file__).resolve().parent
    os.chdir(base_dir)
    
    # Check if required packages are installed (without importing them)
    missing = []
    if not check_package('PyInstaller', 'pyinstaller'):
        missing.append('pyinstaller')
    if not check_package('pystray'):
        missing.append('pystray')
    if not check_package('PIL', 'Pillow'):
        missing.append('Pillow')
    
    if missing:
        print(f"\n[ERROR] Missing packages: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        sys.exit(1)
    
    print("\n[OK] All required packages found")
    
    # Clean previous builds
    print("\nCleaning previous builds...")
    for dir_name in ['build', 'dist']:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  Removed {dir_name}/")
    
    # Remove old spec file if using auto-generation
    spec_file = base_dir / 'labelgen.spec'
    
    print(f"\nBuilding with PyInstaller...")
    print(f"  Using spec file: {spec_file}")
    
    # Run PyInstaller
    try:
        subprocess.run(
            [sys.executable, '-m', 'PyInstaller', str(spec_file)],
            check=True,
            cwd=str(base_dir)
        )
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Build failed: {e}")
        sys.exit(1)
    
    # Check if build succeeded (platform-specific executable name)
    if os.name == 'nt':
        exe_name = 'LabelGen.exe'
    else:
        exe_name = 'LabelGen'
    
    exe_path = base_dir / 'dist' / exe_name
    if not exe_path.exists():
        print(f"\n[ERROR] Build failed - executable not found at {exe_path}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("[SUCCESS] Build successful!")
    print("=" * 60)
    print(f"\nExecutable: {exe_path}")
    print(f"Size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
    
    # Make executable on Unix systems
    if os.name != 'nt':
        import stat
        exe_path.chmod(exe_path.stat().st_mode | stat.S_IEXEC)
    
    # Create a README for distribution
    readme_path = base_dir / 'dist' / 'README.txt'
    with open(readme_path, 'w') as f:
        f.write("""LabelGen - Inventory Label Printing System
==========================================

Quick Start:
1. Double-click LabelGen.exe to start the application
2. On first run, migrations will be applied automatically (takes a few seconds)
3. Look for the LabelGen icon in your system tray (bottom-right)
4. Right-click the tray icon and select "Open LabelGen"
5. Configure printers in Printer Settings
6. Start using the application!

First Run Notes:
- The database (db.sqlite3) will be created automatically
- Migrations are applied on every startup (safe to run multiple times)
- Initial configuration is created with defaults (serial starts at 500)
- Check the console window for startup status messages

System Tray Menu:
- Open LabelGen: Opens the main application in your browser
- Admin Panel: Opens the admin interface (default password: admin)
- Printer Settings: Configure your label printers
- Start/Stop Server: Manually control the Django server
- Quit: Stop the server and close the application

Requirements:
- The Printer Bridge must also be running for printing functionality
- See bridge/README.md for bridge setup instructions

Database:
- The database (db.sqlite3) will be created in the same folder as this executable
- This ensures your data persists between runs
- To backup your data, simply copy db.sqlite3 to a safe location

Note: The server runs on http://127.0.0.1:8001/

For support, see the documentation in the source repository.
""")
    
    print(f"\nCreated README.txt in dist/")
    
    print("\nDistribution files:")
    print(f"  - LabelGen.exe ({exe_path.stat().st_size / (1024*1024):.1f} MB)")
    print(f"  - README.txt")
    
    print("\nNext steps:")
    print("  1. Test the executable: cd dist && ./LabelGen.exe")
    print("  2. Make sure the Printer Bridge is also running")
    print("  3. Distribute the dist/ folder to users")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
