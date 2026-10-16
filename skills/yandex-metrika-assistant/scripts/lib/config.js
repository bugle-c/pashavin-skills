import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { homedir } from 'node:os';

const CONFIG_PATH = () => join(process.env.HOME || homedir(), '.config', 'yandex-metrika', 'config.json');

export function loadConfig() {
  let fromFile = null;
  const path = CONFIG_PATH();
  if (existsSync(path)) {
    try {
      fromFile = JSON.parse(readFileSync(path, 'utf8'));
    } catch (e) {
      throw new Error(`Failed to parse ${path}: ${e.message}`);
    }
  }

  const envToken = process.env.YANDEX_METRIKA_OAUTH_TOKEN;
  const token = envToken || fromFile?.token || null;

  if (!token) {
    throw new Error(
      `No token found. Run: node ${join(process.env.HOME || homedir(), '.claude/skills/yandex-metrika-assistant/scripts/setup.js')}`
    );
  }

  return {
    token,
    counters: fromFile?.counters || {},
    default_counter: fromFile?.default_counter || null,
  };
}

export function resolveCounter(cfg, flagValue) {
  if (flagValue === undefined || flagValue === null) {
    if (!cfg.default_counter) {
      throw new Error(
        'No counter specified and no default_counter in config. ' +
        'Pass --counter <alias|id> or run setup.js to set a default.'
      );
    }
    flagValue = cfg.default_counter;
  }

  if (/^\d+$/.test(String(flagValue))) {
    return Number(flagValue);
  }

  if (cfg.counters[flagValue] !== undefined) {
    return cfg.counters[flagValue];
  }

  const known = Object.keys(cfg.counters).join(', ') || '(none configured)';
  throw new Error(`Unknown counter '${flagValue}'. Known aliases: ${known}`);
}

export function configPath() {
  return CONFIG_PATH();
}
