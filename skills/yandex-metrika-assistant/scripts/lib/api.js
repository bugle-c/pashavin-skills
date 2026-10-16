const BASE = 'https://api-metrika.yandex.net';

export async function metrikaGet(path, params = {}, opts = {}) {
  const fetchFn = opts.fetch || globalThis.fetch;
  const token = opts.token;
  if (!token) throw new Error('metrikaGet: no token provided');

  const url = new URL(BASE + path);
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null) continue;
    const value = Array.isArray(v) ? v.join(',') : String(v);
    url.searchParams.set(k, value);
  }

  const res = await fetchFn(url.toString(), {
    headers: { Authorization: `OAuth ${token}` },
  });

  if (res.ok) {
    return await res.json();
  }

  let body = {};
  try {
    body = await res.json();
  } catch {
    // ignore parse errors
  }

  if (res.status === 401) {
    throw new Error('Token rejected (HTTP 401). Run setup.js to refresh.');
  }
  if (res.status === 403) {
    const ids = params.ids ?? '<unknown>';
    throw new Error(
      `Token has no access to counter ${ids} (HTTP 403). ` +
      'Check OAuth scopes — see references/auth-and-token.md.'
    );
  }
  if (res.status === 429) {
    const retry = (res.headers.get?.('retry-after') ?? res.headers.get?.('Retry-After')) || '?';
    throw new Error(`Quota exceeded (HTTP 429). Retry after ${retry}s.`);
  }

  const msg = body.message || body.error || res.statusText || `HTTP ${res.status}`;
  throw new Error(`Metrika API error (HTTP ${res.status}): ${msg}`);
}
