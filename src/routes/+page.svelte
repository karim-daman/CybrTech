<script lang="ts">
  import "../i18n/config";
  import { t } from "svelte-i18n";
  import { onMount, tick } from "svelte";
  import { invoke } from "@tauri-apps/api/core";
  import { listen } from "@tauri-apps/api/event";
  import { language } from "../stores/language";
  import { theme } from "../stores/theme";
  import SettingsPanel from "../components/SettingsPanel.svelte";
  import HealthInspector from "../components/HealthInspector.svelte";
  import { fly } from "svelte/transition";

  type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue };

  let port = 8888;
  let debug = false;

  let launching = false;
  let stopping = false;
  let checking = false;
  let settingsOpen = false;
  let activeTab: "terminal" | "health" = "terminal";

  let serverRunning = false;
  let mcpRunning = false;
  let healthData: Record<string, JsonValue> | null = null;
  let healthError = "";

  $: isRunning = serverRunning && mcpRunning;

  type LogType = "info" | "success" | "error" | "warn" | "muted" | "cmd";

  interface LogEntry {
    id: number;
    ts: string;
    msg: string;
    type: LogType;
    count?: number;
  }

  interface ProcessLogEvent {
    source: string;
    stream: string;
    message: string;
  }

  let logs: LogEntry[] = [];
  let terminalEl: HTMLDivElement | null = null;
  let followLogs = true;
  let nextLogId = 0;
  const MAX_LOGS = 400;
  const AUTO_SCROLL_THRESHOLD = 24;
  const READY_BANNER = [
    "     ██████╗██╗   ██╗██████╗ ██████╗ ████████╗███████╗ ██████╗██╗  ██╗",
    "    ██╔════╝╚██╗ ██╔╝██╔══██╗██╔══██╗╚══██╔══╝██╔════╝██╔════╝██║  ██║",
    "    ██║      ╚████╔╝ ██████╔╝██████╔╝   ██║   █████╗  ██║     ███████║",
    "    ██║       ╚██╔╝  ██╔══██╗██╔══██╗   ██║   ██╔══╝  ██║     ██╔══██║",
    "    ╚██████╗   ██║   ██████╔╝██║  ██║   ██║   ███████╗╚██████╗██║  ██║",
    "     ╚═════╝   ╚═╝   ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝ ╚═════╝╚═╝  ╚═╝",
    "                                                                      "
  ].join("\n");

  onMount(() => {
    language.init();
    theme.init();

    let unlisten = () => {};

    void (async () => {
      unlisten = await listen<ProcessLogEvent>("process-log", (event) => {
        const payload = event.payload;
        const cleanMessage = normalizeProcessLog(payload);
        if (!cleanMessage) return;

        const prefix = payload.source.toUpperCase();
        log(`[${prefix}] ${cleanMessage}`, classifyProcessLog(payload, cleanMessage));
      });

      log("Checking environment...", "cmd");
      try {
        const res = await invoke<string>("bootstrap");
        log(res === "bootstrapped" ? "Dependencies installed successfully" : "Environment ready", "success");
        log(READY_BANNER, "info");
      } catch (e) {
        log(`Setup failed: ${e}`, "error");
      }
    })();

    return () => {
      unlisten();
    };
  });

  function log(msg: string, type: LogType = "info") {
    const ts = new Date().toLocaleTimeString("en-GB", { hour12: false });
    const lastEntry = logs.at(-1);

    if (lastEntry && lastEntry.msg === msg && lastEntry.type === type) {
      logs = [
        ...logs.slice(0, -1),
        { ...lastEntry, count: (lastEntry.count ?? 1) + 1, ts }
      ];
    } else {
      logs = [...logs, { id: nextLogId++, ts, msg, type }];
      if (logs.length > MAX_LOGS) {
        logs = logs.slice(-MAX_LOGS);
      }
    }

    void scrollTerminalToBottom();
  }

  function stripAnsi(value: string) {
    return value.replace(/\x1B\[[0-9;]*[A-Za-z]/g, "");
  }

  function decodeMojibake(value: string) {
    if (!/[ÃÂâð]/.test(value)) return value;

    try {
      const bytes = Uint8Array.from(Array.from(value, (char) => char.charCodeAt(0) & 0xff));
      return new TextDecoder("utf-8", { fatal: false }).decode(bytes);
    } catch {
      return value;
    }
  }

  function normalizeProcessLog(payload: ProcessLogEvent) {
    let message = stripAnsi(payload.message);
    message = decodeMojibake(message);
    message = message
      .replace(/\r/g, "")
      .replace(/�+/g, "")
      .replace(/[^\x09\x0A\x0D\x20-\x7E]/g, " ")
      .trim();

    if (!message) return "";

    message = message
      .replace(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+\s+-\s+[^-]+?\s+-\s+(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s+-\s+/i, "")
      .replace(/^\*\s+Serving Flask app\b.*$/i, "Flask app loaded")
      .replace(/^\*\s+Debug mode:\s+off$/i, "Debug mode disabled")
      .replace(/^\*\s+Debug mode:\s+on$/i, "Debug mode enabled")
      .replace(/^\*\s+Running on\s+(.*)$/i, "Listening on $1")
      .replace(/^WARNING:\s+This is a development server.*$/i, "Using Flask development server")
      .replace(/^\*\s+Press CTRL\+C to quit$/i, "Server is ready")
      .replace(/\s+/g, " ")
      .trim();

    if (!message) return "";
    if (/^[\s\-_=~.]+$/.test(message)) return "";
    if (/^[\p{S}\p{P}\p{M}\s]+$/u.test(message) && !/[A-Za-z0-9]/.test(message)) return "";
    if (/^(INFO|WARNING|ERROR|DEBUG|CRITICAL)\s*:?$/i.test(message)) return "";
    if (/^(Startup|Server) (info|banner)$/i.test(message)) return "";

    return message;
  }

  function classifyProcessLog(payload: ProcessLogEvent, message: string): LogType {
    if (/\b(ERROR|CRITICAL|FAILED|TRACEBACK|EXCEPTION)\b/i.test(message)) return "error";
    if (/\b(WARN|WARNING|TIMEOUT|RETRY)\b/i.test(message)) return "warn";
    if (/\b(SUCCESS|READY|STARTED|LISTENING ON|RUNNING ON|CONNECTED|REFRESHED)\b/i.test(message)) return "success";
    if (payload.stream === "stderr") return "warn";
    return "info";
  }

  function handleTerminalScroll() {
    if (!terminalEl) return;
    followLogs = isNearBottom(terminalEl);
  }

  function isNearBottom(element: HTMLElement) {
    return element.scrollHeight - element.scrollTop - element.clientHeight <= AUTO_SCROLL_THRESHOLD;
  }

  async function scrollTerminalToBottom() {
    if (!followLogs) return;
    await tick();
    if (terminalEl) {
      terminalEl.scrollTop = terminalEl.scrollHeight;
    }
  }

  function toggleFollowLogs() {
    followLogs = !followLogs;
    if (followLogs) {
      void scrollTerminalToBottom();
    }
  }

  async function launchAll() {
    launching = true;
    log(`init cybrtech -> :${port}${debug ? " --debug" : ""}`, "cmd");
    try {
      const res: string = await invoke("launch_all", { debug, port });
      serverRunning = true;
      mcpRunning = true;
      log(res, "success");
    } catch (e) {
      log(String(e), "error");
    }
    launching = false;
  }

  async function stopAll() {
    stopping = true;
    for (const [cmd] of [["stop_mcp"], ["stop_server"]] as const) {
      try {
        const res: string = await invoke(cmd);
        log(res, "warn");
        if (cmd === "stop_mcp") {
          mcpRunning = false;
        }
        if (cmd === "stop_server") {
          serverRunning = false;
        }
      } catch (e) {
        log(String(e), "error");
      }
    }
    stopping = false;
  }

  async function healthCheck() {
    checking = true;
    healthError = "";
    log(`${$t("terminal.health_cmd")} http://127.0.0.1:${port}/health`, "cmd");
    try {
      const raw: string = await invoke("server_health", { port });
      healthData = JSON.parse(raw) as Record<string, JsonValue>;
      activeTab = "health";
      log("Server health refreshed", "success");
    } catch (e) {
      healthError = String(e);
      activeTab = "health";
      log(String(e), "error");
    }
    checking = false;
  }

  function clearLogs() {
    logs = [];
    followLogs = true;
  }
</script>

<svelte:head>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500&display=swap" rel="stylesheet" />
</svelte:head>

<SettingsPanel bind:open={settingsOpen} on:close={() => (settingsOpen = false)} />

<main>
  <header>
    <div class="brand">
      <div class="brand-mark">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M9 1L16.5 5.5V12.5L9 17L1.5 12.5V5.5L9 1Z" stroke="currentColor" stroke-width="1.2" fill="none" />
          <path d="M9 5L13 7.5V12.5L9 15L5 12.5V7.5L9 5Z" fill="currentColor" fill-opacity="0.15" stroke="currentColor" stroke-width="0.8" />
        </svg>
      </div>
      <div class="brand-text">
        <span class="brand-name">{$t("header.brand")}</span>
        <span class="brand-sub">{$t("header.tagline")}</span>
      </div>
    </div>

    <div class="header-right">
      <div class="status-row">
        <div class="status-item" class:active={serverRunning}>
          <span class="status-dot"></span>
          <span class="status-label">{$t("status.server")}</span>
        </div>
        <div class="status-sep">/</div>
        <div class="status-item" class:active={mcpRunning}>
          <span class="status-dot"></span>
          <span class="status-label">{$t("status.mcp")}</span>
        </div>
      </div>

      <button class="icon-btn" on:click={() => (settingsOpen = true)} aria-label={$t("header.settings")}>
        <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
          <circle cx="7.5" cy="7.5" r="2" stroke="currentColor" stroke-width="1.2" />
          <path
            d="M7.5 1v1.5M7.5 12.5V14M1 7.5h1.5M12.5 7.5H14M2.6 2.6l1.1 1.1M11.3 11.3l1.1 1.1M11.3 3.7l-1.1 1.1M3.8 11.2l-1.1 1.1"
            stroke="currentColor"
            stroke-width="1.2"
            stroke-linecap="round" />
        </svg>
      </button>
    </div>
  </header>

  <section class="workspace-grid">
    <div class="control-stack">
      <section class="config-section panel-card">
        <span class="section-label">{$t("options.title")}</span>

        <div class="config-grid">
          <div class="field">
            <label class="field-label" for="port-input">{$t("options.port")}</label>
            <input id="port-input" type="number" bind:value={port} min="1024" max="65535" disabled={isRunning || launching} />
          </div>

          <div class="field">
            <span class="field-label">{$t("options.debug")}</span>
            <button class="toggle" class:on={debug} disabled={isRunning || launching} on:click={() => (debug = !debug)} aria-pressed={debug}>
              <span class="track-label off">{$t("options.off")}</span>
              <span class="thumb"></span>
              <span class="track-label on">{$t("options.on")}</span>
            </button>
          </div>
        </div>
      </section>

      <section class="action-section panel-card">
        <span class="section-label">Control</span>

        {#if !isRunning}
          <button class="action-btn launch action-fill" on:click={launchAll} disabled={launching}>
            {#if launching}
              <span class="spinner"></span>
              {$t("buttons.launching")}
            {:else}
              <svg width="11" height="11" viewBox="0 0 11 11" fill="currentColor">
                <path d="M2 1.5l7 4-7 4V1.5z" />
              </svg>
              {$t("buttons.launch")}
            {/if}
          </button>
        {:else}
          <button class="action-btn stop action-fill" on:click={stopAll} disabled={stopping}>
            {#if stopping}
              <span class="spinner"></span>
              {$t("buttons.stopping")}
            {:else}
              <svg width="10" height="10" viewBox="0 0 10 10" fill="currentColor">
                <rect x="1" y="1" width="8" height="8" rx="1" />
              </svg>
              {$t("buttons.stop")}
            {/if}
          </button>
        {/if}
      </section>
    </div>

    <section class="terminal-section panel-card">
    <div class="term-header">
      <span class="section-label">{$t("terminal.title")}</span>
      <div class="term-header-right">
        <div class="tab-row">
          <button class="tab-btn" class:active={activeTab === "terminal"} on:click={() => (activeTab = "terminal")}>Terminal</button>
          <button class="tab-btn" class:active={activeTab === "health"} on:click={() => (activeTab = "health")}>Server Health</button>
        </div>
        <div class="term-actions">
          <button class="ghost-btn" class:active={followLogs} on:click={toggleFollowLogs}>
            {followLogs ? "Following logs" : "Paused"}
          </button>
          <button class="ghost-btn" on:click={healthCheck} disabled={checking || !isRunning}>
            {#if checking}
              <span class="spinner sm"></span>
            {:else}
              <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
                <path d="M1 5.5h2l1.5-3 2 6 1.5-3H10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            {/if}
            {$t("buttons.health")}
          </button>
          <button class="ghost-btn" on:click={clearLogs}>{$t("buttons.clear")}</button>
        </div>
      </div>
    </div>

    {#if activeTab === "terminal"}
      <div bind:this={terminalEl} class="terminal" on:scroll={handleTerminalScroll}>
        {#each logs as entry (entry.id)}
          <div class="log-line {entry.type}" in:fly={{ y: 4, duration: 120 }}>
            <span class="log-ts">{entry.ts}</span>
            <span class="log-msg">{entry.msg}</span>
            {#if entry.count && entry.count > 1}
              <span class="log-repeat">x{entry.count}</span>
            {/if}
          </div>
        {/each}
        {#if logs.length === 0}
          <div class="log-line muted">
            <span class="log-ts">-</span>
            <span class="log-msg">{$t("terminal.empty")}</span>
          </div>
        {/if}
      </div>
    {:else}
      <HealthInspector data={healthData} loading={checking} error={healthError} />
    {/if}
  </section>
  </section>
</main>

<style>
  :global(:root) {
    --bg: #080c10;
    --surface: #0d1219;
    --surface-strong: #0d1219;
    --border: #151d28;
    --border-hi: #203548;
    --text-1: #c5d0db;
    --text-2: #6a7f94;
    --text-3: #3a4d5e;
    --primary: #4a9eff;
    --secondary: #203548;
    --accent: #4a9eff;
    --accent-lo: rgba(74, 158, 255, 0.08);
    --green: #39d353;
    --red: #f47067;
    --yellow: #e3b341;
    --font-mono: "IBM Plex Mono", "Cascadia Code", monospace;
    --font-sans: "IBM Plex Sans", system-ui, sans-serif;
    --r: 6px;
  }

  :global(*, *::before, *::after) {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }

  :global(body) {
    background:
      radial-gradient(circle at top left, color-mix(in srgb, var(--primary) 18%, transparent), transparent 28%),
      radial-gradient(circle at top right, color-mix(in srgb, var(--accent) 14%, transparent), transparent 24%),
      linear-gradient(180deg, color-mix(in srgb, var(--bg) 92%, black), var(--bg));
    color: var(--text-1);
    font-family: var(--font-sans);
    font-size: 13px;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
  }

  main {
    width: min(1500px, calc(100vw - 2rem));
    margin: 0 auto;
    padding: 2rem 0 2.5rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    min-height: 100vh;
  }

  .workspace-grid {
    display: grid;
    grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
    gap: 1.25rem;
    align-items: start;
    min-height: 0;
    flex: 1;
  }

  .control-stack {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .panel-card {
    background: linear-gradient(180deg, color-mix(in srgb, var(--surface) 92%, white), var(--surface));
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.1rem 1.15rem;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.18);
    backdrop-filter: blur(10px);
  }

  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .brand-mark {
    flex-shrink: 0;
    color: var(--accent);
  }

  .brand-text {
    display: flex;
    flex-direction: column;
    gap: 1px;
  }

  .brand-name {
    font-family: var(--font-mono);
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--text-1);
    letter-spacing: 0.06em;
  }

  .brand-sub {
    font-family: var(--font-mono);
    font-size: 0.62rem;
    color: var(--text-3);
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .status-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-family: var(--font-mono);
    font-size: 0.68rem;
    letter-spacing: 0.06em;
  }

  .status-sep {
    color: var(--text-3);
  }

  .status-item {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    color: var(--text-3);
    transition: color 0.25s;
  }

  .status-item.active {
    color: var(--green);
  }

  .status-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: currentColor;
    transition: box-shadow 0.25s;
  }

  .status-item.active .status-dot {
    box-shadow: 0 0 6px var(--green);
  }

  .icon-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 30px;
    height: 30px;
    border-radius: var(--r);
    border: 1px solid var(--border);
    background: transparent;
    color: var(--text-2);
    cursor: pointer;
    transition:
      color 0.15s,
      border-color 0.15s,
      background 0.15s;
  }

  .icon-btn:hover {
    color: var(--text-1);
    border-color: var(--border-hi);
    background: var(--surface);
  }

  .section-label {
    font-family: var(--font-mono);
    font-size: 0.62rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-3);
    display: block;
  }

  .config-section {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .config-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .field-label {
    font-family: var(--font-mono);
    font-size: 0.65rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-2);
  }

  input[type="number"] {
    width: 100%;
    padding: 0.5rem 0.65rem;
    background: color-mix(in srgb, var(--surface) 85%, black);
    border: 1px solid var(--border);
    border-radius: var(--r);
    color: var(--text-1);
    font-family: var(--font-mono);
    font-size: 0.82rem;
    outline: none;
    transition: border-color 0.15s;
  }

  input[type="number"]:focus {
    border-color: var(--accent);
  }

  input:disabled {
    opacity: 0.35;
  }

  .toggle {
    display: inline-flex;
    align-items: center;
    height: 32px;
    background: color-mix(in srgb, var(--surface) 85%, black);
    border: 1px solid var(--border);
    border-radius: var(--r);
    cursor: pointer;
    overflow: hidden;
    transition: border-color 0.2s;
    padding: 0;
    position: relative;
    width: 100%;
  }

  .toggle.on {
    border-color: color-mix(in srgb, var(--primary) 45%, transparent);
  }

  .toggle:disabled {
    opacity: 0.35;
    cursor: not-allowed;
  }

  .track-label {
    font-family: var(--font-mono);
    font-size: 0.65rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    flex: 1;
    text-align: center;
    transition: color 0.2s;
    position: relative;
    z-index: 1;
    pointer-events: none;
  }

  .track-label.off {
    color: var(--text-2);
  }

  .track-label.on {
    color: var(--text-3);
  }

  .toggle.on .track-label.off {
    color: var(--text-3);
  }

  .toggle.on .track-label.on {
    color: var(--primary);
  }

  .thumb {
    position: absolute;
    top: 3px;
    bottom: 3px;
    width: calc(50% - 3px);
    background: var(--border-hi);
    border-radius: 4px;
    left: 3px;
    transition:
      transform 0.2s cubic-bezier(0.4, 0, 0.2, 1),
      background 0.2s;
  }

  .toggle.on .thumb {
    transform: translateX(calc(100% + 2px));
    background: color-mix(in srgb, var(--primary) 18%, transparent);
  }

  .action-section {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    justify-content: flex-start;
  }

  .action-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.55rem;
    padding: 0.6rem 1.4rem;
    font-family: var(--font-mono);
    font-size: 0.78rem;
    letter-spacing: 0.06em;
    font-weight: 500;
    border: 1px solid transparent;
    border-radius: var(--r);
    cursor: pointer;
    transition: all 0.15s;
  }

  .action-btn:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }

  .action-btn:active:not(:disabled) {
    transform: scale(0.98);
  }

  .action-btn.launch {
    background: var(--accent-lo);
    border-color: color-mix(in srgb, var(--primary) 28%, transparent);
    color: var(--primary);
  }

  .action-btn.launch:hover:not(:disabled) {
    background: color-mix(in srgb, var(--primary) 16%, transparent);
    border-color: color-mix(in srgb, var(--primary) 54%, transparent);
  }

  .action-btn.stop {
    background: rgba(244, 112, 103, 0.08);
    border-color: rgba(244, 112, 103, 0.2);
    color: var(--red);
  }

  .action-btn.stop:hover:not(:disabled) {
    background: rgba(244, 112, 103, 0.14);
    border-color: rgba(244, 112, 103, 0.4);
  }

  .action-fill {
    width: 100%;
    justify-content: center;
    min-height: 44px;
  }

  .spinner {
    display: inline-block;
    width: 11px;
    height: 11px;
    border: 1.5px solid rgba(255, 255, 255, 0.15);
    border-top-color: currentColor;
    border-radius: 50%;
    animation: spin 0.65s linear infinite;
    flex-shrink: 0;
  }

  .spinner.sm {
    width: 9px;
    height: 9px;
    border-width: 1.2px;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .terminal-section {
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
    flex: 1;
    min-width: 0;
  }

  .term-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
  }

  .term-header-right {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .tab-row {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.2rem;
    border: 1px solid var(--border);
    border-radius: var(--r);
    background: rgba(255, 255, 255, 0.02);
  }

  .tab-btn {
    border: 0;
    background: transparent;
    color: var(--text-2);
    font-family: var(--font-mono);
    font-size: 0.67rem;
    letter-spacing: 0.06em;
    padding: 0.35rem 0.6rem;
    border-radius: 4px;
    cursor: pointer;
    transition:
      background 0.15s,
      color 0.15s;
  }

  .tab-btn.active {
    background: color-mix(in srgb, var(--accent) 15%, transparent);
    color: var(--accent);
  }

  .term-actions {
    display: flex;
    gap: 0.4rem;
  }

  .ghost-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.3rem 0.7rem;
    font-family: var(--font-mono);
    font-size: 0.67rem;
    letter-spacing: 0.06em;
    background: transparent;
    border: 1px solid var(--border);
    border-radius: var(--r);
    color: var(--text-2);
    cursor: pointer;
    transition:
      color 0.15s,
      border-color 0.15s;
  }

  .ghost-btn:hover:not(:disabled) {
    color: var(--text-1);
    border-color: var(--border-hi);
  }

  .ghost-btn.active {
    color: var(--accent);
    border-color: color-mix(in srgb, var(--accent) 28%, transparent);
    background: color-mix(in srgb, var(--accent) 10%, transparent);
  }

  .ghost-btn:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }

  .terminal {
    background: color-mix(in srgb, var(--surface) 88%, black);
    border: 1px solid var(--border);
    border-radius: var(--r);
    height: clamp(360px, 62vh, 820px);
    overflow-y: auto;
    padding: 0.85rem 1rem;
  }

  .terminal::-webkit-scrollbar {
    width: 4px;
  }

  .terminal::-webkit-scrollbar-track {
    background: transparent;
  }

  .terminal::-webkit-scrollbar-thumb {
    background: var(--border-hi);
    border-radius: 2px;
  }

  .log-line {
    display: flex;
    gap: 1rem;
    padding: 0.18rem 0;
    font-family: var(--font-mono);
    font-size: 0.75rem;
    line-height: 1.6;
  }

  .log-ts {
    color: var(--text-3);
    flex-shrink: 0;
    font-size: 0.7rem;
    padding-top: 1px;
  }

  .log-msg {
    color: var(--text-1);
    white-space: pre-wrap;
    word-break: break-word;
    flex: 1;
  }

  .log-repeat {
    color: var(--text-3);
    flex-shrink: 0;
    font-size: 0.68rem;
  }

  .log-line.success .log-msg {
    color: var(--green);
  }

  .log-line.error .log-msg {
    color: var(--red);
  }

  .log-line.warn .log-msg {
    color: var(--yellow);
  }

  .log-line.cmd .log-msg {
    color: var(--text-2);
  }

  .log-line.muted .log-msg {
    color: var(--text-3);
  }

  @media (max-width: 700px) {
    main {
      width: calc(100vw - 1rem);
      padding: 1rem 0 1.5rem;
    }

    header,
    .term-header,
    .term-header-right,
    .header-right {
      flex-direction: column;
      align-items: stretch;
    }

    .workspace-grid {
      grid-template-columns: 1fr;
    }

    .term-actions,
    .tab-row {
      width: 100%;
      flex-wrap: wrap;
    }

    .config-grid {
      grid-template-columns: 1fr;
    }

    .tab-btn,
    .ghost-btn {
      flex: 1;
      justify-content: center;
    }

    .panel-card {
      padding: 0.95rem;
    }

    .terminal {
      height: min(58vh, 560px);
    }
  }
</style>
