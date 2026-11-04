// frontend/src/lib/api.ts
import { PUBLIC_API_URL } from '$app/env/public';

export type Method = 'hybrid' | 'token_set' | 'token_sort' | 'ratio' | 'jaro_winkler' | 'levenshtein';

export type Match = {
  unique_id: string;
  name: string;
  name_type: string;
  designation_type: string;
  regime: string;
  score: number;
};

export async function screenName(name: string, method: Method, threshold: number, limit = 10) {
  const params = new URLSearchParams({
    name,
    method,
    threshold: String(threshold),
    limit: String(limit),
  });
  const res = await fetch(`${PUBLIC_API_URL}/screen?${params}`);
  if (!res.ok) throw new Error(`API returned ${res.status}`);
  const data: { query: string; method: Method; matches: Match[] } = await res.json();
  return data.matches;
}