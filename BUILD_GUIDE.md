# CybrTech Build Guide - Windows & Linux

This guide explains how to build and run CybrTech on Windows and Linux with all dependencies properly configured.

## Quick Start

### First Time Setup
```bash
# Setup all dependencies (one time only)
python setup-build.py

# Then choose one of the following:

# Option A: Development mode (with hot reload)
python build.py --dev

# Option B: Production build
python build.py

# Option C: Manual setup + build
npm install
npm run tauri dev      # Development
npm run tauri build    # Production
```

## Prerequisites by Platform

### Windows
- **Visual Studio 2019+** or **Visual Studio Build Tools** with C++ support
  - Download: https://visualstudio.microsoft.com/downloads/
  - Or install via Chocolatey: `choco install visualstudio2019-workload-nativedesktop`
- **Node.js** 18+ (https://nodejs.org/)
- **Python** 3.9+ (https://www.python.org/)
- **Rust** latest stable (https://rustup.rs/)

### Linux (Ubuntu/Debian)
```bash
# Install build tools
sudo apt-get update
sudo apt-get install -y build-essential libssl-dev libgtk-3-dev \
  webkit2gtk-4.1 libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev

# Install Node.js (v18+)
# Install Python (3.9+)
# Install Rust via rustup
```

### Linux (Fedora/RHEL)
```bash
# Install build tools
sudo dnf install gcc gcc-c++ make openssl-devel gtk3-devel webkit2gtk4.1-devel

# Install Node.js (v18+)
# Install Python (3.9+)
# Install Rust via rustup
```

## Build Scripts

Three helper scripts are provided to simplify the build process:

### 1. `setup-build.py` - Initialize Environment

Checks and installs all required dependencies.

```bash
# Verify/install dependencies
python setup-build.py

# Features:
# ✓ Checks for Visual Studio Build Tools (Windows)
# ✓ Installs system libraries (Linux)
# ✓ Creates Python virtual environment
# ✓ Installs npm dependencies
# ✓ Installs Python dependencies
```

### 2. `build.py` - Build Helper

Simplifies building for your current platform.

```bash
# Verify setup and build
python build.py

# Setup dependencies first, then build
python build.py --setup

# Run in development mode
python build.py --dev

# Features:
# ✓ Verifies all prerequisites
# ✓ Runs Tauri dev or build
# ✓ Shows build output location
# ✓ Provides helpful error messages
```

### 3. Direct npm Commands

For more control, use npm directly:

```bash
# Development mode (hot reload)
npm run tauri dev

# Production build
npm run tauri build

# Frontend only
npm run dev       # Vite dev server
npm run build     # Build static files
npm run check     # Type checking
```

## Development Workflow

### Windows
```bash
# Terminal 1: Setup (one time)
python setup-build.py

# Terminal 2: Development
python build.py --dev

# Or manually:
npm run tauri dev
```

### Linux
```bash
# Terminal 1: Setup (one time)
python setup-build.py

# Terminal 2: Development
python build.py --dev

# Or manually:
npm run tauri dev
```

## Production Build

### Windows
```bash
# Setup (if not done before)
python setup-build.py

# Build
python build.py

# Output: src-tauri/target/release/
# - *.msi installer
# - *.exe setup file
```

### Linux
```bash
# Setup (if not done before)
python setup-build.py

# Build
python build.py

# Output: src-tauri/target/release/
# - *.deb package (Ubuntu/Debian)
# - *.AppImage (portable executable)
```

## Configuration

The build is configured in `src-tauri/tauri.conf.json`:

### Windows Configuration
```json
{
  "bundle": {
    "targets": ["msi", "nsis"],
    "windows": {
      "nsis": {
        "installerHooks": "./windows/hooks.nsh"
      }
    }
  }
}
```

### Linux Configuration
```json
{
  "bundle": {
    "linux": {
      "deb": {
        "depends": ["webkit2gtk-4.1", "libssl3"]
      }
    }
  }
}
```

## Troubleshooting

### "C++ compiler not found" (Windows)
```
✗ Solution:
  • Install Visual Studio with C++ workload
  • Or: choco install visualstudio2019-workload-nativedesktop
  • Then restart your terminal
```

### "webkit2gtk-4.1 not found" (Linux)
```
✗ Solution:
  On Ubuntu/Debian:
    sudo apt-get install webkit2gtk-4.1 libwebkit2gtk-4.1-dev

  On Fedora:
    sudo dnf install webkit2gtk4.1-devel
```

### "Port 1420 already in use"
```
✗ Solution:
  • The Vite dev server is using port 1420
  • Either kill the process using it
  • Or set a different port in tauri.conf.json

  Windows (find PID):
    netstat -ano | findstr :1420
    taskkill /PID <PID> /F

  Linux/macOS:
    lsof -i :1420
    kill -9 <PID>
```

### Virtual environment errors
```
✗ Solution:
  Recreate the virtual environment:
    rm -rf src-tauri/cybrtech-tools/cybrtech-env
    python setup-build.py
```

### Build fails with "module not found"
```
✗ Solution:
  Reinstall Python dependencies:
    cd src-tauri/cybrtech-tools
    
  Windows:
    cybrtech-env\Scripts\pip install -r requirements.txt

  Linux/macOS:
    cybrtech-env/bin/pip install -r requirements.txt
```

### Tauri dev doesn't start
```
✗ Solution:
  1. Make sure npm dependencies are installed:
     npm install

  2. Make sure the frontend builds:
     npm run build

  3. Check that the Rust build works:
     cd src-tauri
     cargo build

  4. Then try again:
     npm run tauri dev
```

## Environment Variables

Configure the build and runtime behavior:

```bash
# Backend server port
export CYBRTECH_PORT=8888

# Backend server host
export CYBRTECH_HOST=127.0.0.1

# Frontend dev port
export VITE_PORT=1420
```

Windows:
```batch
set CYBRTECH_PORT=8888
set CYBRTECH_HOST=127.0.0.1
```

## Platform-Specific Notes

### Windows Notes
- Build requires Visual Studio Build Tools or full Visual Studio
- The app is bundled as .msi and NSIS .exe files
- Windows Defender may flag the app (unsigned builds are suspicious)
- To avoid this, code sign your builds with a certificate

### Linux Notes
- Build creates both .deb (for Debian/Ubuntu) and AppImage (portable)
- Some distributions may require additional libraries
- Use `ldd` to check for missing runtime dependencies
- AppImage is self-contained and doesn't need dependencies installed

### macOS Notes (bonus support)
- Requires Xcode Command Line Tools
- App is bundled as .dmg installer
- Code signing is recommended for distribution

## Cross-Platform CI/CD

For automated builds across platforms, see `.github/workflows/build.yml`

GitHub Actions automatically tests and builds on:
- Windows (Latest)
- Linux (Ubuntu Latest)
- macOS (Latest)

Push to GitHub to trigger automated builds!

## Performance Tips

### Development
- Use `npm run tauri dev` for hot reload
- Keep the Vite dev server running
- Changes to frontend code reload instantly
- Changes to Rust code require rebuild

### Building
- Use `npm run tauri build` for optimized production binary
- Build is single-threaded by default for stability
- On slow machines, this can take 5-10 minutes
- To speed up: `cargo build --release` in parallel terminals

### Debugging
- Use `npm run tauri dev` to see console output
- Browser dev tools available in dev mode
- Check `cybrtech.log` for backend errors
- Use `RUST_LOG=debug` for Rust debugging

## Getting Help

1. **Verify environment:**
   ```bash
   python verify_environment.py
   ```

2. **Check documentation:**
   - README.md - General overview
   - CROSSPLATFORM_SETUP.md - Detailed setup
   - This file - Build guide

3. **Search logs:**
   - `cybrtech.log` - Python server logs
   - Browser console - Frontend errors
   - Terminal output - Build errors

4. **Try setup again:**
   ```bash
   python setup-build.py
   ```

## Next Steps

- Read [README.md](README.md) for project overview
- Check [CROSSPLATFORM_SETUP.md](CROSSPLATFORM_SETUP.md) for detailed environment setup
- Explore [src-tauri/tauri.conf.json](src-tauri/tauri.conf.json) for build configuration
- Create a GitHub Actions workflow for CI/CD (see `.github/workflows/build.yml`)

---

**Ready to build? Run:**
```bash
python setup-build.py
python build.py --dev
```
