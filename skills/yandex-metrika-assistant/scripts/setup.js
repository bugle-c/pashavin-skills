#!/usr/bin/env node
import { mkdirSync, writeFileSync, chmodSync, existsSync, readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { homedir } from 'node:os';
import { createInterface } from 'node:readline/promises';
import { stdin as input, stdout as output } from 'node:process';

import { metrikaGet } from './lib/api.js';
import { configPath } from './lib/config.js';

async function main() {
  const rl = createInterface({ input, output });
  const path = configPath();

  console.log('=== Yandex.Metrika setup ===');
  console.log(`Config will be saved to: ${path}\n`);

  if (existsSync(path)) {
    const ans = await rl.question('Config already exists. Overwrite? [y/N]: ');
    if (!/^y/i.test(ans)) {
      console.log('Aborted.');
      rl.close();
      process.exit(0);
    }
  }

  console.log('1) If you do not have a token yet, see references/auth-and-token.md');
  console.log('   (https://oauth.yandex.ru/authorize?response_type=token&client_id=<YOUR_ID>)\n');
  const token = (await rl.question('Paste OAuth token: ')).trim();
  if (!token) {
    console.error('Empty token. Aborting.');
    rl.close();
    process.exit(1);
  }

  console.log('\nValidating token (fetching counters)...');
  let counters;
  try {
    const res = await metrikaGet('/management/v1/counters', { per_page: 100 }, { token });
    counters = res.counters || [];
  } catch (e) {
    console.error(`Failed: ${e.message}`);
    rl.close();
    process.exit(1);
  }

  if (counters.length === 0) {
    console.error('No counters found for this token.');
    rl.close();
    process.exit(1);
  }

  console.log(`\nFound ${counters.length} counter(s):`);
  counters.forEach((c, i) => {
    console.log(`  [${i + 1}] ${c.id} — ${c.name || '(no name)'} — ${c.site || ''}`);
  });

  const aliases = {};
  for (const c of counters) {
    const suggested = (c.site || c.name || `c${c.id}`)
      .replace(/^https?:\/\//, '')
      .replace(/\//g, '')
      .replace(/[^a-zA-Z0-9.-]/g, '-')
      .replace(/\.+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '')
      .toLowerCase()
      .slice(0, 30) || `c${c.id}`;
    const ans = (await rl.question(`Alias for counter ${c.id} [${suggested}]: `)).trim();
    aliases[ans || suggested] = c.id;
  }

  const aliasNames = Object.keys(aliases);
  console.log('\nChoose default counter:');
  aliasNames.forEach((a, i) => console.log(`  [${i + 1}] ${a}`));
  const defAns = (await rl.question(`Default [1-${aliasNames.length}]: `)).trim();
  const idx = Number(defAns);
  const def = aliasNames[(Number.isFinite(idx) && idx >= 1 && idx <= aliasNames.length) ? idx - 1 : 0];

  const cfg = { token, default_counter: def, counters: aliases };

  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, JSON.stringify(cfg, null, 2));
  chmodSync(path, 0o600);

  console.log(`\nSaved to ${path} (chmod 600).`);
  console.log(`Default counter: ${def}`);
  console.log('\nNext: try `node scripts/list-counters.js` or `node scripts/traffic-by-day.js --from 7daysAgo`');

  rl.close();
}

main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
