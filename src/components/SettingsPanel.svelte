<script lang="ts">
  import { t } from "svelte-i18n";
  import { language } from "../stores/language";
  import { defaultTheme, savedThemePresets, theme } from "../stores/theme";
  import { createEventDispatcher } from "svelte";
  import { fly, fade } from "svelte/transition";

  export let open = false;
  const dispatch = createEventDispatcher();

  let presetName = "";
  let selectedPresetId = "";

  const languageOptions = [
    { value: "en", label: "English" },
    { value: "ja", label: "Japanese" }
  ];

  const themeFields: Array<{ key: keyof typeof defaultTheme; label: string }> = [
    { key: "primary", label: "Primary" },
    { key: "accent", label: "Accent" },
    { key: "secondary", label: "Secondary" },
    { key: "background", label: "Background" },
    { key: "surface", label: "Surface" },
    { key: "success", label: "Success" },
    { key: "warning", label: "Warning" },
    { key: "danger", label: "Danger" }
  ];

  $: if ($savedThemePresets.length > 0 && !$savedThemePresets.some((preset) => preset.id === selectedPresetId)) {
    selectedPresetId = $savedThemePresets[0].id;
  }

  $: if ($savedThemePresets.length === 0) {
    selectedPresetId = "";
  }

  function close() {
    dispatch("close");
  }

  function setLang(lang: string) {
    language.setLanguage(lang);
  }

  function savePreset() {
    const presetId = theme.savePreset(presetName);
    if (presetId) {
      selectedPresetId = presetId;
      presetName = "";
    }
  }

  function applySelectedPreset() {
    if (!selectedPresetId) return;
    theme.applyPreset(selectedPresetId);
  }

  function deleteSelectedPreset() {
    if (!selectedPresetId) return;
    const currentId = selectedPresetId;
    selectedPresetId = "";
    theme.deletePreset(currentId);
  }
</script>

{#if open}
  <div class="backdrop" transition:fade={{ duration: 160 }} on:click={close} on:keydown={(e) => e.key === "Escape" && close()} role="button" tabindex="-1" aria-label="Close settings"></div>

  <aside class="panel" transition:fly={{ x: 240, duration: 220, opacity: 1 }} aria-label={$t("settings.title")}>
    <div class="panel-header">
      <div>
        <span class="eyebrow">Preferences</span>
        <h2 class="panel-title">{$t("settings.title")}</h2>
      </div>
      <button class="close-btn" on:click={close} aria-label={$t("settings.close")}>
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M1 1l12 12M13 1L1 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
        </svg>
      </button>
    </div>

    <div class="panel-body">
      <section class="settings-section">
        <div class="section-heading">
          <span class="setting-label">{$t("settings.language")}</span>
        </div>

        <label class="select-field">
          <span class="sr-only">{$t("settings.language")}</span>
          <select value={$language} on:change={(e) => setLang((e.currentTarget as HTMLSelectElement).value)}>
            {#each languageOptions as option}
              <option value={option.value}>{option.label}</option>
            {/each}
          </select>
        </label>
      </section>

      <section class="settings-section">
        <div class="section-heading split">
          <span class="setting-label">Theme</span>
          <button class="text-btn" on:click={() => theme.reset()}>Reset</button>
        </div>

        <div class="preset-stack">
          <div class="preset-row">
            <input
              class="preset-input"
              type="text"
              bind:value={presetName}
              placeholder="Preset name"
              maxlength="32"
            />
            <button class="mini-btn primary" on:click={savePreset} disabled={!presetName.trim()}>Save</button>
          </div>

          <div class="preset-row">
            <select class="preset-select" bind:value={selectedPresetId} disabled={$savedThemePresets.length === 0}>
              <option value="" disabled>Saved presets</option>
              {#each $savedThemePresets as preset}
                <option value={preset.id}>{preset.name}</option>
              {/each}
            </select>
            <button class="mini-btn" on:click={applySelectedPreset} disabled={!selectedPresetId}>Apply</button>
            <button class="mini-btn danger" on:click={deleteSelectedPreset} disabled={!selectedPresetId}>Delete</button>
          </div>
        </div>

        <div class="theme-list">
          {#each themeFields as field}
            <label class="theme-row">
              <span class="theme-name">{field.label}</span>
              <div class="theme-control">
                <input type="color" value={$theme[field.key]} on:input={(e) => theme.updateColor(field.key, (e.currentTarget as HTMLInputElement).value)} />
                <code>{$theme[field.key]}</code>
              </div>
            </label>
          {/each}
        </div>
      </section>

      <div class="meta">
        <span>CybrTech MCP</span>
        <span>v0.1.0</span>
      </div>
    </div>
  </aside>
{/if}

<style>
  .backdrop {
    position: fixed;
    inset: 0;
    background: rgba(5, 7, 10, 0.52);
    z-index: 50;
  }

  .panel {
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    width: min(360px, 100vw);
    background: #0a0e13;
    border-left: 1px solid rgba(113, 138, 165, 0.18);
    z-index: 51;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .panel-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    padding: 1.1rem 1.1rem 1rem;
    border-bottom: 1px solid rgba(113, 138, 165, 0.12);
  }

  .eyebrow {
    display: block;
    font-family: "IBM Plex Mono", monospace;
    font-size: 0.62rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #718aa5;
    margin-bottom: 0.3rem;
  }

  .panel-title {
    font-family: "IBM Plex Sans", sans-serif;
    font-size: 1rem;
    font-weight: 500;
    color: #e6edf3;
  }

  .close-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 8px;
    border: 1px solid rgba(113, 138, 165, 0.16);
    background: transparent;
    color: #7f95ab;
    cursor: pointer;
  }

  .close-btn:hover {
    color: #e6edf3;
    border-color: rgba(113, 138, 165, 0.32);
  }

  .panel-body {
    flex: 1;
    padding: 1rem 1.1rem 1.1rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    overflow-y: auto;
  }

  .settings-section {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    padding: 0.9rem;
    border: 1px solid rgba(113, 138, 165, 0.12);
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.015);
  }

  .section-heading {
    display: flex;
    align-items: center;
  }

  .section-heading.split {
    justify-content: space-between;
  }

  .setting-label {
    font-family: "IBM Plex Mono", monospace;
    font-size: 0.64rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #718aa5;
  }

  .select-field select,
  .preset-input,
  .preset-select {
    width: 100%;
    min-height: 36px;
    border-radius: 8px;
    border: 1px solid rgba(113, 138, 165, 0.16);
    background: #0d131a;
    color: #d6dee7;
    padding: 0.55rem 0.7rem;
    font-family: "IBM Plex Mono", monospace;
    font-size: 0.72rem;
    outline: none;
  }

  .select-field select:focus,
  .preset-input:focus,
  .preset-select:focus {
    border-color: rgba(106, 227, 255, 0.42);
  }

  .preset-stack {
    display: flex;
    flex-direction: column;
    gap: 0.55rem;
  }

  .preset-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto auto;
    gap: 0.5rem;
  }

  .preset-row:first-child {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .theme-list {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
  }

  .theme-row {
    display: grid;
    grid-template-columns: 84px minmax(0, 1fr);
    gap: 0.65rem;
    align-items: center;
    padding: 0.45rem 0.55rem;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.02);
  }

  .theme-name {
    font-family: "IBM Plex Mono", monospace;
    font-size: 0.62rem;
    color: #93a7ba;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }

  .theme-control {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 0.55rem;
    min-width: 0;
  }

  input[type="color"] {
    width: 24px;
    height: 24px;
    padding: 0;
    border: 0;
    background: transparent;
    cursor: pointer;
    flex-shrink: 0;
  }

  input[type="color"]::-webkit-color-swatch-wrapper {
    padding: 0;
  }

  input[type="color"]::-webkit-color-swatch {
    border: 1px solid rgba(113, 138, 165, 0.22);
    border-radius: 999px;
  }

  code {
    font-family: "IBM Plex Mono", monospace;
    font-size: 0.66rem;
    color: #9db1c4;
    white-space: nowrap;
  }

  .text-btn,
  .mini-btn {
    border: 1px solid rgba(113, 138, 165, 0.16);
    background: transparent;
    color: #8ea4b8;
    border-radius: 8px;
    padding: 0.48rem 0.72rem;
    font-family: "IBM Plex Mono", monospace;
    font-size: 0.66rem;
    cursor: pointer;
  }

  .text-btn:hover,
  .mini-btn:hover:not(:disabled) {
    color: #e6edf3;
    border-color: rgba(113, 138, 165, 0.3);
  }

  .mini-btn.primary {
    color: #79d9f2;
    border-color: rgba(106, 227, 255, 0.24);
    background: rgba(106, 227, 255, 0.06);
  }

  .mini-btn.danger {
    color: #f09990;
  }

  .mini-btn:disabled {
    opacity: 0.42;
    cursor: not-allowed;
  }

  .meta {
    display: flex;
    justify-content: space-between;
    margin-top: auto;
    padding-top: 0.35rem;
    font-family: "IBM Plex Mono", monospace;
    font-size: 0.62rem;
    color: #5d7083;
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  @media (max-width: 640px) {
    .panel {
      width: 100vw;
    }

    .preset-row,
    .preset-row:first-child,
    .theme-row {
      grid-template-columns: 1fr;
    }

    .theme-control {
      justify-content: flex-start;
    }
  }
</style>
