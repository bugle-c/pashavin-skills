#!/usr/bin/env node
import { loadConfig } from './lib/config.js';
import { metrikaGet } from './lib/api.js';
import { formatRows } from './lib/format.js';
import { parseArgs } from './lib/args.js';

const args = parseArgs(process.argv.slice(2));
const format = args.format || 'table';

async function main() {
  const cfg = loadConfig();
  const res = await metrikaGet('/management/v1/counters', { per_page: 100 }, { token: cfg.token });
  const rows = (res.counters || []).map((c) => ({
    id: c.id,
    name: c.name || '',
    site: c.site || '',
    status: c.status || '',
  }));
  process.stdout.write(formatRows(
    {
      columns: [
        { key: 'id', label: 'id', align: 'right' },
        { key: 'name', label: 'name' },
        { key: 'site', label: 'site' },
        { key: 'status', label: 'status' },
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
