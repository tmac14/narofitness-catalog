#!/usr/bin/env node
/**
 * Launcher for audit:page-import (human-friendly output + purge).
 */

import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const hostPagesDir = path.join(repoRoot, 'temp', 'audit', 'pages');
const REPORT_FORMATS = new Set(['json', 'md', 'both']);
const useColor = Boolean(process.stdout.isTTY && !process.env.NO_COLOR);

const c = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  dim: '\x1b[2m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
  gray: '\x1b[90m',
};

function paint(text, ...styles) {
  if (!useColor) return text;
  return `${styles.join('')}${text}${c.reset}`;
}

function line(text = '') {
  console.log(text);
}

function blank() {
  line();
}

function title(text) {
  blank();
  line(paint(`  ${text}`, c.bold, c.cyan));
  line(paint('  ' + '─'.repeat(Math.max(24, text.length)), c.dim));
}

function bullet(label, value, tone = '') {
  const left = paint(`  ${label.padEnd(14)}`, c.dim);
  const right = tone ? paint(String(value), tone) : String(value);
  line(`${left}${right}`);
}

function npmConfig(name) {
  const key = `npm_config_${name.replace(/-/g, '_').toLowerCase()}`;
  return process.env[key];
}

function hasFlag(args, ...names) {
  return names.some((name) => args.includes(name) || args.some((a) => a.startsWith(`${name}=`)));
}

function readFlagValue(args, flag) {
  const eq = args.find((a) => a.startsWith(`${flag}=`));
  if (eq) return eq.slice(flag.length + 1);
  const index = args.indexOf(flag);
  if (index >= 0 && index + 1 < args.length) return args[index + 1];
  return undefined;
}

function flagEnabled(args, flag) {
  if (hasFlag(args, flag)) return true;
  const value = npmConfig(flag.slice(2));
  return value === 'true' || value === '';
}

function pushFlag(out, args, flag, envName) {
  if (hasFlag(args, flag)) return;
  const value = npmConfig(envName ?? flag.slice(2));
  if (value === undefined) return;
  if (value === 'true' || value === '') {
    out.push(flag);
    return;
  }
  if (value === 'false') {
    out.push(`--no-${flag.slice(2)}`);
    return;
  }
  out.push(flag, value);
}

function normalizeArgv(raw) {
  const out = [];
  for (let i = 0; i < raw.length; i += 1) {
    const token = raw[i];
    if (token === '--purge-only') {
      out.push(token);
      continue;
    }
    if (token === '--purge') {
      out.push(token);
      continue;
    }
    if (token === '--format' || token === '--report-format') {
      out.push('--report-format', raw[i + 1] ?? 'both');
      i += 1;
      continue;
    }
    if (token.startsWith('--format=')) {
      out.push('--report-format', token.split('=').slice(1).join('='));
      continue;
    }
    if (token.startsWith('--report-format=')) {
      out.push('--report-format', token.split('=').slice(1).join('='));
      continue;
    }
    out.push(token);
  }
  return out;
}

function rebuildFromPositionals(raw) {
  if (raw.length === 0) return null;
  if (raw.some((a) => a.startsWith('-'))) return null;

  const rebuilt = [];
  let index = 0;

  if (/^\d+$/.test(raw[index] ?? '')) {
    rebuilt.push('--page', raw[index]);
    index += 1;
  }

  if (REPORT_FORMATS.has(raw[index] ?? '')) {
    rebuilt.push('--report-format', raw[index]);
    index += 1;
  }

  if (index === 0) return null;

  if (!hasFlag(rebuilt, '--ensure-pim-seed', '--no-ensure-pim-seed')) {
    const seed = npmConfig('ensure-pim-seed');
    if (seed === 'false') rebuilt.push('--no-ensure-pim-seed');
    else rebuilt.push('--ensure-pim-seed');
  }

  return rebuilt;
}

function buildLauncherArgs(argv) {
  let args = normalizeArgv(argv);
  const rebuilt = rebuildFromPositionals(args);
  if (rebuilt) args = rebuilt;

  const launcherFlags = [];
  if (flagEnabled(args, '--purge-only')) launcherFlags.push('--purge-only');
  if (flagEnabled(args, '--purge')) launcherFlags.push('--purge');

  const out = args.filter((a) => a !== '--purge-only' && a !== '--purge');

  pushFlag(out, args, '--page', 'page');
  pushFlag(out, args, '--from-page', 'from-page');
  pushFlag(out, args, '--to-page', 'to-page');
  pushFlag(out, args, '--pages', 'pages');
  pushFlag(out, args, '--pdf', 'pdf');
  pushFlag(out, args, '--output-base', 'output-base');

  if (!hasFlag(out, '--report-format', '--format')) {
    const fmt = npmConfig('report-format') ?? npmConfig('format');
    if (fmt) out.push('--report-format', fmt);
  }

  if (!hasFlag(out, '--ensure-pim-seed', '--no-ensure-pim-seed')) {
    const seed = npmConfig('ensure-pim-seed');
    if (seed === 'false') out.push('--no-ensure-pim-seed');
    else if (seed === 'true' || seed === '') out.push('--ensure-pim-seed');
  }

  if (!hasFlag(out, '--no-confirm')) {
    const noConfirm = npmConfig('no-confirm');
    if (noConfirm === 'true' || noConfirm === '') out.push('--no-confirm');
  }

  if (!hasFlag(out, '--allow-needs-review')) {
    const allow = npmConfig('allow-needs-review');
    if (allow === 'true' || allow === '') out.push('--allow-needs-review');
  }

  if (!hasFlag(out, '--cumulative')) {
    const cumulative = npmConfig('cumulative');
    if (cumulative === 'true' || cumulative === '') out.push('--cumulative');
  }

  if (!hasFlag(out, '--continue-on-fail')) {
    const cont = npmConfig('continue-on-fail');
    if (cont === 'true' || cont === '') out.push('--continue-on-fail');
  }

  return { cliArgs: out, launcherFlags };
}

function extractAuditedPages(cliArgs) {
  const pages = new Set();
  const single = readFlagValue(cliArgs, '--page');
  if (single && /^\d+$/.test(single)) pages.add(Number(single));

  const list = readFlagValue(cliArgs, '--pages');
  if (list) {
    for (const token of list.split(',')) {
      const n = Number(token.trim());
      if (Number.isInteger(n) && n > 0) pages.add(n);
    }
  }

  const fromPage = readFlagValue(cliArgs, '--from-page');
  const toPage = readFlagValue(cliArgs, '--to-page');
  if (fromPage && toPage) {
    const from = Number(fromPage);
    const to = Number(toPage);
    if (Number.isInteger(from) && Number.isInteger(to) && from > 0 && to >= from) {
      for (let page = from; page <= to; page += 1) pages.add(page);
    }
  }

  return [...pages].sort((a, b) => a - b);
}

function listHostAuditDirs() {
  if (!fs.existsSync(hostPagesDir)) return [];
  return fs
    .readdirSync(hostPagesDir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name);
}

function removeHostAuditDirs(dirs) {
  let removed = 0;
  for (const dir of dirs) {
    fs.rmSync(path.join(hostPagesDir, dir), { recursive: true, force: true });
    removed += 1;
  }
  return removed;
}

function listContainerAuditDirs() {
  const result = spawnSync(
    'docker',
    ['compose', 'exec', '-T', 'api', 'ls', '-1', '/data/audit/pages'],
    { cwd: repoRoot, encoding: 'utf8', shell: false },
  );
  if (result.status !== 0) return [];
  return result.stdout
    .split(/\r?\n/)
    .map((s) => s.trim())
    .filter((s) => /^\d{3}$/.test(s));
}

function removeContainerAuditDirs(dirs) {
  let removed = 0;
  for (const dir of dirs) {
    const result = spawnSync(
      'docker',
      ['compose', 'exec', '-T', 'api', 'rm', '-rf', `/data/audit/pages/${dir}`],
      { cwd: repoRoot, stdio: 'pipe', shell: false },
    );
    if (result.status === 0) removed += 1;
  }
  return removed;
}

function purgeAuditPages({ keepPages = [] } = {}) {
  const keep = new Set(keepPages.map((p) => String(p).padStart(3, '0')));

  const hostDirs = listHostAuditDirs().filter((d) => !keep.has(d));
  const containerDirs = listContainerAuditDirs().filter((d) => !keep.has(d));

  const hostRemoved = removeHostAuditDirs(hostDirs);
  const containerRemoved = removeContainerAuditDirs(containerDirs);

  return { hostRemoved, containerRemoved, hostDirs, containerDirs };
}

function runDockerAudit(cliArgs) {
  const dockerArgs = [
    'compose',
    'exec',
    '-T',
    '-e',
    'PYTHONPATH=/app',
    'api',
    'python',
    'scripts/audit_page_import.py',
    '--quiet',
    ...cliArgs,
  ];

  const result = spawnSync('docker', dockerArgs, {
    cwd: repoRoot,
    encoding: 'utf8',
    shell: true,
  });

  if (result.status !== 0) {
    if (result.stderr) process.stderr.write(result.stderr);
    if (result.stdout) process.stdout.write(result.stdout);
    return { status: result.status ?? 1, summary: null };
  }

  const summaryLine = (result.stdout || '')
    .split(/\r?\n/)
    .find((row) => row.startsWith('AUDIT_SUMMARY='));

  if (!summaryLine) {
    return { status: 1, summary: null, error: 'Missing AUDIT_SUMMARY from audit runner' };
  }

  try {
    const summary = JSON.parse(summaryLine.slice('AUDIT_SUMMARY='.length));
    return { status: 0, summary };
  } catch {
    return { status: 1, summary: null, error: 'Invalid AUDIT_SUMMARY JSON' };
  }
}

function syncReports(auditedPages) {
  fs.mkdirSync(hostPagesDir, { recursive: true });
  for (const page of auditedPages) {
    const padded = String(page).padStart(3, '0');
    const hostPageDir = path.join(hostPagesDir, padded);
    fs.mkdirSync(hostPageDir, { recursive: true });

    const result = spawnSync(
      'docker',
      ['compose', 'cp', `api:/data/audit/pages/${padded}/.`, hostPageDir],
      { cwd: repoRoot, stdio: 'pipe', shell: true },
    );

    if (result.status !== 0) {
      throw new Error(`No se pudo sincronizar temp/audit/pages/${padded}`);
    }
  }
}

function statusTone(status) {
  if (status === 'pass') return c.green;
  if (status === 'fail') return c.red;
  return c.yellow;
}

function printPageSummary(pageResult) {
  const label = `Página ${pageResult.page}`;
  title(`Auditoría import · ${label}`);

  bullet('Estado', pageResult.status.toUpperCase(), statusTone(pageResult.status));
  bullet('Parseadas', `${pageResult.parsed} filas (PDF: ${pageResult.pdf_rows_total ?? '?'})`);
  bullet('Importadas', pageResult.imported, pageResult.imported > 0 ? c.green : '');
  bullet('Bloqueadas', pageResult.blocked, pageResult.blocked > 0 ? c.yellow : '');
  bullet('En app', `${pageResult.visible_in_app} productos`);
  bullet('DB aislada', pageResult.isolated ? 'sí' : 'no', pageResult.isolated ? c.green : c.red);
  bullet('Confirm', pageResult.confirm_executed ? 'ejecutado' : 'no');

  if (pageResult.fail_reasons?.length) {
    blank();
    line(paint('  Motivos de fallo', c.red, c.bold));
    for (const reason of pageResult.fail_reasons) {
      line(paint(`    · ${reason}`, c.red));
    }
  }

  blank();
  line(paint('  Reportes', c.bold));
  line(`    ${pageResult.output_dir}/`);

  if (pageResult.status === 'pass') {
    blank();
    line(paint('  Siguiente paso', c.bold));
    line(`    Abre Products en la app → deberías ver ${pageResult.visible_in_app} productos.`);
    line(paint('    Da OK manual antes de auditar la siguiente página.', c.dim));
  } else {
    blank();
    line(paint('  Siguiente paso', c.bold));
    line('    Corrige el problema, purga si hace falta y vuelve a auditar esta misma página.');
  }
}

function printPurgeSummary(result, { titleText }) {
  title(titleText);
  if (result.hostRemoved === 0 && result.containerRemoved === 0) {
    bullet('Resultado', 'no había auditorías que eliminar', c.dim);
    return;
  }
  bullet('Host', `${result.hostRemoved} carpeta(s) eliminada(s)`);
  bullet('Contenedor', `${result.containerRemoved} carpeta(s) eliminada(s)`);
  if (result.hostDirs.length) {
    line(paint(`    ${result.hostDirs.join(', ')}`, c.dim));
  }
}

function runPurgeOnly() {
  title('Purge auditorías');
  const result = purgeAuditPages();
  printPurgeSummary(result, { titleText: 'Purge completado' });
  blank();
  line(paint('  Listo.', c.green));
  blank();
}

function main() {
  const { cliArgs, launcherFlags } = buildLauncherArgs(process.argv.slice(2));
  const purgeOnly = launcherFlags.includes('--purge-only');
  const purgeBeforeRun = launcherFlags.includes('--purge');

  if (purgeOnly) {
    runPurgeOnly();
    process.exit(0);
  }

  if (
    !hasFlag(cliArgs, '--page') &&
    !hasFlag(cliArgs, '--from-page') &&
    !hasFlag(cliArgs, '--pages')
  ) {
    line(paint('Falta indicar la página.', c.red));
    line(paint('  npm run audit:page-import --page=3 --report-format=both --ensure-pim-seed', c.cyan));
    line(paint('  npm run audit:page-import --page=3 --purge', c.cyan));
    process.exit(2);
  }

  const auditedPages = extractAuditedPages(cliArgs);

  if (purgeBeforeRun) {
    title('Preparación');
    const result = purgeAuditPages();
    printPurgeSummary(result, { titleText: 'Purge previo' });
    blank();
  }

  const { status, summary, error } = runDockerAudit(cliArgs);
  if (status !== 0 || !summary) {
    title('Error');
    line(paint(`  ${error ?? 'La auditoría falló.'}`, c.red));
    blank();
    process.exit(status || 1);
  }

  try {
    syncReports(auditedPages);
  } catch (err) {
    title('Error');
    line(paint(`  ${err.message}`, c.red));
    blank();
    process.exit(1);
  }

  for (const pageResult of summary.pages) {
    printPageSummary(pageResult);
  }

  if (summary.any_failed || summary.stopped_early) {
    blank();
    process.exit(1);
  }

  blank();
}

main();
