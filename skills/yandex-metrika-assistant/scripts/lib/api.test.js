import { test } from 'node:test';
import assert from 'node:assert/strict';
import { metrikaGet } from './api.js';

function fakeFetch(impl) {
  const calls = [];
  const fn = async (url, opts) => {
    calls.push({ url, opts });
    return impl(url, opts);
  };
  fn.calls = calls;
  return fn;
}

test('metrikaGet: builds url, sets Authorization header, returns parsed json', async () => {
  const fetchFn = fakeFetch(async () => ({
    ok: true,
    status: 200,
    json: async () => ({ data: [{ x: 1 }] }),
  }));
  const result = await metrikaGet('/stat/v1/data', { ids: 123, metrics: 'ym:s:visits' }, {
    token: 'y0_secret',
    fetch: fetchFn,
  });
  assert.deepEqual(result, { data: [{ x: 1 }] });
  const { url, opts } = fetchFn.calls[0];
  assert.match(url, /^https:\/\/api-metrika\.yandex\.net\/stat\/v1\/data\?/);
  assert.match(url, /ids=123/);
  assert.match(url, /metrics=ym%3As%3Avisits/);
  assert.equal(opts.headers.Authorization, 'OAuth y0_secret');
});

test('metrikaGet: 401 throws "Token rejected"', async () => {
  const fetchFn = fakeFetch(async () => ({
    ok: false,
    status: 401,
    json: async () => ({ message: 'unauthorized' }),
    headers: new Map(),
  }));
  await assert.rejects(
    () => metrikaGet('/stat/v1/data', {}, { token: 'bad', fetch: fetchFn }),
    /Token rejected.*setup\.js/
  );
});

test('metrikaGet: 403 throws access error', async () => {
  const fetchFn = fakeFetch(async () => ({
    ok: false,
    status: 403,
    json: async () => ({ message: 'forbidden' }),
    headers: new Map(),
  }));
  await assert.rejects(
    () => metrikaGet('/stat/v1/data', { ids: 999 }, { token: 't', fetch: fetchFn }),
    /no access.*999/
  );
});

test('metrikaGet: 429 throws Retry-After message', async () => {
  const fetchFn = fakeFetch(async () => ({
    ok: false,
    status: 429,
    json: async () => ({}),
    headers: new Map([['retry-after', '42']]),
  }));
  await assert.rejects(
    () => metrikaGet('/stat/v1/data', {}, { token: 't', fetch: fetchFn }),
    /Quota exceeded.*42/
  );
});

test('metrikaGet: 4xx with message field bubbles up', async () => {
  const fetchFn = fakeFetch(async () => ({
    ok: false,
    status: 400,
    json: async () => ({ message: 'invalid metric ym:s:bogus' }),
    headers: new Map(),
  }));
  await assert.rejects(
    () => metrikaGet('/stat/v1/data', {}, { token: 't', fetch: fetchFn }),
    /invalid metric ym:s:bogus/
  );
});

test('metrikaGet: token never appears in error messages', async () => {
  const fetchFn = fakeFetch(async () => ({
    ok: false,
    status: 500,
    json: async () => ({ message: 'oops' }),
    headers: new Map(),
  }));
  try {
    await metrikaGet('/stat/v1/data', {}, { token: 'y0_SECRET_VALUE', fetch: fetchFn });
    assert.fail('should have thrown');
  } catch (e) {
    assert.equal(e.message.includes('y0_SECRET_VALUE'), false);
  }
});

test('metrikaGet: array params (e.g., metrics list) joined with comma', async () => {
  const fetchFn = fakeFetch(async () => ({
    ok: true,
    status: 200,
    json: async () => ({}),
  }));
  await metrikaGet('/stat/v1/data', { metrics: ['ym:s:visits', 'ym:s:users'] }, {
    token: 't',
    fetch: fetchFn,
  });
  assert.match(fetchFn.calls[0].url, /metrics=ym%3As%3Avisits%2Cym%3As%3Ausers/);
});
