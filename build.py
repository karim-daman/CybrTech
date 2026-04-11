#!/usr/bin/env python3
"""
CybrTech Build Helper Script

This script simplifies building CybrTech for Windows and Linux
with all necessary dependencies and platform-specific configurations.

Usage:
    python build.py              # Build for current platform
    python build.py --setup      # Setup all dependencies first
    python build.py --dev        # Run in development mode
"""

import os
import sys
import subprocess
import platform
import argparse
from pathlib import Path

class CybrTechBuilder:
    """Build CybrTech for different platforms."""
    
    def __init__(self):
        self.system = platform.system()
        self.root = Path(__file__).parent
    
    def print_header(self, title: str):
        """Print a formatted header."""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")
    
    def run_command(self, cmd: list, description: str = "") -> bool:
        """Run a shell command."""
        if description:
            print(f"▶ {description}...")
        try:
            result = subprocess.run(cmd, cwd=self.root)
            if result.returncode == 0:
                if description:
                    print(f"✓ {description} completed")
                return True
            else:
                if description:
                    print(f"✗ {description} failed")
                return False
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
    
    def setup_dependencies(self) -> bool:
        """Run the setup-build.py script."""
        self.print_header("Setting Up Dependencies")
        
        python_cmd = 'python3' if self.system != 'Windows' else 'python'
        return self.run_command(
            [python_cmd, 'setup-build.py'],
            "Dependency setup"
        )
    
    def build_dev(self) -> bool:
        """Run Tauri in development mode."""
        self.print_header(f"Starting Development ({self.system})")
        
        print("Starting development environment...")
        print("Press Ctrl+C to stop\n")
        
        return self.run_command(['npm', 'run', 'tauri', 'dev'])
    
    def build_production(self) -> bool:
        """Build Tauri application for production."""
        self.print_header(f"Building Production Binary ({self.system})")
        
        print(f"Building for {self.system}...")
        if not self.run_command(['npm', 'run', 'tauri', 'build']):
            return False
        
        # Show build output location
        target_dir = self.root / 'src-tauri' / 'target' / 'release'
        print(f"\n✓ Build completed!")
        print(f"  Output location: {target_dir}")
        
        if self.system == 'Windows':
            print("\n  Installers created:")
            print("    • .msi installer")
            print("    • NSIS installer (.exe)")
        elif self.system == 'Linux':
            print("\n  Packages created:")
            print("    • .deb package (Ubuntu/Debian)")
            print("    • AppImage (portable)")
        elif self.system == 'Darwin':
            print("\n  Package created:")
            print("    • .dmg installer (macOS)")
        
        return True
    
    def verify_setup(self) -> bool:
        """Verify that the environment is ready."""
        self.print_header("Verifying Setup")
        
        checks = [
            ('Python', 'python3' if self.system != 'Windows' else 'python'),
            ('Node.js', 'node'),
            ('npm', 'npm'),
            ('Rust', 'rustc'),
        ]
        
        all_ok = True
        for name, cmd in checks:
            try:
                result = subprocess.run(
                    [cmd, '--version'],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    version = result.stdout.decode().split('\n')[0]
                    print(f"✓ {name}: {version}")
                else:
                    print(f"✗ {name}: Not configured properly")
                    all_ok = False
            except FileNotFoundError:
                print(f"✗ {name}: Not found")
                all_ok = False
            except Exception as e:
                print(f"✗ {name}: Error - {e}")
                all_ok = False
        
        # Check project files
        print()
        files = [
            ('package.json', self.root / 'package.json'),
            ('Cargo.toml', self.root / 'src-tauri' / 'Cargo.toml'),
            ('tauri.conf.json', self.root / 'src-tauri' / 'tauri.conf.json'),
        ]
        
        for name, path in files:
            if path.exists():
                print(f"✓ {name}")
            else:
                print(f"✗ {name}: Not found at {path}")
                all_ok = False
        
        return all_ok
    
    def main(self, args):
        """Main entry point."""
        print("""
╔════════════════════════════════════════════════════════╗
║         CybrTech Build Helper                          ║
║                                                        ║
║     Building for: """ + f"{self.system:<25} ║")
        print("╚════════════════════════════════════════════════════════╝")
        
        # Verify setup
        if not self.verify_setup():
            print("\n✗ Environment verification failed!")
            print("  Run: python setup-build.py")
            return 1
        
        # Setup if requested
        if args.setup:
            if not self.setup_dependencies():
                return 1
        
        # Run requested action
        if args.dev:
            return 0 if self.build_dev() else 1
        else:
            return 0 if self.build_production() else 1

def main():
    """Entry point."""
    parser = argparse.ArgumentParser(
        description='CybrTech Build Helper'
    )
    parser.add_argument(
        '--setup',
        action='store_true',
        help='Setup all dependencies before building'
    )
    parser.add_argument(
        '--dev',
        action='store_true',
        help='Run in development mode instead of building'
    )
    
    args = parser.parse_args()
    
    try:
        builder = CybrTechBuilder()
        return builder.main(args)
    except KeyboardInterrupt:
        print("\n\nBuild cancelled by user")
        return 0
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
