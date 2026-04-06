<script lang="ts">
  export let label = "";
  export let value: unknown;
  export let depth = 0;

  let open = depth < 1;

  function isObjectLike(input: unknown): input is Record<string, unknown> {
    return typeof input === "object" && input !== null && !Array.isArray(input);
  }

  function valueKind(input: unknown) {
    if (Array.isArray(input)) return "array";
    if (input === null) return "null";
    return typeof input;
  }

  function preview(input: unknown) {
    if (Array.isArray(input)) return `[${input.length}]`;
    if (isObjectLike(input)) return `{${Object.keys(input).length}}`;
    if (typeof input === "string") return `"${input}"`;
    if (input === null) return "null";
    return String(input);
  }

  $: kind = valueKind(value);
  $: entries = isObjectLike(value) ? Object.entries(value) : [];
  $: items = Array.isArray(value) ? value : [];
</script>

{#if kind === "array"}
  <div class="node">
    <button class="branch" type="button" on:click={() => (open = !open)}>
      <span class="toggle">{open ? "-" : "+"}</span>
      {#if label}<span class="key">{label}:</span>{/if}
      <span class="meta">[{(value as unknown[]).length}]</span>
    </button>
    {#if open}
      <div class="children">
        {#each items as item, index}
          <svelte:self label={String(index)} value={item} depth={depth + 1} />
        {/each}
      </div>
    {/if}
  </div>
{:else if kind === "object"}
  <div class="node">
    <button class="branch" type="button" on:click={() => (open = !open)}>
      <span class="toggle">{open ? "-" : "+"}</span>
      {#if label}<span class="key">{label}:</span>{/if}
      <span class="meta">{`{${entries.length}}`}</span>
    </button>
    {#if open}
      <div class="children">
        {#each entries as [entryKey, entryValue]}
          <svelte:self label={entryKey} value={entryValue} depth={depth + 1} />
        {/each}
      </div>
    {/if}
  </div>
{:else}
  <div class="leaf">
    {#if label}<span class="key">{label}:</span>{/if}
    <span class:string={kind === "string"} class:number={kind === "number"} class:boolean={kind === "boolean"} class:null={kind === "null"}>
      {preview(value)}
    </span>
  </div>
{/if}

<style>
  .node,
  .leaf {
    font-family: var(--font-mono);
    font-size: 0.73rem;
    line-height: 1.55;
  }

  .branch {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.2rem 0;
    border: 0;
    background: transparent;
    color: var(--text-1);
    font: inherit;
    cursor: pointer;
  }

  .toggle,
  .meta {
    color: var(--text-3);
  }

  .key {
    color: #9eb2c6;
  }

  .children {
    margin-left: 1rem;
    padding-left: 0.7rem;
    border-left: 1px solid var(--border);
  }

  .leaf {
    display: flex;
    align-items: baseline;
    gap: 0.45rem;
    padding: 0.16rem 0;
  }

  .string {
    color: #39c7b7;
  }

  .number {
    color: #e3b341;
  }

  .boolean {
    color: #39d353;
  }

  .null {
    color: var(--text-3);
  }
</style>
