<script lang="ts">
  import "../i18n/config";
  import { t } from "svelte-i18n";
  import { onMount } from "svelte";
  import { invoke } from "@tauri-apps/api/core";
  import { language } from "../stores/language";
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
    ts: string;
    msg: string;
    type: LogType;
  }

  let logs: LogEntry[] = [];

  onMount(async () => {
    language.init();
    log("Checking environment...", "cmd");
    try {
      const res = await invoke<string>("bootstrap");
      log(res === "bootstrapped" ? "Dependencies installed successfully" : "Environment ready", "success");
    } catch (e) {
      log(`Setup failed: ${e}`, "error");
    }
  });

  function log(msg: string, type: LogType = "info") {
    const ts = new Date().toLocaleTimeString("en-GB", { hour12: false });
    logs = [...logs, { ts, msg, type }];
    requestAnimationFrame(() => {
      const el = document.getElementById("terminal");
      if (el) el.scrollTop = el.scrollHeight;
    });
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
      } catch (e) {
        log(String(e), "error");
      }
    }
    serverRunning = false;
    mcpRunning = false;
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
          <path d="M9 1L16.5 5.5V12.5L9 17L1.5 12.5V5.5L9 1Z" stroke="#4a9eff" stroke-width="1.2" fill="none" />
          <path d="M9 5L13 7.5V12.5L9 15L5 12.5V7.5L9 5Z" fill="#4a9eff" fill-opacity="0.15" stroke="#4a9eff" stroke-width="0.8" />
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

  <div class="divider-h"></div>

  <section class="config-section">
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

  <div class="divider-h"></div>

  <section class="action-section">
    {#if !isRunning}
      <button class="action-btn launch" on:click={launchAll} disabled={launching}>
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
      <button class="action-btn stop" on:click={stopAll} disabled={stopping}>
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

  <div class="divider-h"></div>

  <section class="terminal-section">
    <div class="term-header">
      <span class="section-label">{$t("terminal.title")}</span>
      <div class="term-header-right">
        <div class="tab-row">
          <button class="tab-btn" class:active={activeTab === "terminal"} on:click={() => (activeTab = "terminal")}>Terminal</button>
          <button class="tab-btn" class:active={activeTab === "health"} on:click={() => (activeTab = "health")}>Server Health</button>
        </div>
        <div class="term-actions">
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
      <div id="terminal" class="terminal">
        {#each logs as entry (entry.ts + entry.msg)}
          <div class="log-line {entry.type}" in:fly={{ y: 4, duration: 120 }}>
            <span class="log-ts">{entry.ts}</span>
            <span class="log-msg">{entry.msg}</span>
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
</main>

<style>
  :global(:root) {
    --bg: #080c10;
    --surface: #0d1219;
    --border: #151d28;
    --border-hi: #1e2d3d;
    --text-1: #c5d0db;
    --text-2: #6a7f94;
    --text-3: #3a4d5e;
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
    background: var(--bg);
    color: var(--text-1);
    font-family: var(--font-sans);
    font-size: 13px;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
  }

  main {
    max-width: 820px;
    margin: 0 auto;
    padding: 2rem 1.75rem;
    display: flex;
    flex-direction: column;
    gap: 0;
    min-height: 100vh;
  }

  .divider-h {
    height: 1px;
    background: var(--border);
    margin: 1.5rem 0;
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
    background: var(--surface);
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
    background: var(--surface);
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
    border-color: rgba(74, 158, 255, 0.3);
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
    color: var(--accent);
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
    background: rgba(74, 158, 255, 0.15);
  }

  .action-section {
    display: flex;
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
    border-color: rgba(74, 158, 255, 0.25);
    color: var(--accent);
  }

  .action-btn.launch:hover:not(:disabled) {
    background: rgba(74, 158, 255, 0.14);
    border-color: rgba(74, 158, 255, 0.45);
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
    background: rgba(74, 158, 255, 0.12);
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

  .ghost-btn:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }

  .terminal {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r);
    height: 260px;
    overflow-y: auto;
    padding: 0.85rem 1rem;
    scroll-behavior: smooth;
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
    word-break: break-all;
    flex: 1;
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
      padding: 1.25rem 1rem;
    }

    header,
    .term-header,
    .term-header-right,
    .header-right {
      flex-direction: column;
      align-items: stretch;
    }

    .config-grid,
    .tab-row,
    .term-actions {
      grid-template-columns: 1fr;
      justify-content: stretch;
    }

    .term-actions,
    .tab-row {
      width: 100%;
    }

    .tab-btn,
    .ghost-btn {
      flex: 1;
      justify-content: center;
    }
  }
</style>
