<script lang="ts">
  import '../app.css';
  import { onMount } from 'svelte';
  import { PUBLIC_API_URL } from '$app/env/public';
  import { screenName, type Match, type Method } from '#lib/api.ts';

  // Default threshold for each method, based on the evaluation results
  const METHODS: { value: Method; label: string; threshold: number }[] = [
    { value: 'hybrid', label: 'Hybrid (recommended)', threshold: 85 },
    { value: 'token_set', label: 'Token set', threshold: 85 },
    { value: 'token_sort', label: 'Token sort', threshold: 85 },
    { value: 'ratio', label: 'Ratio', threshold: 85 },
    { value: 'levenshtein', label: 'Levenshtein', threshold: 85 },
    { value: 'jaro_winkler', label: 'Jaro-Winkler', threshold: 93 },
  ];

  let info = $state<{ report_date: string; names: number } | null>(null);
  let name = $state('');
  let method = $state<Method>('hybrid');
  let threshold = $state(85);
  let matches = $state<Match[] | null>(null);
  let loading = $state(false);
  let error = $state<string | null>(null);

  // Load the list version once, when the page opens
  onMount(async () => {
    try {
      const res = await fetch(`${PUBLIC_API_URL}/list-info`);
      info = await res.json();
    } catch {
      error = 'Could not reach the API. Is the backend running?';
    }
  });

  // When the method changes, move the slider to that method's default threshold
  function changeMethod(event: Event) {
    method = (event.target as HTMLSelectElement).value as Method;
    threshold = METHODS.find((m) => m.value === method)!.threshold;
  }

  async function search(event: SubmitEvent) {
    event.preventDefault();
    if (!name.trim()) return;
    loading = true;
    error = null;
    try {
      matches = await screenName(name, method, threshold);
    } catch {
      error = 'Search failed. Is the backend running?';
      matches = null;
    } finally {
      loading = false;
    }
  }

  // Colour each score by how likely a hit it is
  function scoreClass(score: number) {
    if (score >= 85) return 'high';
    if (score >= 70) return 'medium';
    return 'low';
  }
</script>

<main>
  <header>
    <h1 class="title">SENTRA</h1>
    {#if info}
      <p class="list-info">
        UK Sanctions List, dated {info.report_date}: {info.names.toLocaleString()} names
      </p>
    {/if}
  </header>

  <form onsubmit={search}>
    <div class="search">
      <input
        bind:value={name}
        placeholder="Enter a name to screen"
        aria-label="Name to screen"
        autocomplete="off"
        spellcheck="false"
      />
      <button type="submit" disabled={loading}>{loading ? 'Screening…' : 'Screen'}</button>
    </div>

    <div class="controls">
      <label class="field">
        <span class="field-label">Method</span>
        <span class="select">
          <select value={method} onchange={changeMethod}>
            {#each METHODS as m}
              <option value={m.value}>{m.label}</option>
            {/each}
          </select>
        </span>
      </label>

      <label class="field threshold">
        <span class="field-label">Threshold <output>{threshold}</output></span>
        <input type="range" min="0" max="100" bind:value={threshold} />
      </label>
    </div>

    {#if method === 'jaro_winkler'}
      <p class="note">Jaro-Winkler scores run high, so it needs a higher threshold than the other methods.</p>
    {/if}
  </form>

  <section class="results" aria-live="polite">
    {#if error}
      <p class="error">{error}</p>
    {:else if matches && matches.length === 0}
      <p class="empty">No matches at or above {threshold}.</p>
    {:else if matches}
      <p class="count">
        {matches.length} {matches.length === 1 ? 'match' : 'matches'} at or above {threshold}
      </p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Name type</th>
              <th>Type</th>
              <th>Regime</th>
              <th>ID</th>
              <th class="num">Score</th>
            </tr>
          </thead>
          <tbody>
            {#each matches as m}
              <tr>
                <td class="name">{m.name}</td>
                <td>{m.name_type}</td>
                <td>{m.designation_type}</td>
                <td>{m.regime}</td>
                <td class="id">{m.unique_id}</td>
                <td class="num">
                  <span class="score {scoreClass(m.score)}" style:--score="{m.score}%">
                    <span class="bar" aria-hidden="true"></span>
                    {m.score}
                  </span>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </section>
</main>

<style>
  /* Page canvas: these apply to the whole document */
  :global(:root) {
    --bg: #fafafa;
    --surface: #ffffff;
    --border: rgba(0, 0, 0, 0.08);
    --border-strong: rgba(0, 0, 0, 0.2);
    --text: #111113;
    --text-secondary: #5c5c66;
    --text-tertiary: #8a8a94;
    --high: #c4182f;
    --medium: #b26a00;
    --radius: 6px;
    --ease: cubic-bezier(0.16, 1, 0.3, 1);
    color-scheme: light;
  }

  @media (prefers-color-scheme: dark) {
    :global(:root) {
      --bg: #0c0c0e;
      --surface: #141417;
      --border: rgba(255, 255, 255, 0.08);
      --border-strong: rgba(255, 255, 255, 0.22);
      --text: #ededf0;
      --text-secondary: #a1a1aa;
      --text-tertiary: #71717a;
      --high: #ff5c6c;
      --medium: #e0a33a;
      color-scheme: dark;
    }
  }

  :global(body) {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    -webkit-font-smoothing: antialiased;
  }

  main {
    max-width: 960px;
    margin: 0 auto;
    padding: clamp(3rem, 10vw, 6rem) 1.25rem 6rem;
  }

  /* Header */
  header {
    margin-bottom: 3rem;
  }

  .title {
    font-size: 1rem;
    font-weight: 600;
    margin: 0 0 0.5rem;
  }

  .list-info {
    margin: 0;
    font-size: 0.8125rem;
    color: var(--text-tertiary);
  }

  /* Search row: the main moment on the page */
  form {
    margin-bottom: 3rem;
  }

  .search {
    display: flex;
    align-items: center;
    border-bottom: 1px solid var(--border-strong);
    transition: border-color 200ms var(--ease);
  }

  .search:focus-within {
    border-color: var(--text);
  }

  .search input {
    flex: 1;
    min-width: 0;
    padding: 1rem 0;
    border: 0;
    background: none;
    color: var(--text);
    font-size: clamp(1.125rem, 3vw, 1.5rem);
    outline: none;
  }

  .search input::placeholder {
    color: var(--text-tertiary);
  }

  button {
    flex-shrink: 0;
    padding: 0.625rem 1.25rem;
    border: 1px solid var(--text);
    border-radius: var(--radius);
    background: var(--text);
    color: var(--bg);
    font-size: 0.875rem;
    cursor: pointer;
    transition: opacity 200ms var(--ease);
  }

  button:hover:not(:disabled) {
    opacity: 0.85;
  }

  button:disabled {
    opacity: 0.5;
    cursor: progress;
  }

  /* Method and threshold */
  .controls {
    display: flex;
    flex-wrap: wrap;
    gap: 1.5rem 2.5rem;
    margin-top: 1.5rem;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .field-label {
    display: flex;
    justify-content: space-between;
    font-size: 0.75rem;
    color: var(--text-tertiary);
  }

  .field-label output {
    color: var(--text);
    font-variant-numeric: tabular-nums;
  }

  .select {
    position: relative;
  }

  .select::after {
    content: '';
    position: absolute;
    right: 0.75rem;
    top: 50%;
    width: 0.375rem;
    height: 0.375rem;
    border-right: 1px solid var(--text-secondary);
    border-bottom: 1px solid var(--text-secondary);
    transform: translateY(-75%) rotate(45deg);
    pointer-events: none;
  }

  select {
    appearance: none;
    min-width: 15rem;
    padding: 0.5rem 2.25rem 0.5rem 0.75rem;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--surface);
    color: var(--text);
    font-size: 0.875rem;
    cursor: pointer;
    transition: border-color 200ms var(--ease);
  }

  select:hover {
    border-color: var(--border-strong);
  }

  .threshold {
    flex: 1;
    min-width: 14rem;
    max-width: 22rem;
  }

  input[type='range'] {
    width: 100%;
    margin: 0.5rem 0 0;
    accent-color: var(--text);
    cursor: pointer;
  }

  .note {
    margin: 1.25rem 0 0;
    font-size: 0.8125rem;
    color: var(--text-secondary);
  }

  /* Results */
  .count,
  .empty {
    margin: 0 0 1rem;
    font-size: 0.8125rem;
    color: var(--text-secondary);
  }

  .error {
    margin: 0;
    font-size: 0.875rem;
    color: var(--high);
  }

  .table-wrap {
    overflow-x: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8125rem;
  }

  th {
    padding: 0 1rem 0.75rem 0;
    border-bottom: 1px solid var(--border-strong);
    text-align: left;
    font-weight: 400;
    color: var(--text-tertiary);
    white-space: nowrap;
  }

  td {
    padding: 0.875rem 1rem 0.875rem 0;
    border-bottom: 1px solid var(--border);
    color: var(--text-secondary);
    vertical-align: top;
  }

  tbody tr {
    transition: background-color 150ms var(--ease);
  }

  tbody tr:hover {
    background: var(--surface);
  }

  td.name {
    color: var(--text);
  }

  td.id {
    white-space: nowrap;
  }

  .num {
    padding-right: 0;
    text-align: right;
  }

  /* Score: number plus a thin bar showing its size */
  .score {
    display: inline-flex;
    align-items: center;
    gap: 0.625rem;
    font-variant-numeric: tabular-nums;
  }

  .bar {
    width: 3rem;
    height: 2px;
    background: linear-gradient(to right, currentColor var(--score), var(--border) var(--score));
  }

  .score.high {
    color: var(--high);
    font-weight: 600;
  }

  .score.medium {
    color: var(--medium);
  }

  .score.low {
    color: var(--text-tertiary);
  }

  /* Keyboard focus */
  button:focus-visible,
  select:focus-visible,
  input[type='range']:focus-visible {
    outline: 2px solid var(--text);
    outline-offset: 2px;
  }

  @media (max-width: 480px) {
    .search {
      flex-direction: column;
      align-items: stretch;
      border-bottom: 0;
      gap: 0.75rem;
    }

    .search input {
      border-bottom: 1px solid var(--border-strong);
    }

    select {
      min-width: 0;
      width: 100%;
    }

    .threshold {
      max-width: none;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    * {
      transition: none !important;
    }
  }
</style>