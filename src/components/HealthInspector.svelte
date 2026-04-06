<script lang="ts">
  import JsonNode from "./JsonNode.svelte";

  type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue };

  export let data: Record<string, JsonValue> | null = null;
  export let loading = false;
  export let error = "";

  const sectionDefaults = {
    overview: true,
    systemMetrics: true,
    telemetry: false,
    cacheStats: false,
    categoryStats: true,
    toolsStatus: true,
  };

  let sections = { ...sectionDefaults };

  function toggleSection(name: keyof typeof sectionDefaults) {
    sections = { ...sections, [name]: !sections[name] };
  }

  function asRecord(value: JsonValue | undefined | null): Record<string, JsonValue> {
    return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, JsonValue>) : {};
  }

  function asNumber(value: JsonValue | undefined | null): number | null {
    if (typeof value === "number") return value;
    if (typeof value === "string") {
      const match = value.match(/-?\d+(\.\d+)?/);
      return match ? Number(match[0]) : null;
    }
    return null;
  }

  function asBoolean(value: JsonValue | undefined | null): boolean | null {
    return typeof value === "boolean" ? value : null;
  }

  function titleize(value: string) {
    return value
      .replace(/_/g, " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function formatPercent(value: JsonValue | undefined | null) {
    if (typeof value === "string") return value;
    if (typeof value === "number") return `${value.toFixed(1)}%`;
    return "n/a";
  }

  function formatDuration(totalSeconds: number | null) {
    if (totalSeconds === null) return "n/a";
    const seconds = Math.max(0, Math.floor(totalSeconds));
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${secs}s`;
    return `${secs}s`;
  }

  function statusClass(value: JsonValue | undefined | null) {
    if (typeof value === "boolean") return value ? "good" : "bad";
    return "";
  }

  function isWarning(label: string, value: JsonValue | undefined | null) {
    const numeric = asNumber(value);
    const lower = label.toLowerCase();
    if (lower.includes("success_rate") && numeric !== null && numeric <= 0) return true;
    if (lower.includes("disk") && numeric !== null && numeric >= 85) return true;
    if ((lower.includes("tool") || lower.includes("essential")) && value === false) return true;
    return false;
  }

  function metricTone(label: string, value: JsonValue | undefined | null) {
    return isWarning(label, value) ? "warn" : "";
  }

  $: overview = data
    ? {
        status: data.status,
        message: data.message,
        version: data.version,
        all_essential_tools_available: data.all_essential_tools_available,
        total_tools_available: data.total_tools_available,
        total_tools_count: data.total_tools_count,
        uptime: data.uptime,
      }
    : null;

  $: telemetry = asRecord(data?.telemetry as JsonValue);
  $: systemMetrics = asRecord(telemetry.system_metrics);
  $: cacheStats = asRecord(data?.cache_stats as JsonValue);
  $: categoryStats = asRecord(data?.category_stats as JsonValue);
  $: toolsStatus = asRecord(data?.tools_status as JsonValue);
  $: toolEntries = Object.entries(toolsStatus).sort((a, b) => a[0].localeCompare(b[0]));
  $: categoryEntries = Object.entries(categoryStats).map(([name, value]) => {
    const stats = asRecord(value);
    const available = asNumber(stats.available) ?? 0;
    const total = asNumber(stats.total) ?? 0;
    const percent = total > 0 ? (available / total) * 100 : 0;
    return { name, available, total, percent, raw: stats };
  });

  $: metricCards = [
    {
      key: "cpu_percent",
      label: "CPU",
      value: formatPercent(systemMetrics.cpu_percent),
      tone: metricTone("cpu_percent", systemMetrics.cpu_percent),
    },
    {
      key: "memory_percent",
      label: "Memory",
      value: formatPercent(systemMetrics.memory_percent),
      tone: metricTone("memory_percent", systemMetrics.memory_percent),
    },
    {
      key: "disk_usage",
      label: "Disk",
      value: formatPercent(systemMetrics.disk_usage),
      tone: metricTone("disk_usage", systemMetrics.disk_usage),
    },
    {
      key: "uptime_seconds",
      label: "Uptime",
      value: formatDuration(asNumber(telemetry.uptime_seconds) ?? asNumber(data?.uptime as JsonValue)),
      tone: "",
    },
  ];
</script>

<div class="health-panel">
  {#if loading}
    <div class="empty-state">Loading server health...</div>
  {:else if error}
    <div class="empty-state error">{error}</div>
  {:else if !data}
    <div class="empty-state">Run Server Health to inspect the live response.</div>
  {:else}
    <div class="sections">
      <section class="card">
        <button class="section-head" type="button" on:click={() => toggleSection("overview")}>
          <span>Overview</span>
          <span class="caret">{sections.overview ? "-" : "+"}</span>
        </button>
        {#if sections.overview && overview}
          <div class="section-body">
            <div class="overview-grid">
              {#each Object.entries(overview) as [key, value]}
                <div class:warning={isWarning(key, value)} class="overview-item">
                  <span class="item-label">{titleize(key)}</span>
                  <span class={`item-value ${statusClass(value)}`}>
                    {#if key === "uptime"}
                      {formatDuration(asNumber(value))}
                    {:else}
                      {String(value)}
                    {/if}
                  </span>
                </div>
              {/each}
            </div>
            <div class="json-shell">
              <JsonNode label="overview" value={overview} />
            </div>
          </div>
        {/if}
      </section>

      <section class="card">
        <button class="section-head" type="button" on:click={() => toggleSection("systemMetrics")}>
          <span>System Metrics</span>
          <span class="caret">{sections.systemMetrics ? "-" : "+"}</span>
        </button>
        {#if sections.systemMetrics}
          <div class="section-body">
            <div class="metric-cards">
              {#each metricCards as metric}
                <div class={`metric-card ${metric.tone}`}>
                  <span class="metric-label">{metric.label}</span>
                  <strong class="metric-value">{metric.value}</strong>
                </div>
              {/each}
            </div>
            <div class="json-shell">
              <JsonNode label="system_metrics" value={systemMetrics} />
            </div>
          </div>
        {/if}
      </section>

      <section class="card">
        <button class="section-head" type="button" on:click={() => toggleSection("telemetry")}>
          <span>Telemetry</span>
          <span class="caret">{sections.telemetry ? "-" : "+"}</span>
        </button>
        {#if sections.telemetry}
          <div class="section-body">
            <div class="overview-grid compact">
              {#each Object.entries(telemetry).filter(([key]) => key !== "system_metrics") as [key, value]}
                <div class:warning={isWarning(key, value)} class="overview-item">
                  <span class="item-label">{titleize(key)}</span>
                  <span class="item-value">{String(value)}</span>
                </div>
              {/each}
            </div>
            <div class="json-shell">
              <JsonNode label="telemetry" value={telemetry} />
            </div>
          </div>
        {/if}
      </section>

      <section class="card">
        <button class="section-head" type="button" on:click={() => toggleSection("cacheStats")}>
          <span>Cache Stats</span>
          <span class="caret">{sections.cacheStats ? "-" : "+"}</span>
        </button>
        {#if sections.cacheStats}
          <div class="section-body">
            <div class="overview-grid compact">
              {#each Object.entries(cacheStats) as [key, value]}
                <div class:warning={isWarning(key, value)} class="overview-item">
                  <span class="item-label">{titleize(key)}</span>
                  <span class="item-value">{String(value)}</span>
                </div>
              {/each}
            </div>
            <div class="json-shell">
              <JsonNode label="cache_stats" value={cacheStats} />
            </div>
          </div>
        {/if}
      </section>

      <section class="card">
        <button class="section-head" type="button" on:click={() => toggleSection("categoryStats")}>
          <span>Category Stats</span>
          <span class="caret">{sections.categoryStats ? "-" : "+"}</span>
        </button>
        {#if sections.categoryStats}
          <div class="section-body">
            <div class="category-list">
              {#each categoryEntries as category}
                <div class:warning={category.available === 0 || category.available < category.total} class="category-row">
                  <div class="category-head">
                    <span>{titleize(category.name)}</span>
                    <span>{category.available}/{category.total}</span>
                  </div>
                  <div class="bar-track" aria-hidden="true">
                    <div class="bar-available" style={`width:${category.percent}%`}></div>
                  </div>
                </div>
              {/each}
            </div>
            <div class="json-shell">
              <JsonNode label="category_stats" value={categoryStats} />
            </div>
          </div>
        {/if}
      </section>

      <section class="card">
        <button class="section-head" type="button" on:click={() => toggleSection("toolsStatus")}>
          <span>Tools Status</span>
          <span class="caret">{sections.toolsStatus ? "-" : "+"}</span>
        </button>
        {#if sections.toolsStatus}
          <div class="section-body">
            <div class="tool-grid">
              {#each toolEntries as [tool, available]}
                <div class="tool-chip" class:warning={!available}>
                  <span class={`tool-dot ${available ? "up" : "down"}`}></span>
                  <span class="tool-name">{tool}</span>
                </div>
              {/each}
            </div>
            <div class="json-shell">
              <JsonNode label="tools_status" value={toolsStatus} />
            </div>
          </div>
        {/if}
      </section>
    </div>
  {/if}
</div>

<style>
  .health-panel {
    min-height: 260px;
    border: 1px solid var(--border);
    border-radius: var(--r);
    background: var(--surface);
    padding: 0.85rem 1rem;
    overflow: auto;
  }

  .sections {
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
  }

  .card {
    border: 1px solid var(--border);
    border-radius: var(--r);
    background: rgba(255, 255, 255, 0.01);
  }

  .section-head {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.7rem 0.85rem;
    border: 0;
    background: transparent;
    color: var(--text-1);
    font-family: var(--font-mono);
    font-size: 0.75rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    cursor: pointer;
  }

  .caret {
    color: var(--text-3);
  }

  .section-body {
    display: flex;
    flex-direction: column;
    gap: 0.9rem;
    padding: 0 0.85rem 0.85rem;
  }

  .overview-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.65rem;
  }

  .overview-grid.compact {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .overview-item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    padding: 0.65rem;
    border-radius: var(--r);
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid var(--border);
  }

  .overview-item.warning {
    border-color: rgba(244, 112, 103, 0.4);
    background: rgba(244, 112, 103, 0.06);
  }

  .item-label,
  .metric-label {
    color: var(--text-3);
    font-family: var(--font-mono);
    font-size: 0.65rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }

  .item-value,
  .metric-value {
    font-family: var(--font-mono);
    word-break: break-word;
  }

  .item-value.good {
    color: var(--green);
  }

  .item-value.bad {
    color: var(--red);
  }

  .metric-cards {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.65rem;
  }

  .metric-card {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    padding: 0.75rem;
    border: 1px solid var(--border);
    border-radius: var(--r);
    background: rgba(74, 158, 255, 0.04);
  }

  .metric-card.warn {
    border-color: rgba(244, 112, 103, 0.42);
    background: rgba(244, 112, 103, 0.08);
  }

  .category-list {
    display: flex;
    flex-direction: column;
    gap: 0.65rem;
  }

  .category-row {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  .category-row.warning .category-head {
    color: #ff9b91;
  }

  .category-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-family: var(--font-mono);
    font-size: 0.73rem;
  }

  .bar-track {
    height: 10px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border);
    overflow: hidden;
  }

  .bar-available {
    height: 100%;
    background: linear-gradient(90deg, #39d353, #e3b341);
  }

  .tool-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 0.45rem;
  }

  .tool-chip {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.45rem 0.55rem;
    border-radius: var(--r);
    border: 1px solid var(--border);
    background: rgba(255, 255, 255, 0.02);
    font-family: var(--font-mono);
    font-size: 0.68rem;
  }

  .tool-chip.warning {
    border-color: rgba(244, 112, 103, 0.4);
  }

  .tool-dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .tool-dot.up {
    background: var(--green);
    box-shadow: 0 0 8px rgba(57, 211, 83, 0.4);
  }

  .tool-dot.down {
    background: var(--red);
    box-shadow: 0 0 8px rgba(244, 112, 103, 0.35);
  }

  .tool-name {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .json-shell {
    padding: 0.75rem;
    border-radius: var(--r);
    border: 1px solid var(--border);
    background: rgba(0, 0, 0, 0.16);
  }

  .empty-state {
    min-height: 220px;
    display: grid;
    place-items: center;
    text-align: center;
    color: var(--text-3);
    font-family: var(--font-mono);
  }

  .empty-state.error {
    color: var(--red);
  }

  @media (max-width: 700px) {
    .overview-grid,
    .overview-grid.compact,
    .metric-cards {
      grid-template-columns: 1fr 1fr;
    }

    .tool-grid {
      grid-template-columns: 1fr 1fr;
    }
  }
</style>
