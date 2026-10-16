#!/usr/bin/env node
import { loadConfig, resolveCounter } from './lib/config.js';
import { metrikaGet } from './lib/api.js';
import { formatRows } from './lib/format.js';
import { parseArgs } from './lib/args.js';

const args = parseArgs(process.argv.slice(2));
const format = args.format || 'table';
const limit = Number(args.limit || 20);

async function main() {
  const cfg = loadConfig();
  const counterId = resolveCounter(cfg, args.counter);
  const date1 = args.from || '30daysAgo';
  const date2 = args.to || 'yesterday';

  const dimensions = args.utm
    ? ['ym:s:trafficSource', 'ym:s:UTMSource', 'ym:s:UTMMedium', 'ym:s:UTMCampaign']
    : ['ym:s:trafficSource'];

  const res = await metrikaGet('/stat/v1/data', {
    ids: counterId,
    metrics: ['ym:s:visits', 'ym:s:users', 'ym:s:bounceRate'],
    dimensions: dimensions.join(','),
    date1,
    date2,
    sort: '-ym:s:visits',
    limit,
    accuracy: 'full',
  }, { token: cfg.token });

  const rows = (res.data || []).map((d) => {
    const row = {
      source: d.dimensions[0]?.name || '',
      visits: d.metrics[0],
      users: d.metrics[1],
      bounce: d.metrics[2] !== null ? (d.metrics[2] / 100).toFixed(3) : '',
    };
    if (args.utm) {
      row.utm_source = d.dimensions[1]?.name || '';
      row.utm_medium = d.dimensions[2]?.name || '';
      row.utm_campaign = d.dimensions[3]?.name || '';
    }
    return row;
  });

  const columns = [
    { key: 'source', label: 'source' },
    { key: 'visits', label: 'visits', align: 'right' },
    { key: 'users', label: 'users', align: 'right' },
    { key: 'bounce', label: 'bounce', align: 'right' },
  ];
  if (args.utm) {
    columns.push(
      { key: 'utm_source', label: 'utm_source' },
      { key: 'utm_medium', label: 'utm_medium' },
      { key: 'utm_campaign', label: 'utm_campaign' }
    );
  }

  process.stdout.write(formatRows({ columns, rows }, format));
}

main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
