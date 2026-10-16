#!/usr/bin/env node
import { loadConfig, resolveCounter } from './lib/config.js';
import { metrikaGet } from './lib/api.js';
import { formatRows } from './lib/format.js';
import { parseArgs } from './lib/args.js';

const PERIOD_MAP = { '7d': 7, '14d': 14, '30d': 30, '90d': 90 };

export function shiftPeriod(date1, date2) {
  const d1 = new Date(date1 + 'T00:00:00Z');
  const d2 = new Date(date2 + 'T00:00:00Z');
  const lenDays = Math.round((d2 - d1) / 86400000) + 1;
  const prevEnd = new Date(d1.getTime() - 86400000);
  const prevStart = new Date(prevEnd.getTime() - (lenDays - 1) * 86400000);
  const fmt = (d) => d.toISOString().slice(0, 10);
  return { date1: fmt(prevStart), date2: fmt(prevEnd) };
}

export function computeDelta(current, previous, kind) {
  if (kind === 'pp') {
    const diff = Number(current) - Number(previous);
    const sign = diff >= 0 ? '+' : '';
    return `${sign}${diff.toFixed(1)}pp`;
  }
  if (Number(previous) === 0) return 'n/a';
  const pct = ((Number(current) - Number(previous)) / Number(previous)) * 100;
  const sign = pct >= 0 ? '+' : '';
  return `${sign}${pct.toFixed(1)}%`;
}

function todayMinus(days) {
  const d = new Date(Date.now() - days * 86400000);
  return d.toISOString().slice(0, 10);
}

async function fetchAggregates(cfg, counterId, date1, date2) {
  const res = await metrikaGet('/stat/v1/data', {
    ids: counterId,
    metrics: ['ym:s:visits', 'ym:s:pageviews', 'ym:s:users', 'ym:s:bounceRate', 'ym:s:avgVisitDurationSeconds'],
    date1,
    date2,
    accuracy: 'full',
  }, { token: cfg.token });
  const totals = res.totals || res.data?.[0]?.metrics || [0, 0, 0, 0, 0];
  return {
    visits: totals[0] || 0,
    pageviews: totals[1] || 0,
    users: totals[2] || 0,
    bounce: totals[3] || 0,
    avg_dur_sec: totals[4] || 0,
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const format = args.format || 'table';
  const cfg = loadConfig();
  const counterId = resolveCounter(cfg, args.counter);

  let date1, date2, prev1, prev2;
  if (args.from && args.to) {
    date1 = args.from;
    date2 = args.to;
    if (args['prev-from'] && args['prev-to']) {
      prev1 = args['prev-from'];
      prev2 = args['prev-to'];
    } else {
      ({ date1: prev1, date2: prev2 } = shiftPeriod(date1, date2));
    }
  } else {
    const period = args.period || '7d';
    const days = PERIOD_MAP[period];
    if (!days) throw new Error(`Unknown period '${period}'. Known: ${Object.keys(PERIOD_MAP).join(', ')}`);
    date2 = todayMinus(1); // yesterday
    date1 = todayMinus(days);
    ({ date1: prev1, date2: prev2 } = shiftPeriod(date1, date2));
  }

  const [cur, prev] = await Promise.all([
    fetchAggregates(cfg, counterId, date1, date2),
    fetchAggregates(cfg, counterId, prev1, prev2),
  ]);

  const metrics = [
    { key: 'visits', label: 'visits', kind: 'pct' },
    { key: 'pageviews', label: 'pageviews', kind: 'pct' },
    { key: 'users', label: 'users', kind: 'pct' },
    { key: 'bounce', label: 'bounce%', kind: 'pp', fmt: (v) => v.toFixed(1) },
    { key: 'avg_dur_sec', label: 'avg_dur_s', kind: 'pct', fmt: (v) => Math.round(v) },
  ];

  const rows = metrics.map((m) => ({
    metric: m.label,
    current: m.fmt ? m.fmt(cur[m.key]) : cur[m.key],
    previous: m.fmt ? m.fmt(prev[m.key]) : prev[m.key],
    delta: computeDelta(cur[m.key], prev[m.key], m.kind),
    period_current: `${date1}..${date2}`,
    period_previous: `${prev1}..${prev2}`,
  }));

  process.stdout.write(formatRows(
    {
      columns: [
        { key: 'metric', label: 'metric' },
        { key: 'current', label: 'current', align: 'right' },
        { key: 'previous', label: 'previous', align: 'right' },
        { key: 'delta', label: 'delta', align: 'right' },
      ],
      rows,
    },
    format
  ));

  if (format === 'table') {
    process.stdout.write(`\nperiods: current=${date1}..${date2}  previous=${prev1}..${prev2}\n`);
  }
}

// Only run main when invoked directly, not when imported by tests.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((e) => {
    console.error(e.message);
    process.exit(1);
  });
}
