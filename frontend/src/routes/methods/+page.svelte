<script lang="ts">
  // The one example used throughout the page
  const QUERY = 'Putin Vladimir';
  const LISTED = 'Vladimir Vladimirovich Putin';

  type Method = {
    id: string;
    name: string;
    summary: string;
    how: string;
    sees: { label: string; value: string }[];
    example: string;
    goodAt: string;
    weakAt: string;
    caught: number | null; // % of real hits caught at threshold 85
    flagged: number | null; // % of innocent names flagged at threshold 85
    note: string;
  };

  const METHODS: Method[] = [
    {
      id: 'ratio',
      name: 'ratio',
      summary: 'Compares the two names character by character.',
      how: 'It counts how many characters the two names share in the same order, as a share of their combined length. Adding or removing a letter counts as one difference, so a changed letter counts as two.',
      sees: [
        { label: 'Query', value: 'putin vladimir' },
        { label: 'Listed', value: 'vladimir vladimirovich putin' }
      ],
      example: 'Low. The words are in a different order and the patronymic is missing, so few characters line up.',
      goodAt: 'Small typos in names written the same way.',
      weakAt: 'Reordered words and missing words.',
      caught: 66,
      flagged: 0.3,
      note: 'Strict to a fault: almost no false alerts, but a third of real hits missed.'
    },
    {
      id: 'levenshtein',
      name: 'levenshtein',
      summary: 'Counts the edits needed to turn one name into the other.',
      how: 'It finds the fewest single-letter insertions, deletions or substitutions that turn one name into the other, then scales that to 0–100. A changed letter counts as one edit rather than two, so typos score a little higher than with ratio.',
      sees: [
        { label: 'Query', value: 'putin vladimir' },
        { label: 'Listed', value: 'vladimir vladimirovich putin' }
      ],
      example: 'Low, for the same reasons as ratio.',
      goodAt: 'Typos.',
      weakAt: 'Reordered words and missing words.',
      caught: null,
      flagged: null,
      note: 'Not yet tested. Expect results close to ratio.'
    },
    {
      id: 'jaro_winkler',
      name: 'jaro_winkler',
      summary: 'Matches nearby characters and rewards a matching start.',
      how: 'It looks for shared characters that sit close to each other, allows for swapped letters, and adds extra credit when the first few letters match.',
      sees: [
        { label: 'Query starts', value: 'p…' },
        { label: 'Listed starts', value: 'v…' }
      ],
      example: 'Fairly low. One name starts with “Putin” and the other with “Vladimir”, so there is no matching start to reward.',
      goodAt: 'Typos in single words, including short ones.',
      weakAt: 'Reordered names and initials. Its scores run high, so unrelated names with similar starts get flagged.',
      caught: 75,
      flagged: 58.5,
      note: 'Needs a much higher threshold than the other methods.'
    },
    {
      id: 'token_sort',
      name: 'token_sort',
      summary: 'Sorts the words alphabetically, then compares.',
      how: 'It splits each name into words, sorts them alphabetically, joins them back together and then runs ratio.',
      sees: [
        { label: 'Query', value: 'putin vladimir' },
        { label: 'Listed', value: 'putin vladimir vladimirovich' }
      ],
      example: 'Word order no longer matters, but the missing “Vladimirovich” still pulls the score down.',
      goodAt: 'Reordered names.',
      weakAt: 'Missing middle names and patronymics.',
      caught: 88,
      flagged: 0.3,
      note: 'Clean, but misses most names with a dropped middle name.'
    },
    {
      id: 'token_set',
      name: 'token_set',
      summary: 'Focuses on the words both names share.',
      how: 'It splits the words into those both names share and those unique to each, compares those groups in a few combinations and keeps the best score. If every word of one name appears in the other, it scores 100.',
      sees: [
        { label: 'Shared', value: 'putin vladimir' },
        { label: 'Only in listed', value: 'vladimirovich' }
      ],
      example: '100. Both “Putin” and “Vladimir” appear in the listed name.',
      goodAt: 'Reordered names and missing words.',
      weakAt: 'One-word names. “Laura Green” scores 100 against a listed alias of “Green”.',
      caught: 98,
      flagged: 9,
      note: 'Catches almost everything, but flags too many innocent names.'
    },
    {
      id: 'hybrid',
      name: 'hybrid',
      summary: 'Picks a method based on the names being compared.',
      how: 'It counts the unique words in each name, then chooses: token_set when both names have several words; strict ratio when either name is a single word, so one word can’t match inside a longer name; and, from version 1.1, jaro_winkler when both names are a single word.',
      sees: [
        { label: 'Unique words', value: 'query 2, listed 3' },
        { label: 'Uses', value: 'token_set' }
      ],
      example: '100. Both names have several words, so it uses token_set.',
      goodAt: 'All variation types tested, with low false alerts.',
      weakAt: 'Initials with short names, and typos in very short single words.',
      caught: 97.5,
      flagged: 1.5,
      note: 'Measured before the repeated-word fix.'
    }
  ];

  const fmt = (n: number) => (n < 1 ? '<1' : String(n)) + '%';
</script>

<svelte:head>
  <title>How each matching method works · Sentra</title>
</svelte:head>

<main>
  <header class="intro">
    <a class="back" href="/">Back to search</a>
    <h1>How each matching method works</h1>
    <p>
      Every method below is tested on the same pair: a query of
      <q>{QUERY}</q> against the listed name <q>{LISTED}</q>. The words are
      reordered and the patronymic is missing, two of the most common reasons
      real hits are missed in payment screening.
    </p>
    <p class="threshold">Test results use an alert threshold of 85, on about 1,450 test names.</p>
  </header>

  {#each METHODS as m (m.id)}
    <section class="method" id={m.id} aria-labelledby="{m.id}-title">
      <h2 id="{m.id}-title"><a href="#{m.id}">{m.name}</a></h2>

      <div class="body">
        <p class="summary">{m.summary}</p>
        <p class="how">{m.how}</p>

        <div class="sees" aria-label="What this method compares in the example">
          {#each m.sees as s}
            <div class="sees-row">
              <span class="sees-label">{s.label}</span>
              <code class="sees-value">{s.value}</code>
            </div>
          {/each}
        </div>

        <dl class="facts">
          <div>
            <dt>With the example</dt>
            <dd>{m.example}</dd>
          </div>
          <div>
            <dt>Good at</dt>
            <dd>{m.goodAt}</dd>
          </div>
          <div>
            <dt>Weak at</dt>
            <dd>{m.weakAt}</dd>
          </div>
        </dl>

        <div class="results">
          {#if m.caught !== null && m.flagged !== null}
            <div class="bar-row">
              <span class="bar-label">Real hits caught</span>
              <div class="bar" role="img" aria-label="{m.caught}% of real hits caught">
                <div class="fill caught" style:width="{m.caught}%"></div>
              </div>
              <span class="bar-value">{fmt(m.caught)}</span>
            </div>
            <div class="bar-row">
              <span class="bar-label">Innocent names flagged</span>
              <div class="bar" role="img" aria-label="{m.flagged}% of innocent names flagged">
                <div class="fill flagged" style:width="{Math.max(m.flagged, 0.6)}%"></div>
              </div>
              <span class="bar-value flagged-value">{fmt(m.flagged)}</span>
            </div>
          {/if}
          <p class="note">{m.note}</p>
        </div>
      </div>
    </section>
  {/each}

  <section class="method pattern" aria-labelledby="pattern-title">
    <h2 id="pattern-title">The pattern</h2>
    <div class="body">
      <p>
        Character-based methods (<code>ratio</code>, <code>levenshtein</code>,
        <code>jaro_winkler</code>) handle typos but fail when words move or go
        missing. Word-based methods (<code>token_sort</code>, <code>token_set</code>)
        handle word order and missing words but are fooled by short names.
        No single method covers every case, which is why <code>hybrid</code>,
        choosing the right comparison for each pair of names, performs best.
      </p>
    </div>
  </section>
</main>

<style>
  /* Colours, fonts and the body background come from app.css */

  main {
    max-width: 960px;
    margin: 0 auto;
    padding: clamp(2rem, 6vw, 4rem) 1.25rem 6rem;
    line-height: 1.7;
  }

  p {
    margin: 0;
  }

  a {
    color: inherit;
    text-decoration: none;
  }

  a:focus-visible {
    outline: 2px solid var(--text);
    outline-offset: 4px;
    border-radius: 2px;
  }

  code {
    font-family: inherit;
    font-size: 0.92em;
    color: var(--text);
  }

  /* Intro */
  .intro {
    max-width: 44rem;
    margin-bottom: 4rem;
  }

  .back {
    font-size: 0.8125rem;
    color: var(--text-tertiary);
    transition: color 200ms var(--ease);
  }

  .back:hover {
    color: var(--text);
  }

  .intro h1 {
    margin: 1.5rem 0 1.25rem;
    font-size: clamp(1.375rem, 3.5vw, 1.875rem);
    font-weight: 600;
    line-height: 1.2;
  }

  .intro p {
    color: var(--text-secondary);
  }

  .intro q {
    color: var(--text);
  }

  .threshold {
    margin-top: 1rem;
    font-size: 0.8125rem;
  }

  .intro .threshold {
    color: var(--text-tertiary);
  }

  /* Each method: name in a left column, details on the right */
  .method {
    display: grid;
    grid-template-columns: 11rem minmax(0, 1fr);
    gap: 2.5rem;
    padding: 3rem 0;
    border-top: 1px solid var(--border);
    scroll-margin-top: 4.5rem; /* clears the sticky navbar when jumping to #id */
  }

  .method h2 {
    margin: 0;
    font-size: 0.9375rem;
    font-weight: 600;
    line-height: 1.7;
  }

  .method h2 a:hover {
    color: var(--text-secondary);
  }

  .body {
    max-width: 44rem;
  }

  .summary {
    color: var(--text);
  }

  .how {
    margin-top: 0.75rem;
    font-size: 0.875rem;
    color: var(--text-secondary);
  }

  /* What the method actually compares */
  .sees {
    display: grid;
    gap: 0.5rem;
    margin-top: 1.5rem;
    padding: 1rem 1.25rem;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--surface);
    overflow-x: auto;
  }

  .sees-row {
    display: grid;
    grid-template-columns: 9rem 1fr;
    gap: 1rem;
    align-items: baseline;
  }

  .sees-label {
    font-size: 0.75rem;
    color: var(--text-tertiary);
  }

  .sees-value {
    white-space: nowrap;
  }

  /* Example, good at, weak at */
  .facts {
    display: grid;
    gap: 0.75rem;
    margin: 1.5rem 0 0;
    font-size: 0.875rem;
  }

  .facts div {
    display: grid;
    grid-template-columns: 9rem 1fr;
    gap: 1rem;
  }

  .facts dt {
    color: var(--text-tertiary);
    font-size: 0.75rem;
    line-height: 2;
  }

  .facts dd {
    margin: 0;
    color: var(--text-secondary);
  }

  /* Test results */
  .results {
    margin-top: 1.75rem;
    padding-top: 1.25rem;
    border-top: 1px solid var(--border);
  }

  .bar-row {
    display: grid;
    grid-template-columns: 13rem 1fr 3.5rem;
    gap: 1rem;
    align-items: center;
    margin-bottom: 0.625rem;
  }

  .bar-label {
    font-size: 0.75rem;
    color: var(--text-tertiary);
  }

  .bar {
    height: 2px;
    background: var(--border);
  }

  .fill {
    height: 100%;
  }

  .fill.caught {
    background: var(--text);
  }

  .fill.flagged {
    background: var(--high);
  }

  .bar-value {
    text-align: right;
    font-size: 0.8125rem;
    font-variant-numeric: tabular-nums;
    color: var(--text);
  }

  .flagged-value {
    color: var(--high);
  }

  .note {
    margin-top: 0.75rem;
    font-size: 0.8125rem;
    color: var(--text-secondary);
  }

  /* Closing summary */
  .pattern .body p {
    color: var(--text-secondary);
  }

  @media (max-width: 720px) {
    .method {
      grid-template-columns: 1fr;
      gap: 1rem;
      padding: 2.25rem 0;
    }
  }

  @media (max-width: 560px) {
    .facts div,
    .sees-row {
      grid-template-columns: 1fr;
      gap: 0.125rem;
    }

    .bar-row {
      grid-template-columns: 1fr 3.5rem;
      gap: 0.375rem 1rem;
    }

    .bar-label {
      grid-column: 1 / -1;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .back {
      transition: none;
    }
  }
</style>