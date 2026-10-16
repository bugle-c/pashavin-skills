export function formatRows({ columns, rows }, format) {
  switch (format) {
    case 'json':
      return JSON.stringify(rows);
    case 'tsv':
      return formatTsv(columns, rows);
    case 'table':
      return formatTable(columns, rows);
    default:
      throw new Error(`Unknown format: ${format}. Use one of: table, json, tsv`);
  }
}

function formatTsv(columns, rows) {
  const header = columns.map((c) => c.label).join('\t');
  const body = rows
    .map((r) => columns.map((c) => stringify(r[c.key])).join('\t'))
    .join('\n');
  return body ? `${header}\n${body}\n` : `${header}\n`;
}

function formatTable(columns, rows) {
  const widths = columns.map((c) =>
    Math.max(
      String(c.label).length,
      ...rows.map((r) => stringify(r[c.key]).length)
    )
  );

  const renderRow = (cells) =>
    cells
      .map((cell, i) => {
        const w = widths[i];
        return columns[i].align === 'right' ? cell.padStart(w) : cell.padEnd(w);
      })
      .join('  ');

  const header = renderRow(columns.map((c) => c.label));
  const sep = widths.map((w) => '-'.repeat(w)).join('  ');
  const body = rows.map((r) => renderRow(columns.map((c) => stringify(r[c.key]))));
  return [header, sep, ...body].join('\n') + '\n';
}

function stringify(v) {
  if (v === null || v === undefined) return '';
  return String(v);
}
