# 🚀 CybrTech - Simplified Workflow

You now only need **two commands** to develop and build CybrTech:

## ⚡ Quick Start

### Development Mode
```bash
npm run tauri dev
```

That's it! This command will:
1. ✅ Create Python virtual environment (if needed)
2. ✅ Install all npm dependencies
3. ✅ Install all Python dependencies
4. ✅ Start the Python backend server
5. ✅ Start the frontend dev server
6. ✅ Launch the Tauri desktop app

### Production Build
```bash
npm run tauri build
```

This command will:
1. ✅ Create Python virtual environment (if needed)
2. ✅ Install all dependencies
3. ✅ Build the frontend
4. ✅ Build the desktop app binary

## 📋 What Happens Automatically

### On Windows
```
npm run tauri dev
  ↓
Runs: python setup-env.py --dev
  ↓
  ├─ Creates cybrtech-env\ (if missing)
  ├─ Installs npm packages
  ├─ Installs Python packages
  ├─ Starts backend server (Python)
  ├─ Starts frontend dev server (Vite)
  └─ Returns control to Tauri
  ↓
Tauri starts the desktop app
  ↓
App connects to frontend dev server on port 1420
```

### On Linux
```
npm run tauri dev
  ↓
Runs: python setup-env.py --dev
  ↓
  ├─ Creates cybrtech-env/ (if missing)
  ├─ Installs npm packages
  ├─ Installs Python packages
  ├─ Starts backend server (Python)
  ├─ Starts frontend dev server (Vite)
  └─ Returns control to Tauri
  ↓
Tauri starts the desktop app
  ↓
App connects to frontend dev server on port 1420
```

## 🎯 That's All You Need!

No more:
- ~~`python setup-build.py`~~
- ~~`python init.py`~~
- ~~`python build.py --dev`~~
- ~~Manual terminal management~~
- ~~Separate dependency installation~~

**Just use:**
- `npm run tauri dev` - Development
- `npm run tauri build` - Build

## 📦 Building for Your Platform

### Windows
```bash
npm run tauri build
```
Creates:
- `.msi` installer
- NSIS `.exe` setup

### Linux
```bash
npm run tauri build
```
Creates:
- `.deb` package (Ubuntu/Debian)
- `.AppImage` (portable)

## 🛠️ Advanced: Manual Control

If you need more control, you can run the setup script separately:

```bash
# Just setup without running Tauri
python setup-env.py --build

# Or manually start services
cd src-tauri/cybrtech-tools
cybrtech-env\Scripts\activate.bat  # Windows
source cybrtech-env/bin/activate  # Linux/macOS
python cybrtech_server.py
```

## ✓ First Time Only

The first time you run `npm run tauri dev`, it will take longer because it's:
- Creating the virtual environment
- Installing all packages
- Starting all services

Subsequent runs are faster since everything is already set up.

## 🐛 If Something Goes Wrong

### "Virtual environment not found"
Just run the command again:
```bash
npm run tauri dev
```

### "Port already in use"
The dev server on port 1420 might already be running from a previous session:
```bash
# Windows
netstat -ano | findstr :1420
taskkill /PID <PID> /F

# Linux/macOS
lsof -i :1420
kill -9 <PID>
```

### "Dependencies not installed"
Run the command again. The setup script will retry installation:
```bash
npm run tauri dev
```

## 📚 File Structure

- **setup-env.py** - Automatic setup and service manager
- **src-tauri/tauri.conf.json** - Configured to use setup-env.py
- **package.json** - Contains npm scripts

## ✨ Summary

**Old workflow:**
```bash
python verify_environment.py
python setup-build.py
python build.py --dev
npm run tauri build
```

**New workflow:**
```bash
npm run tauri dev
npm run tauri build
```

That's it! 🎉
