#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::Serialize;
use std::env;
use std::io::{BufRead, BufReader, Read, Write};
use std::net::TcpStream;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::time::{SystemTime, UNIX_EPOCH};
use std::time::{Duration, Instant};
#[allow(unused_imports)]
use tauri::{Emitter, Manager, State};

#[cfg(windows)]
use std::os::windows::process::CommandExt;

#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x08000000;

struct AppState {
    server_process: Mutex<Option<Child>>,
    mcp_process: Mutex<Option<Child>>,
}

#[derive(Clone, Serialize)]
struct ProcessLogEvent {
    source: String,
    stream: String,
    message: String,
}

#[derive(Serialize)]
struct RuntimeStatus {
    server_running: bool,
    server_healthy: bool,
    mcp_running: bool,
}

/// Finds the first system Python executable available on PATH.
fn find_python() -> Option<&'static str> {
    for candidate in &["py", "python", "python3"] {
        let ok = Command::new(candidate)
            .arg("--version")
            .output()
            .map(|o| o.status.success())
            .unwrap_or(false);
        if ok {
            return Some(candidate);
        }
    }
    None
}

#[allow(unused_variables)]
fn resolve_cybrtech_path(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    #[cfg(debug_assertions)]
    {
        Ok(PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("cybrtech-tools"))
    }
    #[cfg(not(debug_assertions))]
    {
        let resource_dir = app
            .path()
            .resource_dir()
            .map_err(|e| format!("Could not resolve resource dir: {e}"))?;
        Ok(resource_dir.join("cybrtech-tools"))
    }
}

#[allow(unused_variables)]
fn resolve_python_runtime_path(app: &tauri::AppHandle) -> Result<PathBuf, String> {
    #[cfg(debug_assertions)]
    {
        Ok(PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("python-runtime"))
    }
    #[cfg(not(debug_assertions))]
    {
        let resource_dir = app
            .path()
            .resource_dir()
            .map_err(|e| format!("Could not resolve resource dir: {e}"))?;
        Ok(resource_dir.join("python-runtime"))
    }
}

fn wait_for_port(port: u16, timeout_secs: u64) -> Result<(), String> {
    let addr = format!("127.0.0.1:{port}");
    let deadline = Instant::now() + Duration::from_secs(timeout_secs);
    while Instant::now() < deadline {
        if TcpStream::connect(&addr).is_ok() {
            return Ok(());
        }
        std::thread::sleep(Duration::from_millis(500));
    }
    Err(format!(
        "Server did not respond within {timeout_secs} seconds"
    ))
}

fn run_and_capture(cmd: &mut Command) -> Result<(bool, String), String> {
    let output = cmd
        .output()
        .map_err(|e| format!("Failed to run command: {e}"))?;

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    let combined = match (stdout.trim(), stderr.trim()) {
        ("", "") => String::new(),
        ("", stderr) => stderr.to_string(),
        (stdout, "") => stdout.to_string(),
        (stdout, stderr) => format!("{stdout}\n{stderr}"),
    };

    Ok((output.status.success(), combined))
}

fn configure_bundled_python_env(
    cmd: &mut Command,
    runtime_dir: &Path,
    cybrtech_dir: &Path,
) -> Result<(), String> {
    let site_packages = cybrtech_dir
        .join("cybrtech-env")
        .join("Lib")
        .join("site-packages");
    let scripts_dir = cybrtech_dir.join("cybrtech-env").join("Scripts");
    let pywin32_system32 = site_packages.join("pywin32_system32");
    let win32_dir = site_packages.join("win32");
    let win32_lib_dir = win32_dir.join("lib");

    if !site_packages.exists() {
        return Err(format!(
            "Bundled site-packages not found at {}",
            site_packages.display()
        ));
    }

    let mut paths = vec![runtime_dir.to_path_buf(), scripts_dir, pywin32_system32];
    if let Some(existing_path) = env::var_os("PATH") {
        paths.extend(env::split_paths(&existing_path));
    }

    let joined_path =
        env::join_paths(paths).map_err(|e| format!("Failed to prepare Python PATH: {e}"))?;

    let python_paths = env::join_paths([site_packages, win32_dir, win32_lib_dir])
        .map_err(|e| format!("Failed to prepare PYTHONPATH: {e}"))?;

    cmd.env("PATH", joined_path)
        .env("PYTHONHOME", runtime_dir)
        .env("PYTHONPATH", python_paths)
        .env("PYTHONIOENCODING", "utf-8")
        .env("PYTHONUTF8", "1")
        .env("PYTHONNOUSERSITE", "1");

    Ok(())
}

fn resolve_python_command(
    app: &tauri::AppHandle,
    cybrtech_dir: &Path,
) -> Result<(PathBuf, Option<PathBuf>), String> {
    let venv_python = cybrtech_dir
        .join("cybrtech-env")
        .join("Scripts")
        .join("python.exe");
    if cfg!(debug_assertions) && venv_python.exists() {
        return Ok((venv_python, None));
    }

    let runtime_dir = resolve_python_runtime_path(app)?;
    let bundled_python = runtime_dir.join("python.exe");
    if bundled_python.exists() {
        return Ok((bundled_python, Some(runtime_dir)));
    }

    if venv_python.exists() {
        return Ok((venv_python, None));
    }

    Err(format!(
        "No Python runtime is available. Expected either {} or {}",
        venv_python.display(),
        bundled_python.display()
    ))
}

fn run_local_health_check(port: u16) -> Result<String, String> {
    let mut stream = TcpStream::connect(("127.0.0.1", port))
        .map_err(|e| format!("Could not connect to local server on port {port}: {e}"))?;

    stream
        .write_all(b"GET /health HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n")
        .map_err(|e| format!("Failed to send health-check request: {e}"))?;

    let mut response = String::new();
    stream
        .read_to_string(&mut response)
        .map_err(|e| format!("Failed to read health-check response: {e}"))?;

    if let Some((_, body)) = response.split_once("\r\n\r\n") {
        let trimmed = body.trim();
        if !trimmed.is_empty() {
            return Ok(trimmed.to_string());
        }
    }

    Err("Health endpoint returned an empty response".into())
}

fn spawn_log_pump<R>(app: tauri::AppHandle, source: &str, stream: &str, reader: R)
where
    R: Read + Send + 'static,
{
    let source = source.to_string();
    let stream = stream.to_string();

    std::thread::spawn(move || {
        let reader = BufReader::new(reader);
        for line in reader.lines() {
            match line {
                Ok(message) if !message.trim().is_empty() => {
                    let _ = app.emit(
                        "process-log",
                        ProcessLogEvent {
                            source: source.clone(),
                            stream: stream.clone(),
                            message,
                        },
                    );
                }
                Ok(_) => {}
                Err(err) => {
                    let _ = app.emit(
                        "process-log",
                        ProcessLogEvent {
                            source: source.clone(),
                            stream: "stderr".into(),
                            message: format!("Failed to read {source} {stream}: {err}"),
                        },
                    );
                    break;
                }
            }
        }
    });
}

fn attach_child_logs(app: &tauri::AppHandle, child: &mut Child, source: &str) {
    if let Some(stdout) = child.stdout.take() {
        spawn_log_pump(app.clone(), source, "stdout", stdout);
    }
    if let Some(stderr) = child.stderr.take() {
        spawn_log_pump(app.clone(), source, "stderr", stderr);
    }
}

fn stop_child_process(child: &mut Child, label: &str) -> Result<String, String> {
    match child.try_wait().map_err(|e| e.to_string())? {
        Some(status) => {
            return Ok(format!(
                "{label} already exited{}",
                status
                    .code()
                    .map(|code| format!(" with code {code}"))
                    .unwrap_or_default()
            ));
        }
        None => {}
    }

    match child.kill() {
        Ok(_) => {}
        Err(err) if err.kind() == std::io::ErrorKind::InvalidInput => {
            return Ok(format!("{label} was already stopping"));
        }
        Err(err) => return Err(err.to_string()),
    }

    let _ = child.wait();
    Ok(format!("{label} stopped"))
}

fn configure_background_process(command: &mut Command) {
    #[cfg(windows)]
    {
        command.creation_flags(CREATE_NO_WINDOW);
    }
}

fn generate_internal_api_token(port: u16) -> String {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_nanos())
        .unwrap_or_default();
    format!("cybrtech-{port:x}-{:x}-{:x}", std::process::id(), nonce)
}

fn rollback_managed_child(slot: &Mutex<Option<Child>>, label: &str) {
    if let Some(mut child) = slot.lock().unwrap().take() {
        let _ = stop_child_process(&mut child, label);
    }
}

/// Returns true if the child process in `slot` is still running.
///
/// Unlike the previous implementation, this function is intentionally
/// non-mutating: it never clears the slot. Reaping an exited process is
/// the responsibility of the stop/restart commands, not a status query.
fn child_is_running(slot: &Mutex<Option<Child>>) -> Result<bool, String> {
    let mut guard = slot.lock().unwrap();
    match guard.as_mut() {
        None => Ok(false),
        Some(child) => match child.try_wait().map_err(|e| e.to_string())? {
            Some(_) => Ok(false), // exited — leave the slot intact for callers to inspect
            None => Ok(true),
        },
    }
}

#[tauri::command]
async fn bootstrap(app: tauri::AppHandle) -> Result<String, String> {
    let base = resolve_cybrtech_path(&app)?;
    let venv_python = base.join("cybrtech-env").join("Scripts").join("python.exe");
    let bundled_python = resolve_python_runtime_path(&app)?.join("python.exe");
    let bundled_site_packages = base.join("cybrtech-env").join("Lib").join("site-packages");

    if venv_python.exists() || (bundled_python.exists() && bundled_site_packages.exists()) {
        return Ok("ready".into());
    }

    #[cfg(not(debug_assertions))]
    {
        return Err(format!(
            "Bundled Python runtime missing at {}. Rebuild the app bundle with python-runtime included.",
            bundled_python.display()
        ));
    }

    #[cfg(debug_assertions)]
    {
        let python_exe = find_python()
            .ok_or("Python not found. Please install Python 3.10+ and ensure it is on PATH.")?;

        let mut cmd = Command::new(python_exe);
        cmd.args(["-m", "venv", "cybrtech-env"]).current_dir(&base);
        let (ok, out) = run_and_capture(&mut cmd)?;
        if !ok {
            return Err(format!("venv creation failed:\n{out}"));
        }

        let pip = base.join("cybrtech-env").join("Scripts").join("pip.exe");
        let mut cmd = Command::new(&pip);
        cmd.args(["install", "--upgrade", "pip"]).current_dir(&base);
        let (ok, out) = run_and_capture(&mut cmd)?;
        if !ok {
            return Err(format!("pip upgrade failed:\n{out}"));
        }

        let req = base.join("requirements.txt");
        if !req.exists() {
            return Err(format!(
                "requirements.txt not found at: {}\nBase dir contents: {:?}",
                req.display(),
                std::fs::read_dir(&base).map(|d| d
                    .filter_map(|e| e.ok())
                    .map(|e| e.file_name())
                    .collect::<Vec<_>>())
            ));
        }

        let mut cmd = Command::new(&pip);
        cmd.args(["install", "-r", req.to_string_lossy().as_ref()])
            .current_dir(&base);
        let (ok, out) = run_and_capture(&mut cmd)?;
        if !ok {
            return Err(format!("pip install failed:\n{out}"));
        }

        Ok(format!("bootstrapped\n{out}"))
    }
}

#[tauri::command]
async fn launch_all(
    debug: bool,
    port: u16,
    app: tauri::AppHandle,
    state: State<'_, AppState>,
) -> Result<String, String> {
    let base = resolve_cybrtech_path(&app)?;
    let (python, runtime_dir) = resolve_python_command(&app, &base)?;
    let server = base.join("cybrtech_server.py");
    let mcp = base.join("cybrtech_mcp.py");
    let server_url = format!("http://127.0.0.1:{port}");
    let internal_api_token = generate_internal_api_token(port);

    if !python.exists() {
        return Err(format!(
            "Python runtime not found at {}. Run bootstrap first.",
            python.display()
        ));
    }

    {
        let mut proc = state.server_process.lock().unwrap();
        if proc.is_some() {
            return Err("Server already running".into());
        }

        let mut command = Command::new(&python);
        command
            .arg(&server)
            .args(["--port", &port.to_string()])
            .current_dir(&base)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .env("CYBRTECH_HOST", "127.0.0.1")
            .env("CYBRTECH_COMMAND_TOKEN", &internal_api_token)
            .env("PYTHONIOENCODING", "utf-8")
            .env("PYTHONUTF8", "1");
        if debug {
            command.arg("--debug");
        }
        if let Some(runtime_dir) = runtime_dir.as_deref() {
            configure_bundled_python_env(&mut command, runtime_dir, &base)?;
        }

        configure_background_process(&mut command);

        let mut child = command
            .spawn()
            .map_err(|e| format!("Failed to start server: {e}"))?;
        attach_child_logs(&app, &mut child, "server");

        *proc = Some(child);
    }

    if let Err(err) = wait_for_port(port, 20) {
        rollback_managed_child(&state.server_process, "Server");
        return Err(format!("{err}. Server process was rolled back."));
    }

    {
        let mut proc = state.mcp_process.lock().unwrap();
        if proc.is_some() {
            rollback_managed_child(&state.server_process, "Server");
            return Err("MCP already running".into());
        }

        let mut command = Command::new(&python);
        command
            .arg(&mcp)
            .args(["--server", &server_url])
            .current_dir(&base)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .env("CYBRTECH_COMMAND_TOKEN", &internal_api_token)
            .env("PYTHONIOENCODING", "utf-8")
            .env("PYTHONUTF8", "1");
        if let Some(runtime_dir) = runtime_dir.as_deref() {
            configure_bundled_python_env(&mut command, runtime_dir, &base)?;
        }

        configure_background_process(&mut command);

        let mut child = command
            .spawn()
            .map_err(|e| {
                rollback_managed_child(&state.server_process, "Server");
                format!("Failed to start MCP: {e}")
            })?;
        attach_child_logs(&app, &mut child, "mcp");
        *proc = Some(child);
    }

    Ok(format!(
        "CybrTech running on port {}{}",
        port,
        if debug { " [debug]" } else { "" }
    ))
}

#[tauri::command]
async fn stop_server(state: State<'_, AppState>) -> Result<String, String> {
    let child = state.server_process.lock().unwrap().take();
    match child {
        None => Err("Server was not running".into()),
        Some(mut child) => {
            tauri::async_runtime::spawn_blocking(move || stop_child_process(&mut child, "Server"))
                .await
                .map_err(|e| format!("Task panicked: {e}"))?
        }
    }
}

#[tauri::command]
async fn stop_mcp(state: State<'_, AppState>) -> Result<String, String> {
    let child = state.mcp_process.lock().unwrap().take();
    match child {
        None => Err("MCP was not running".into()),
        Some(mut child) => {
            tauri::async_runtime::spawn_blocking(move || stop_child_process(&mut child, "MCP"))
                .await
                .map_err(|e| format!("Task panicked: {e}"))?
        }
    }
}

#[tauri::command]
async fn runtime_status(port: u16, state: State<'_, AppState>) -> Result<RuntimeStatus, String> {
    let server_running = child_is_running(&state.server_process)?;
    let mcp_running = child_is_running(&state.mcp_process)?;
    let server_healthy = if server_running {
        tauri::async_runtime::spawn_blocking(move || run_local_health_check(port).is_ok())
            .await
            .unwrap_or(false)
    } else {
        false
    };

    Ok(RuntimeStatus {
        server_running,
        server_healthy,
        mcp_running,
    })
}

#[tauri::command]
async fn restart_server(
    debug: bool,
    port: u16,
    app: tauri::AppHandle,
    state: State<'_, AppState>,
) -> Result<String, String> {
    if let Some(mut child) = state.mcp_process.lock().unwrap().take() {
        let _ = stop_child_process(&mut child, "MCP");
    }

    if let Some(mut child) = state.server_process.lock().unwrap().take() {
        let _ = stop_child_process(&mut child, "Server");
    }

    launch_all(debug, port, app, state).await
}

#[tauri::command]
async fn health_check(port: u16) -> Result<String, String> {
    tauri::async_runtime::spawn_blocking(move || run_local_health_check(port))
        .await
        .map_err(|e| format!("Task panicked: {e}"))?
}

#[tauri::command]
async fn server_health(port: u16) -> Result<String, String> {
    tauri::async_runtime::spawn_blocking(move || run_local_health_check(port))
        .await
        .map_err(|e| format!("Task panicked: {e}"))?
}

fn main() {
    tauri::Builder::default()
        .manage(AppState {
            server_process: Mutex::new(None),
            mcp_process: Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![
            bootstrap,
            launch_all,
            stop_server,
            stop_mcp,
            runtime_status,
            restart_server,
            health_check,
            server_health,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}