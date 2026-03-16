#!/usr/bin/env python
"""
LabelGen System Tray Application

Manages Django server as a background process with system tray controls.

When bundled with PyInstaller, this runs Django directly in a thread.
When run as a script, it spawns manage.py runserver as a subprocess.
"""
import os
import sys
import subprocess
import threading
import webbrowser
import time
import traceback
from pathlib import Path

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    print("Error: Required packages not installed.")
    print("Run: pip install pystray Pillow")
    sys.exit(1)

# When frozen, we need to run Django directly, not as subprocess
IS_FROZEN = getattr(sys, 'frozen', False)


class LabelGenTrayApp:
    def __init__(self):
        self.server_process = None
        self.server_thread = None
        self.icon = None
        self.log_lock = threading.Lock()
        
        # Use executable location when frozen, script location otherwise
        if IS_FROZEN:
            self.base_dir = Path(sys.executable).resolve().parent
        else:
            self.base_dir = Path(__file__).resolve().parent
        
        self.port = 8001
        self.running = False
        self.log_path = self.base_dir / 'labelgen_tray.log'
        self.max_log_size = 1024 * 1024
        self.log('Tray app initialized')

    def _prune_log_if_needed(self):
        try:
            if self.log_path.exists() and self.log_path.stat().st_size > self.max_log_size:
                with open(self.log_path, 'rb') as f:
                    size = f.seek(0, os.SEEK_END)
                    keep_bytes = self.max_log_size // 2
                    if size > keep_bytes:
                        f.seek(-keep_bytes, os.SEEK_END)
                    else:
                        f.seek(0)
                    tail = f.read()
                with open(self.log_path, 'wb') as f:
                    f.write(b"--- truncated old logs ---\n")
                    f.write(tail)
        except Exception:
            pass

    def log(self, message):
        """Append timestamped messages to log file."""
        try:
            ts = time.strftime('%Y-%m-%d %H:%M:%S')
            line = f"[{ts}] {message}\n"
            with self.log_lock:
                self._prune_log_if_needed()
                with open(self.log_path, 'a', encoding='utf-8') as f:
                    f.write(line)
        except Exception:
            # Logging should not crash the tray
            pass

    def _capture_subprocess_output(self):
        def reader(stream, name):
            try:
                for raw in iter(stream.readline, b''):
                    if not raw:
                        break
                    text = raw.decode(errors='replace').rstrip()
                    self.log(f"{name}: {text}")
            except Exception as e:
                self.log(f"Error reading {name}: {e}")

        if self.server_process is None:
            return

        if self.server_process.stdout:
            threading.Thread(target=reader, args=(self.server_process.stdout, 'STDOUT'), daemon=True).start()
        if self.server_process.stderr:
            threading.Thread(target=reader, args=(self.server_process.stderr, 'STDERR'), daemon=True).start()

    def create_icon(self):
        """Create a simple icon for the system tray"""
        # Create a blue square with "LG" text
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), color='#3273dc')
        draw = ImageDraw.Draw(image)
        
        # Draw white text
        draw.text((10, 20), "LG", fill='white')
        
        return image
    
    def start_server(self):
        """Start the Django development server"""
        if self.server_process is not None or self.running:
            return
        
        try:
            if IS_FROZEN:
                # Running as PyInstaller bundle - run Django directly in thread
                # This prevents fork bomb by not spawning subprocess
                self.running = True
                self.server_thread = threading.Thread(target=self._run_django_frozen, daemon=True)
                self.server_thread.start()
            else:
                # Running as script - use subprocess with manage.py
                manage_py = self.base_dir / 'manage.py'
                python_exe = sys.executable
                
                cmd = [python_exe, str(manage_py), 'runserver', str(self.port), '--noreload']
                self.log(f"Starting subprocess: {cmd} cwd={self.base_dir}")
                
                # Start server in background
                startupinfo = None
                if os.name == 'nt':
                    # Hide console window on Windows
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                self.server_process = subprocess.Popen(
                    cmd,
                    cwd=str(self.base_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.DEVNULL,
                    startupinfo=startupinfo
                )
                self._capture_subprocess_output()
            
            self.running = True
            self.log(f"Server started on port {self.port}")
            # Update icon title
            if self.icon:
                self.icon.title = "LabelGen (Running)"
            
        except Exception as e:
            self.log(f"Error starting server: {e}")
            self.running = False
            print(f"Error starting server: {e}")
    
    def _run_django_frozen(self):
        """Run Django server directly when frozen (in thread)"""
        try:
            # Ensure we have usable stdout/stderr in tray mode
            if sys.stdout is None:
                sys.stdout = open(os.devnull, 'w', encoding='utf-8', errors='ignore')
            if sys.stderr is None:
                sys.stderr = open(os.devnull, 'w', encoding='utf-8', errors='ignore')

            # Set up Django
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'labelgen.settings')
            
            import django
            from django.core.management import execute_from_command_line, call_command
            
            django.setup()
            
            # Apply migrations automatically on startup
            print("Checking for migrations...")
            try:
                call_command('migrate', '--noinput', verbosity=0)
                print("✓ Migrations applied")
            except Exception as e:
                print(f"Warning: Migration error: {e}")
                self.log(f"Warning: Migration error: {e}")
            
            # Check if Config object exists, create if not
            try:
                from inventory.models import Config
                if not Config.objects.exists():
                    print("Creating initial Config...")
                    Config.objects.create()
                    print("✓ Config created")
            except Exception as e:
                print(f"Warning: Config check error: {e}")
                self.log(f"Warning: Config check error: {e}")
            
            # Run server
            sys.argv = ['manage.py', 'runserver', str(self.port), '--noreload']
            execute_from_command_line(sys.argv)
        except Exception as e:
            self.log(f"Error running Django: {e}")
            self.log(traceback.format_exc())
            print(f"Error running Django: {e}")
        finally:
            self.running = False
            self.log("Frozen Django thread exiting")
    
    def stop_server(self):
        """Stop the Django server"""
        if self.server_process:
            self.log("Stopping subprocess server")
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.log("Subprocess did not terminate, killing")
                self.server_process.kill()
            finally:
                self.server_process = None
        
        if self.running:
            self.running = False
            # Thread will exit when Django stops
        self.log("Server stopped")
                
        if self.icon:
            self.icon.title = "LabelGen (Stopped)"
    
    def open_browser(self, icon, item):
        """Open the application in default browser"""
        self.log("Open browser action")
        webbrowser.open(f'http://127.0.0.1:{self.port}/')
    
    def open_admin(self, icon, item):
        """Open admin panel in browser"""
        self.log("Open admin panel action")
        webbrowser.open(f'http://127.0.0.1:{self.port}/admin-upc/')
    
    def open_printer_settings(self, icon, item):
        """Open printer settings in browser"""
        self.log("Open printer settings action")
        webbrowser.open(f'http://127.0.0.1:{self.port}/printer-settings/')
    
    def quit_app(self, icon, item):
        """Quit the application"""
        self.log("Quit requested")
        self.stop_server()
        icon.stop()
    
    def setup_menu(self):
        """Create the system tray menu"""
        return pystray.Menu(
            pystray.MenuItem("Open LabelGen", self.open_browser, default=True),
            pystray.MenuItem("Admin Panel", self.open_admin),
            pystray.MenuItem("Printer Settings", self.open_printer_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self.quit_app)
        )
    
    def run(self):
        """Run the tray application"""
        self.log('Tray app run starting')
        # Start server automatically
        threading.Thread(target=self.start_server, daemon=True).start()
        
        # Create system tray icon
        image = self.create_icon()
        menu = self.setup_menu()
        
        self.icon = pystray.Icon(
            "LabelGen",
            image,
            "LabelGen (Starting...)",
            menu
        )
        
        # Run the icon (blocks until quit)
        self.icon.run()


def main():
    """Main entry point"""
    # Prevent multiple instances
    import socket
    try:
        # Try to bind to a specific port to ensure single instance
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lock_socket.bind(('127.0.0.1', 47200))  # Random high port for lock
    except OSError:
        print("LabelGen is already running!")
        sys.exit(0)
    
    print("Starting LabelGen...")
    app = LabelGenTrayApp()
    app.log('Main started')

    try:
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        app.log('KeyboardInterrupt: shutting down')
        app.stop_server()
    except Exception as e:
        print(f"Error: {e}")
        app.log(f"Fatal exception in main: {e}")
        app.stop_server()
        sys.exit(1)
    finally:
        lock_socket.close()


if __name__ == '__main__':
    main()
