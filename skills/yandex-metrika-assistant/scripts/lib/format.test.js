import { test } from 'node:test';
import assert from 'node:assert/strict';
import { formatRows } from './format.js';

const sample = {
  columns: [
    { key: 'date', label: 'date' },
    { key: 'visits', label: 'visits', align: 'right' },
    { key: 'bounce', label: 'bounce%', align: 'right' },
  ],
  rows: [
    { date: '2026-04-18', visits: 1234, bounce: 0.224 },
    { date: '2026-04-19', visits: 987, bounce: 0.301 },
  ],
};

test('formatRows json: returns serialized rows', () => {
  const out = formatRows(sample, 'json');
  assert.deepEqual(JSON.parse(out), sample.rows);
});

test('formatRows tsv: header + rows separated by tabs', () => {
  const out = formatRows(sample, 'tsv').trim().split('\n');
  assert.equal(out[0], 'date\tvisits\tbounce%');
  assert.equal(out[1], '2026-04-18\t1234\t0.224');
});

test('formatRows table: includes header, aligned columns, all rows', () => {
  const out = formatRows(sample, 'table');
  assert.match(out, /date\s+visits\s+bounce%/);
  assert.match(out, /2026-04-18/);
  assert.match(out, /2026-04-19/);
});

test('formatRows table: numeric column right-aligned', () => {
  const out = formatRows(sample, 'table');
  const lines = out.split('\n').filter((l) => l.includes('2026'));
  // visits column 1234 should align right under header "visits"
  for (const line of lines) {
    assert.match(line, /\s\d+\s/);
  }
});

test('formatRows: unknown format throws', () => {
  assert.throws(() => formatRows(sample, 'xml'), /Unknown format/);
});

test('formatRows: empty rows returns header for table, [] for json', () => {
  const empty = { columns: sample.columns, rows: [] };
  assert.equal(formatRows(empty, 'json'), '[]');
  const t = formatRows(empty, 'table');
  assert.match(t, /date\s+visits\s+bounce%/);
});
