#!/usr/bin/env python3
"""
CybrTech Environment Setup & Service Manager

Automatically handles:
1. Virtual environment creation/activation
2. Dependency installation
3. Backend server startup (for development)
4. Frontend dev server startup (for development)

Usage:
    python setup-env.py --dev       # Development mode: setup + start services
    python setup-env.py --build     # Build mode: setup only
    python setup-env.py --check     # Check setup status
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
import time
import signal

class EnvironmentManager:
    """Manage CybrTech environment setup and services."""
    
    def __init__(self):
        self.system = platform.system()
        self.root = Path(__file__).parent
        self.venv_path = self.root / 'src-tauri' / 'cybrtech-tools' / 'cybrtech-env'
        self.python_exe = self.get_python_exe()
        self.success = True
        self.backend_process = None
        self.frontend_process = None
    
    def get_python_exe(self) -> Path:
        """Get the Python executable path in the virtual environment."""
        if self.system == 'Windows':
            return self.venv_path / 'Scripts' / 'python.exe'
        else:
            return self.venv_path / 'bin' / 'python'
    
    def log(self, message: str, prefix: str = "▶"):
        """Print a formatted log message."""
        print(f"{prefix} {message}")
    
    def create_venv(self) -> bool:
        """Create Python virtual environment if it doesn't exist."""
        if self.venv_path.exists():
            self.log(f"Virtual environment exists", "✓")
            return True
        
        self.log(f"Creating virtual environment at {self.venv_path}")
        python_cmd = 'python3' if self.system != 'Windows' else 'python'
        
        try:
            result = subprocess.run(
                [python_cmd, '-m', 'venv', str(self.venv_path)],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.log("Virtual environment created", "✓")
                return True
            else:
                self.log(f"Failed to create virtual environment: {result.stderr}", "✗")
                return False
        except Exception as e:
            self.log(f"Error creating virtual environment: {e}", "✗")
            return False
    
    def install_dependencies(self) -> bool:
        """Install npm and Python dependencies."""
        # Install npm dependencies
        self.log("Installing npm dependencies")
        try:
            result = subprocess.run(
                ['npm', 'install'],
                cwd=self.root,
                capture_output=True,
                timeout=300
            )
            if result.returncode == 0:
                self.log("npm dependencies installed", "✓")
            else:
                self.log("npm install had issues", "⚠")
        except Exception as e:
            self.log(f"Error installing npm dependencies: {e}", "⚠")
        
        # Install Python dependencies
        req_file = self.root / 'src-tauri' / 'cybrtech-tools' / 'requirements.txt'
        if not req_file.exists():
            self.log("requirements.txt not found, skipping Python dependencies", "⚠")
            return True
        
        self.log("Installing Python dependencies")
        try:
            # Upgrade pip first
            subprocess.run(
                [str(self.python_exe), '-m', 'pip', 'install', '--upgrade', 'pip'],
                capture_output=True,
                timeout=60
            )
            
            # Install requirements
            result = subprocess.run(
                [str(self.python_exe), '-m', 'pip', 'install', '-r', str(req_file)],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.log("Python dependencies installed", "✓")
                return True
            else:
                self.log("Python dependency installation had issues", "⚠")
                return True  # Non-blocking
        except Exception as e:
            self.log(f"Error installing Python dependencies: {e}", "⚠")
            return True  # Non-blocking
    
    def start_backend_server(self) -> bool:
        """Start the Python backend server in background."""
        self.log("Starting backend server on port 8888")
        
        server_script = self.root / 'src-tauri' / 'cybrtech-tools' / 'cybrtech_server.py'
        if not server_script.exists():
            self.log("Backend server script not found", "⚠")
            return False
        
        try:
            if self.system == 'Windows':
                # On Windows, start in a separate console window
                self.backend_process = subprocess.Popen(
                    [str(self.python_exe), str(server_script)],
                    cwd=self.root / 'src-tauri' / 'cybrtech-tools',
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                # On Unix, start in background
                self.backend_process = subprocess.Popen(
                    [str(self.python_exe), str(server_script)],
                    cwd=self.root / 'src-tauri' / 'cybrtech-tools',
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid
                )
            
            # Give it time to start
            time.sleep(2)
            
            if self.backend_process.poll() is None:
                self.log("Backend server started (PID: {})".format(self.backend_process.pid), "✓")
                return True
            else:
                self.log("Backend server failed to start", "✗")
                return False
        except Exception as e:
            self.log(f"Error starting backend server: {e}", "✗")
            return False
    
    def start_frontend_dev(self) -> bool:
        """Start the frontend development server."""
        self.log("Starting frontend dev server")
        
        try:
            self.frontend_process = subprocess.Popen(
                ['npm', 'run', 'dev'],
                cwd=self.root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            time.sleep(2)
            
            if self.frontend_process.poll() is None:
                self.log("Frontend dev server started", "✓")
                return True
            else:
                self.log("Frontend dev server failed to start", "✗")
                return False
        except Exception as e:
            self.log(f"Error starting frontend dev server: {e}", "✗")
            return False
    
    def check_setup(self) -> bool:
        """Check if environment is properly set up."""
        self.log("Checking environment setup")
        
        checks = [
            ("Virtual environment", self.venv_path.exists()),
            ("Python executable", self.python_exe.exists()),
            ("package.json", (self.root / 'package.json').exists()),
            ("tauri.conf.json", (self.root / 'src-tauri' / 'tauri.conf.json').exists()),
        ]
        
        all_ok = True
        for name, exists in checks:
            if exists:
                self.log(f"{name}: OK", "✓")
            else:
                self.log(f"{name}: MISSING", "✗")
                all_ok = False
        
        return all_ok
    
    def setup_for_build(self) -> bool:
        """Set up environment for building."""
        print(f"\n{'='*60}")
        print("CybrTech - Build Mode Setup")
        print(f"{'='*60}\n")
        
        if not self.create_venv():
            self.success = False
            return False
        
        if not self.install_dependencies():
            self.success = False
            return False
        
        self.log("Environment ready for build", "✓")
        return True
    
    def setup_for_dev(self) -> bool:
        """Set up environment and start services for development."""
        print(f"\n{'='*60}")
        print("CybrTech - Development Mode Setup")
        print(f"{'='*60}\n")
        
        if not self.create_venv():
            self.success = False
            return False
        
        if not self.install_dependencies():
            self.success = False
        
        # Start backend server
        if not self.start_backend_server():
            self.log("Warning: Backend server failed to start", "⚠")
        
        # Start frontend dev server and wait for it
        self.log("Starting Vite development server...")
        if not self.start_frontend_dev():
            self.log("Frontend dev server failed to start", "✗")
            self.cleanup()
            return False
        
        return True
    
    def cleanup(self):
        """Kill background processes."""
        if self.backend_process:
            try:
                if self.system == 'Windows':
                    self.backend_process.terminate()
                else:
                    import signal as sig
                    os.killpg(os.getpgid(self.backend_process.pid), sig.SIGTERM)
            except:
                pass
        
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
            except:
                pass
    
    def main(self, args: list) -> int:
        """Main entry point."""
        if '--check' in args:
            return 0 if self.check_setup() else 1
        elif '--build' in args:
            return 0 if self.setup_for_build() else 1
        elif '--dev' in args:
            try:
                if self.setup_for_dev():
                    # Don't wait for frontend process - let it run in background
                    # Tauri will take over from here
                    return 0
                else:
                    return 1
            except KeyboardInterrupt:
                print("\n\nShutting down...")
                self.cleanup()
                return 0
        else:
            print("Usage:")
            print("  python setup-env.py --dev       # Development mode")
            print("  python setup-env.py --build     # Build mode")
            print("  python setup-env.py --check     # Check setup")
            return 1

def main():
    """Entry point."""
    try:
        manager = EnvironmentManager()
        return manager.main(sys.argv[1:])
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
