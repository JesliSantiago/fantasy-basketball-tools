import type { DraftPicks, Health, Rankings } from "./types";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`/api${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const api = {
  health: () => get<Health>("/health"),
  rankings: (params: { season?: string; limit?: number } = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)]),
    );
    return get<Rankings>(`/rankings?${qs}`);
  },
  draft: () => get<DraftPicks>("/draft"),
};
