#!/usr/bin/env node
/**
 * Cross-platform setup launcher
 * 
 * This script detects the OS and calls the correct Python command
 * to run setup-env.py
 * 
 * Usage:
 *   node setup-dev.js --dev
 *   node setup-dev.js --build
 */

const { spawn } = require('child_process');
const os = require('os');

const args = process.argv.slice(2);
const platform = os.platform();

let pythonCmd = 'python';

// On Linux and macOS, prefer python3
if (platform === 'linux' || platform === 'darwin') {
  pythonCmd = 'python3';
}

// On Windows, use python (which is typically available)
// If python3 is available on Windows (from Microsoft Store or specific install), it would work too

const command = [pythonCmd, 'setup-env.py', ...args];

console.log(`[INFO] Platform detected: ${platform}`);
console.log(`[INFO] Using Python command: ${pythonCmd}`);
console.log(`[INFO] Running: ${command.join(' ')}\n`);

// Spawn the process and inherit stdio so we see all output
const child = spawn(command[0], command.slice(1), {
  stdio: 'inherit',
  shell: true
});

// Pass exit code through
child.on('exit', (code) => {
  process.exit(code);
});

// Handle errors
child.on('error', (err) => {
  console.error(`[ERROR] Failed to spawn process: ${err.message}`);
  process.exit(1);
});
