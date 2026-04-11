#!/usr/bin/env python3
"""
Pre-build setup script for CybrTech

This script ensures all system and project dependencies are installed
before running `npm run tauri build` or `npm run tauri dev`

Usage:
    python setup-build.py
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

class BuildSetup:
    """Manage build dependencies for cross-platform Tauri app."""
    
    def __init__(self):
        self.system = platform.system()
        self.success = True
    
    def run_command(self, cmd: list, description: str, check: bool = True) -> bool:
        """Run a command and return success status."""
        print(f"\n▶ {description}...")
        try:
            result = subprocess.run(cmd, check=False)
            if result.returncode == 0:
                print(f"  ✓ {description} completed")
                return True
            else:
                if check:
                    print(f"  ✗ {description} failed")
                    return False
                else:
                    print(f"  ⚠ {description} had issues (non-critical)")
                    return True
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False
    
    def check_command_exists(self, cmd: str) -> bool:
        """Check if a command exists."""
        try:
            subprocess.run(
                [cmd, '--version'] if cmd != 'sudo' else ['sudo', '-n', 'true'],
                capture_output=True,
                timeout=5
            )
            return True
        except:
            return False
    
    def setup_windows(self):
        """Setup Windows build environment."""
        print("\n" + "="*60)
        print("🪟 WINDOWS BUILD SETUP")
        print("="*60)
        
        # Check for Visual Studio Build Tools
        print("\nChecking for Visual Studio Build Tools...")
        try:
            result = subprocess.run(
                ['where', 'cl.exe'],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                print("  ✓ C++ compiler found (cl.exe)")
            else:
                print("  ✗ C++ compiler not found")
                print("\n  Please install one of the following:")
                print("    • Visual Studio (with C++ support)")
                print("    • Visual Studio Build Tools")
                print("    • Or: choco install visualstudio2019-workload-nativedesktop")
                self.success = False
        except Exception as e:
            print(f"  ⚠ Could not verify C++ compiler: {e}")
        
        print("\n  Windows is ready for Tauri development")
    
    def setup_linux(self):
        """Setup Linux build environment."""
        print("\n" + "="*60)
        print("🐧 LINUX BUILD SETUP")
        print("="*60)
        
        # Detect distribution
        distro = self.detect_linux_distro()
        
        if distro in ['ubuntu', 'debian']:
            self.setup_debian_based()
        elif distro in ['fedora', 'rhel', 'centos']:
            self.setup_fedora_based()
        else:
            print(f"\n  ⚠ Unknown Linux distribution: {distro}")
            print("  Please ensure these packages are installed:")
            self.print_linux_dependencies()
    
    def detect_linux_distro(self) -> str:
        """Detect Linux distribution."""
        try:
            with open('/etc/os-release', 'r') as f:
                content = f.read().lower()
                if 'ubuntu' in content:
                    return 'ubuntu'
                elif 'debian' in content:
                    return 'debian'
                elif 'fedora' in content:
                    return 'fedora'
                elif 'rhel' in content or 'red hat' in content:
                    return 'rhel'
                elif 'centos' in content:
                    return 'centos'
        except:
            pass
        return 'unknown'
    
    def setup_debian_based(self):
        """Setup Debian/Ubuntu build environment."""
        print("\nDetected: Debian/Ubuntu based system")
        
        deps = [
            'build-essential',
            'libssl-dev',
            'libgtk-3-dev',
            'webkit2gtk-4.1',
            'libwebkit2gtk-4.1-dev',
            'libappindicator3-dev',
            'librsvg2-dev'
        ]
        
        print(f"\nRequired packages: {', '.join(deps)}")
        
        if not self.check_command_exists('sudo'):
            print("\n  ⚠ sudo not available. Please manually install:")
            print(f"    sudo apt-get update")
            print(f"    sudo apt-get install -y {' '.join(deps)}")
            self.success = False
            return
        
        # Check if packages are already installed
        print("\nChecking installed packages...")
        missing = []
        for pkg in deps:
            result = subprocess.run(
                ['dpkg', '-l', f'*{pkg}*'],
                capture_output=True
            )
            if result.returncode != 0:
                missing.append(pkg)
        
        if missing:
            print(f"  Missing packages: {', '.join(missing)}")
            
            # Ask user permission to install
            response = input("\n  Install missing packages? (y/n): ").strip().lower()
            if response == 'y':
                print("\n  Updating package list...")
                self.run_command(
                    ['sudo', 'apt-get', 'update'],
                    "Package list update",
                    check=False
                )
                
                print(f"  Installing missing packages...")
                self.run_command(
                    ['sudo', 'apt-get', 'install', '-y'] + missing,
                    "Package installation",
                    check=False
                )
            else:
                print("\n  Skipping package installation")
                print("  Note: You may need to install packages manually if build fails")
        else:
            print("  ✓ All required packages are installed")
    
    def setup_fedora_based(self):
        """Setup Fedora/RHEL build environment."""
        print("\nDetected: Fedora/RHEL based system")
        
        deps = [
            'gcc',
            'gcc-c++',
            'make',
            'openssl-devel',
            'gtk3-devel',
            'webkit2gtk4.1-devel'
        ]
        
        print(f"\nRequired packages: {', '.join(deps)}")
        
        if not self.check_command_exists('sudo'):
            print("\n  ⚠ sudo not available. Please manually install:")
            print(f"    sudo dnf install {' '.join(deps)}")
            self.success = False
            return
        
        response = input("\n  Install packages? (y/n): ").strip().lower()
        if response == 'y':
            self.run_command(
                ['sudo', 'dnf', 'install', '-y'] + deps,
                "Package installation",
                check=False
            )
        else:
            print("  Skipping package installation")
    
    def print_linux_dependencies(self):
        """Print Linux dependencies."""
        print("\n  Ubuntu/Debian:")
        print("    sudo apt-get update")
        print("    sudo apt-get install build-essential libssl-dev libgtk-3-dev \\")
        print("      webkit2gtk-4.1 libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev")
        print("\n  Fedora/RHEL:")
        print("    sudo dnf install gcc gcc-c++ make openssl-devel \\")
        print("      gtk3-devel webkit2gtk4.1-devel")
    
    def setup_macos(self):
        """Setup macOS build environment."""
        print("\n" + "="*60)
        print("🍎 MACOS BUILD SETUP")
        print("="*60)
        
        print("\nChecking Xcode Command Line Tools...")
        result = subprocess.run(
            ['xcode-select', '-p'],
            capture_output=True
        )
        
        if result.returncode == 0:
            print("  ✓ Xcode Command Line Tools found")
        else:
            print("  ✗ Xcode Command Line Tools not found")
            print("\n  Install with: xcode-select --install")
            self.success = False
    
    def setup_node_and_rust(self):
        """Setup Node.js and Rust."""
        print("\n" + "="*60)
        print("🔧 PROJECT DEPENDENCIES")
        print("="*60)
        
        # Check Node.js
        print("\nChecking Node.js...")
        if self.check_command_exists('node'):
            result = subprocess.run(
                ['node', '--version'],
                capture_output=True,
                text=True
            )
            print(f"  ✓ {result.stdout.strip()}")
        else:
            print("  ✗ Node.js not found")
            print("    Install from: https://nodejs.org/")
            self.success = False
        
        # Check Rust
        print("\nChecking Rust...")
        if self.check_command_exists('rustc'):
            result = subprocess.run(
                ['rustc', '--version'],
                capture_output=True,
                text=True
            )
            print(f"  ✓ {result.stdout.strip()}")
        else:
            print("  ✗ Rust not found")
            print("    Install from: https://rustup.rs/")
            self.success = False
        
        # Install npm dependencies
        print("\nInstalling npm dependencies...")
        root = Path(__file__).parent
        if (root / 'package.json').exists():
            self.run_command(['npm', 'install'], "npm install")
        else:
            print("  ⚠ package.json not found")
    
    def setup_python_env(self):
        """Setup Python virtual environment."""
        print("\n" + "="*60)
        print("🐍 PYTHON ENVIRONMENT")
        print("="*60)
        
        root = Path(__file__).parent
        venv_path = root / 'src-tauri' / 'cybrtech-tools' / 'cybrtech-env'
        
        if venv_path.exists():
            print(f"  ✓ Virtual environment exists")
        else:
            print(f"  Creating virtual environment...")
            python_cmd = 'python3' if self.system != 'Windows' else 'python'
            self.run_command(
                [python_cmd, '-m', 'venv', str(venv_path)],
                "Virtual environment creation"
            )
        
        # Install Python dependencies
        req_file = root / 'src-tauri' / 'cybrtech-tools' / 'requirements.txt'
        if req_file.exists():
            if self.system == 'Windows':
                python_exe = venv_path / 'Scripts' / 'python.exe'
            else:
                python_exe = venv_path / 'bin' / 'python'
            
            self.run_command(
                [str(python_exe), '-m', 'pip', 'install', '--upgrade', 'pip'],
                "Upgrading pip",
                check=False
            )
            
            self.run_command(
                [str(python_exe), '-m', 'pip', 'install', '-r', str(req_file)],
                "Installing Python dependencies",
                check=False
            )
    
    def run(self):
        """Run full setup."""
        print("""
╔════════════════════════════════════════════════════════╗
║   CybrTech Build Setup - Cross-Platform                ║
║                                                        ║
║   This script prepares your system for building        ║
║   CybrTech on Windows, Linux, or macOS                 ║
╚════════════════════════════════════════════════════════╝
        """)
        
        # Platform-specific setup
        if self.system == 'Windows':
            self.setup_windows()
        elif self.system == 'Linux':
            self.setup_linux()
        elif self.system == 'Darwin':
            self.setup_macos()
        else:
            print(f"  Unknown system: {self.system}")
            self.success = False
        
        # Common setup
        self.setup_node_and_rust()
        self.setup_python_env()
        
        # Summary
        print("\n" + "="*60)
        if self.success:
            print("✓ Setup completed successfully!")
            print("\nYou can now run:")
            print("  npm run tauri dev    # Development mode")
            print("  npm run tauri build  # Production build")
        else:
            print("⚠ Setup completed with warnings")
            print("\nPlease install the missing dependencies and try again.")
        print("="*60 + "\n")
        
        return 0 if self.success else 1

def main():
    """Main entry point."""
    try:
        setup = BuildSetup()
        return setup.run()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        return 1
    except Exception as e:
        print(f"\n✗ Error during setup: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
