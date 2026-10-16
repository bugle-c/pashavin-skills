import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, mkdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { loadConfig, resolveCounter } from './config.js';

function withTempHome(fn) {
  const dir = mkdtempSync(join(tmpdir(), 'ym-cfg-'));
  mkdirSync(join(dir, '.config', 'yandex-metrika'), { recursive: true });
  const oldHome = process.env.HOME;
  const oldToken = process.env.YANDEX_METRIKA_OAUTH_TOKEN;
  process.env.HOME = dir;
  delete process.env.YANDEX_METRIKA_OAUTH_TOKEN;
  try {
    return fn(dir);
  } finally {
    process.env.HOME = oldHome;
    if (oldToken !== undefined) process.env.YANDEX_METRIKA_OAUTH_TOKEN = oldToken;
    rmSync(dir, { recursive: true, force: true });
  }
}

test('loadConfig reads token and counters from ~/.config/yandex-metrika/config.json', () => {
  withTempHome((home) => {
    writeFileSync(
      join(home, '.config/yandex-metrika/config.json'),
      JSON.stringify({
        token: 'y0_test',
        default_counter: 'primary_site',
        counters: { primary_site: 111, secondary_site: 222 },
      })
    );
    const cfg = loadConfig();
    assert.equal(cfg.token, 'y0_test');
    assert.equal(cfg.default_counter, 'primary_site');
    assert.deepEqual(cfg.counters, { primary_site: 111, secondary_site: 222 });
  });
});

test('loadConfig: env YANDEX_METRIKA_OAUTH_TOKEN overrides config token', () => {
  withTempHome((home) => {
    writeFileSync(
      join(home, '.config/yandex-metrika/config.json'),
      JSON.stringify({ token: 'from_file', counters: {}, default_counter: null })
    );
    process.env.YANDEX_METRIKA_OAUTH_TOKEN = 'from_env';
    const cfg = loadConfig();
    assert.equal(cfg.token, 'from_env');
  });
});

test('loadConfig: env token works without config file (counters empty)', () => {
  withTempHome(() => {
    process.env.YANDEX_METRIKA_OAUTH_TOKEN = 'from_env';
    const cfg = loadConfig();
    assert.equal(cfg.token, 'from_env');
    assert.deepEqual(cfg.counters, {});
    assert.equal(cfg.default_counter, null);
  });
});

test('loadConfig throws helpful error when no token anywhere', () => {
  withTempHome(() => {
    assert.throws(() => loadConfig(), /No token found.*setup\.js/);
  });
});

test('resolveCounter: alias resolves to numeric id', () => {
  const cfg = { counters: { primary_site: 111, secondary_site: 222 }, default_counter: 'primary_site' };
  assert.equal(resolveCounter(cfg, 'secondary_site'), 222);
});

test('resolveCounter: numeric string passes through unchanged', () => {
  const cfg = { counters: {}, default_counter: null };
  assert.equal(resolveCounter(cfg, '987654'), 987654);
});

test('resolveCounter: undefined uses default_counter alias', () => {
  const cfg = { counters: { primary_site: 111 }, default_counter: 'primary_site' };
  assert.equal(resolveCounter(cfg, undefined), 111);
});

test('resolveCounter: unknown alias throws with list of known aliases', () => {
  const cfg = { counters: { primary_site: 111, secondary_site: 222 }, default_counter: 'primary_site' };
  assert.throws(
    () => resolveCounter(cfg, 'unknown_site'),
    /Unknown counter 'unknown_site'.*primary_site.*secondary_site/s
  );
});

test('resolveCounter: no default and no flag throws', () => {
  const cfg = { counters: { primary_site: 111 }, default_counter: null };
  assert.throws(() => resolveCounter(cfg, undefined), /No counter specified/);
});
