import { test } from 'node:test';
import assert from 'node:assert/strict';
import { shiftPeriod, computeDelta } from './compare-periods.js';

test('shiftPeriod: 7d period', () => {
  const { date1, date2 } = shiftPeriod('2026-04-19', '2026-04-25');
  assert.equal(date1, '2026-04-12');
  assert.equal(date2, '2026-04-18');
});

test('shiftPeriod: 30d period', () => {
  const { date1, date2 } = shiftPeriod('2026-03-27', '2026-04-25');
  assert.equal(date1, '2026-02-25');
  assert.equal(date2, '2026-03-26');
});

test('shiftPeriod: month boundary', () => {
  // Current period: 2026-03-01..2026-03-31 (31 days).
  // Previous: ends 2026-02-28, starts 31 days back → 2026-01-29.
  const { date1, date2 } = shiftPeriod('2026-03-01', '2026-03-31');
  assert.equal(date1, '2026-01-29');
  assert.equal(date2, '2026-02-28');
});

test('computeDelta: percent change for absolute metric', () => {
  assert.equal(computeDelta(110, 100, 'pct'), '+10.0%');
  assert.equal(computeDelta(80, 100, 'pct'), '-20.0%');
  assert.equal(computeDelta(100, 100, 'pct'), '+0.0%');
});

test('computeDelta: zero previous → "n/a"', () => {
  assert.equal(computeDelta(50, 0, 'pct'), 'n/a');
});

test('computeDelta: percentage-points for ratio metric', () => {
  // bounce rate: 24.1% vs 21.8% → -2.3pp
  assert.equal(computeDelta(21.8, 24.1, 'pp'), '-2.3pp');
});
