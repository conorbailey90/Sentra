<script lang="ts">
  import { page } from '$app/state';

  type Link = { href: string; label: string };

  // Pass your own links, or edit these defaults
  let { links = [{ href: '/', label: 'Screen' }] }: { links?: Link[] } = $props();

  // A link counts as active on its own path and any path beneath it
  function isActive(href: string) {
    const path = page.url.pathname;
    return href === '/' ? path === '/' : path === href || path.startsWith(href + '/');
  }
</script>

<header class="nav">
  <nav aria-label="Main">
    <a href="/" class="wordmark">SENTRA</a>

    <ul>
      {#each links as link}
        <li>
          <a href={link.href} aria-current={isActive(link.href) ? 'page' : undefined}>
            {link.label}
          </a>
        </li>
      {/each}
    </ul>
  </nav>
</header>

<style>
  .nav {
    position: sticky;
    top: 0;
    z-index: 10;
    background: color-mix(in srgb, var(--bg) 80%, transparent);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
  }

  nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1.5rem;
    max-width: 960px;
    height: 3.5rem;
    margin: 0 auto;
    padding: 0 1.25rem;
  }

  a {
    color: inherit;
    text-decoration: none;
  }

  .wordmark {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text);
  }

  ul {
    display: flex;
    gap: 1.5rem;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  ul a {
    font-size: 0.8125rem;
    color: var(--text-tertiary);
    transition: color 200ms var(--ease);
  }

  ul a:hover,
  ul a[aria-current='page'] {
    color: var(--text);
  }

  a:focus-visible {
    outline: 2px solid var(--text);
    outline-offset: 4px;
    border-radius: 2px;
  }

  @media (prefers-reduced-motion: reduce) {
    ul a {
      transition: none;
    }
  }
</style>