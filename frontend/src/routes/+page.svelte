<script lang="ts">
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
  <h1>Sentra</h1>
  {#if info}
    <p class="list-info">
      UK Sanctions List, dated {info.report_date}: {info.names.toLocaleString()} names
    </p>
  {/if}

  <form onsubmit={search}>
    <input bind:value={name} placeholder="Enter a name to screen" />

    <select value={method} onchange={changeMethod}>
      {#each METHODS as m}
        <option value={m.value}>{m.label}</option>
      {/each}
    </select>

    <label>
      Threshold: {threshold}
      <input type="range" min="0" max="100" bind:value={threshold} />
    </label>

    <button type="submit" disabled={loading}>{loading ? 'Screening…' : 'Screen'}</button>
  </form>

  {#if method === 'jaro_winkler'}
    <p class="note">Jaro-Winkler scores run high, so it needs a higher threshold than the other methods.</p>
  {/if}

  {#if error}
    <p class="error">{error}</p>
  {:else if matches && matches.length === 0}
    <p>No matches at or above {threshold}.</p>
  {:else if matches}
    <table>
      <thead>
        <tr><th>Name</th><th>Name type</th><th>Type</th><th>Regime</th><th>ID</th><th>Score</th></tr>
      </thead>
      <tbody>
        {#each matches as m}
          <tr>
            <td>{m.name}</td>
            <td>{m.name_type}</td>
            <td>{m.designation_type}</td>
            <td>{m.regime}</td>
            <td>{m.unique_id}</td>
            <td class={scoreClass(m.score)}>{m.score}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  {/if}
</main>

<style>
  main { max-width: 960px; margin: 2rem auto; padding: 0 1rem; font-family: system-ui, sans-serif; }
  .list-info, .note { color: #666; }
  form { display: flex; gap: 0.75rem; flex-wrap: wrap; align-items: center; margin: 1.5rem 0; }
  input:not([type='range']) { flex: 1; min-width: 220px; padding: 0.5rem; }
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 0.5rem; border-bottom: 1px solid #ddd; }
  .high { color: #b00020; font-weight: bold; }
  .medium { color: #b26a00; }
  .low { color: #888; }
  .error { color: #b00020; }
</style>