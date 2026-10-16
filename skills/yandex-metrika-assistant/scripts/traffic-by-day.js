#!/usr/bin/env node
import { loadConfig, resolveCounter } from './lib/config.js';
import { metrikaGet } from './lib/api.js';
import { formatRows } from './lib/format.js';
import { parseArgs } from './lib/args.js';

const args = parseArgs(process.argv.slice(2));
const format = args.format || 'table';

async function main() {
  const cfg = loadConfig();
  const counterId = resolveCounter(cfg, args.counter);
  const date1 = args.from || '7daysAgo';
  const date2 = args.to || 'yesterday';

  const res = await metrikaGet('/stat/v1/data', {
    ids: counterId,
    metrics: ['ym:s:visits', 'ym:s:pageviews', 'ym:s:users', 'ym:s:bounceRate', 'ym:s:avgVisitDurationSeconds'],
    dimensions: 'ym:s:date',
    date1,
    date2,
    sort: 'ym:s:date',
    limit: 365,
    accuracy: 'full',
  }, { token: cfg.token });

  const rows = (res.data || []).map((d) => ({
    date: d.dimensions[0].name,
    visits: d.metrics[0],
    pageviews: d.metrics[1],
    users: d.metrics[2],
    bounce: d.metrics[3] !== null ? (d.metrics[3] / 100).toFixed(3) : '',
    avg_dur_sec: d.metrics[4] !== null ? Math.round(d.metrics[4]) : '',
  }));

  // Total row
  const sum = (k) => rows.reduce((a, r) => a + (Number(r[k]) || 0), 0);
  if (rows.length > 0) {
    rows.push({
      date: 'TOTAL',
      visits: sum('visits'),
      pageviews: sum('pageviews'),
      users: sum('users'),
      bounce: '',
      avg_dur_sec: '',
    });
  }

  process.stdout.write(formatRows(
    {
      columns: [
        { key: 'date', label: 'date' },
        { key: 'visits', label: 'visits', align: 'right' },
        { key: 'pageviews', label: 'pageviews', align: 'right' },
        { key: 'users', label: 'users', align: 'right' },
        { key: 'bounce', label: 'bounce', align: 'right' },
        { key: 'avg_dur_sec', label: 'avg_dur_s', align: 'right' },
      ],
      rows,
    },
    format
  ));
}

main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
