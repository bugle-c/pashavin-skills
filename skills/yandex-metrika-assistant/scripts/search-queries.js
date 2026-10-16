#!/usr/bin/env node
import { loadConfig, resolveCounter } from './lib/config.js';
import { metrikaGet } from './lib/api.js';
import { formatRows } from './lib/format.js';
import { parseArgs } from './lib/args.js';

const args = parseArgs(process.argv.slice(2));
const format = args.format || 'table';
const limit = Number(args.limit || 50);
const engine = args.engine || 'all'; // yandex | google | all

async function main() {
  const cfg = loadConfig();
  const counterId = resolveCounter(cfg, args.counter);
  const date1 = args.from || '30daysAgo';
  const date2 = args.to || 'yesterday';

  const params = {
    ids: counterId,
    metrics: ['ym:s:visits', 'ym:s:users', 'ym:s:bounceRate'],
    dimensions: 'ym:s:searchPhrase',
    date1,
    date2,
    sort: '-ym:s:visits',
    limit,
    accuracy: 'full',
  };
  if (engine === 'yandex') params.filters = "ym:s:lastSearchEngine=='yandex'";
  else if (engine === 'google') params.filters = "ym:s:lastSearchEngine=='google'";

  const res = await metrikaGet('/stat/v1/data', params, { token: cfg.token });

  const rows = (res.data || []).map((d) => ({
    query: d.dimensions[0]?.name || '(not set)',
    visits: d.metrics[0],
    users: d.metrics[1],
    bounce: d.metrics[2] !== null ? (d.metrics[2] / 100).toFixed(3) : '',
  }));

  process.stdout.write(formatRows(
    {
      columns: [
        { key: 'query', label: 'query' },
        { key: 'visits', label: 'visits', align: 'right' },
        { key: 'users', label: 'users', align: 'right' },
        { key: 'bounce', label: 'bounce', align: 'right' },
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
