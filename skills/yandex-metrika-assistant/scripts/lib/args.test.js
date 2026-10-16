import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseArgs } from './args.js';

test('parseArgs: long flag with value (--counter primary_site)', () => {
  const out = parseArgs(['--counter', 'primary_site']);
  assert.equal(out.counter, 'primary_site');
});

test('parseArgs: --flag=value form', () => {
  const out = parseArgs(['--from=7daysAgo']);
  assert.equal(out.from, '7daysAgo');
});

test('parseArgs: boolean flag (--utm with no value)', () => {
  const out = parseArgs(['--utm', '--limit', '10']);
  assert.equal(out.utm, true);
  assert.equal(out.limit, '10');
});

test('parseArgs: missing flags become undefined', () => {
  const out = parseArgs([]);
  assert.equal(out.counter, undefined);
});

test('parseArgs: --help is set true', () => {
  const out = parseArgs(['--help']);
  assert.equal(out.help, true);
});

test('parseArgs: ignores leading non-flag tokens', () => {
  const out = parseArgs(['positional', '--counter', 'x']);
  assert.equal(out.counter, 'x');
});
