<script lang="ts">
  import { t } from "svelte-i18n";
  import { language } from "../stores/language";
  import { createEventDispatcher } from "svelte";
  import { fly, fade } from "svelte/transition";

  export let open = false;
  const dispatch = createEventDispatcher();

  function close() {
    dispatch("close");
  }

  function setLang(lang: string) {
    language.setLanguage(lang);
  }
</script>

{#if open}
  <!-- Backdrop -->
  <div class="backdrop" transition:fade={{ duration: 200 }} on:click={close} on:keydown={(e) => e.key === "Escape" && close()} role="button" tabindex="-1" aria-label="Close settings"></div>

  <!-- Panel -->
  <aside class="panel" transition:fly={{ x: 320, duration: 280, opacity: 1 }} aria-label={$t("settings.title")}>
    <div class="panel-header">
      <div class="panel-title">
        <span class="panel-title-en">{$t("settings.title")}</span>
      </div>
      <button class="close-btn" on:click={close} aria-label={$t("settings.close")}>
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
          <path d="M1 1l12 12M13 1L1 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
        </svg>
      </button>
    </div>

    <div class="panel-body">
      <div class="setting-row">
        <span class="setting-label">{$t("settings.language")}</span>
        <div class="lang-group">
          <button class="lang-btn" class:active={$language === "en"} on:click={() => setLang("en")}>
            <span class="lang-flag">EN</span>
            <span class="lang-name">{$t("settings.english")}</span>
          </button>
          <button class="lang-btn" class:active={$language === "ja"} on:click={() => setLang("ja")}>
            <span class="lang-flag">日</span>
            <span class="lang-name">{$t("settings.japanese")}</span>
          </button>
        </div>
      </div>

      <div class="divider"></div>

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
    background: rgba(0, 0, 0, 0.55);
    z-index: 50;
    cursor: default;
  }

  .panel {
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    width: 300px;
    background: #0e1117;
    border-left: 1px solid #1e2530;
    z-index: 51;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.5rem;
    border-bottom: 1px solid #1e2530;
  }

  .panel-title-en {
    font-family: "IBM Plex Mono", monospace;
    font-size: 0.7rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #8899aa;
  }

  .close-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 4px;
    border: 1px solid #1e2530;
    background: transparent;
    color: #556677;
    cursor: pointer;
    transition:
      color 0.15s,
      border-color 0.15s;
  }
  .close-btn:hover {
    color: #c9d1d9;
    border-color: #2e3b4b;
  }

  .panel-body {
    flex: 1;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .setting-label {
    font-family: "IBM Plex Mono", monospace;
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #556677;
    display: block;
    margin-bottom: 0.75rem;
  }

  .lang-group {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  .lang-btn {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.7rem 0.9rem;
    background: transparent;
    border: 1px solid #1e2530;
    border-radius: 6px;
    color: #667788;
    cursor: pointer;
    transition: all 0.15s;
    text-align: left;
  }
  .lang-btn:hover {
    border-color: #2e3b4b;
    color: #aabbcc;
  }
  .lang-btn.active {
    border-color: #2a7fff40;
    background: #2a7fff0a;
    color: #6aacff;
  }

  .lang-flag {
    font-family: "IBM Plex Mono", monospace;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    min-width: 20px;
  }

  .lang-name {
    font-size: 0.85rem;
    font-family: "IBM Plex Sans", sans-serif;
  }

  .divider {
    height: 1px;
    background: #1e2530;
    margin: 0 -1.5rem;
    width: calc(100% + 3rem);
  }

  .meta {
    display: flex;
    justify-content: space-between;
    font-family: "IBM Plex Mono", monospace;
    font-size: 0.65rem;
    color: #334455;
    letter-spacing: 0.06em;
    margin-top: auto;
  }
</style>
