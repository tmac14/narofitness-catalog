#!/usr/bin/env node
/**
 * npm run help — referencia CLI de comandos NaroCatalog.
 * Fuente: docs/control/commands.catalog.json + package.json
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const catalogPath = path.join(repoRoot, 'docs', 'control', 'commands.catalog.json');
const packagePath = path.join(repoRoot, 'package.json');

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

function loadCatalog() {
  return JSON.parse(fs.readFileSync(catalogPath, 'utf8'));
}

function loadPackageScripts() {
  const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
  return pkg.scripts ?? {};
}

function collectRootCommands(catalog) {
  const map = new Map();
  for (const section of catalog.sections ?? []) {
    for (const cmd of section.commands ?? []) {
      map.set(cmd.name, { ...cmd, section });
    }
  }
  return map;
}

function collectDesktopCommands(catalog) {
  const map = new Map();
  for (const cmd of catalog.desktopCommands ?? []) {
    map.set(cmd.name, cmd);
  }
  return map;
}

function allCommandNames(catalog) {
  const root = collectRootCommands(catalog);
  const desktop = collectDesktopCommands(catalog);
  return [...root.keys(), ...desktop.keys()].sort();
}

function suggestCommands(query, catalog) {
  const q = query.toLowerCase();
  return allCommandNames(catalog).filter((name) => name.toLowerCase().includes(q));
}

function formatFlags(flags) {
  if (!flags?.length) return null;
  return flags
    .map((flag) => {
      const defaultPart = flag.default ? ` (default ${flag.default})` : '';
      return `${flag.name}${defaultPart}${flag.description ? ` — ${flag.description}` : ''}`;
    })
    .join('\n               ');
}

function printOverview(catalog) {
  title('NaroCatalog — comandos npm');
  line(paint('  npm run help -- <comando>   detalle de un comando', c.dim));
  line(paint('  npm run help -- list        lista plana (o npm run help:list)', c.dim));
  line(paint('  Documentación: COMMANDS.md', c.dim));

  title('Flujos rápidos');
  for (const flow of catalog.quickFlows ?? []) {
    const cmdText = flow.commands
      ? flow.commands.map((n) => paint(`npm run ${n}`, c.cyan)).join(paint(' → ', c.dim))
      : paint(`npm run ${flow.command}`, c.cyan);
    line(`  ${paint(flow.goal.padEnd(28), c.dim)} ${cmdText}`);
  }

  if (catalog.localUrls) {
    blank();
    line(
      paint(
        `  URLs: API ${catalog.localUrls.api} · UI ${catalog.localUrls.ui} · Postgres :${catalog.localUrls.postgresHostPort}`,
        c.dim,
      ),
    );
  }

  for (const section of catalog.sections ?? []) {
    title(section.title);
    for (const note of section.notes ?? []) {
      line(paint(`  · ${note}`, c.yellow));
    }
    for (const cmd of section.commands ?? []) {
      line(`  ${paint(cmd.name.padEnd(28), c.cyan)} ${cmd.description}`);
    }
  }

  if (catalog.desktopCommands?.length) {
    title('Desktop (apps/desktop)');
    line(paint('  Invocar con --prefix apps/desktop o vía delegados desktop:* / frontend:*', c.dim));
    for (const cmd of catalog.desktopCommands) {
      line(`  ${paint(cmd.name.padEnd(28), c.cyan)} ${cmd.description}`);
    }
  }
}

function printList(catalog) {
  for (const name of allCommandNames(catalog)) {
    line(name);
  }
}

function printRootDetail(name, entry, scripts) {
  const { section, ...cmd } = entry;
  title(`Comando: ${name}`);
  bullet('Categoría', section.title);
  bullet('Descripción', cmd.description);
  if (cmd.profile) bullet('Perfil', cmd.profile);
  if (cmd.requires?.length) bullet('Requisitos', cmd.requires.join('; '));
  bullet('Invocación', `npm run ${name}`);
  if (scripts[name]) bullet('Script', scripts[name]);
  if (cmd.underlyingScript) bullet('Subyacente', cmd.underlyingScript);
  const flagsText = formatFlags(cmd.flags);
  if (flagsText) bullet('Flags', flagsText);
  if (cmd.examples?.length) bullet('Ejemplos', cmd.examples.join('\n               '));
  if (cmd.related?.length) bullet('Relacionados', cmd.related.join(', '));
  blank();
}

function printDesktopDetail(name, cmd) {
  title(`Comando desktop: ${name}`);
  bullet('Paquete', cmd.prefix);
  bullet('Descripción', cmd.description);
  bullet('Invocación', `npm run ${name} --prefix ${cmd.prefix}`);
  blank();
}

function printDetail(name, catalog, scripts) {
  const root = collectRootCommands(catalog);
  const desktop = collectDesktopCommands(catalog);

  if (root.has(name)) {
    printRootDetail(name, root.get(name), scripts);
    return 0;
  }
  if (desktop.has(name)) {
    printDesktopDetail(name, desktop.get(name));
    return 0;
  }

  title('Comando no encontrado');
  line(paint(`  No hay documentación para "${name}".`, c.red));
  const suggestions = suggestCommands(name, catalog);
  if (suggestions.length) {
    blank();
    line(paint('  ¿Quisiste decir?', c.yellow));
    for (const s of suggestions.slice(0, 8)) {
      line(`    ${paint(s, c.cyan)}`);
    }
  }
  blank();
  line(paint('  Ver índice: npm run help', c.dim));
  blank();
  return 1;
}

function main() {
  const args = process.argv.slice(2);

  let catalog;
  try {
    catalog = loadCatalog();
  } catch (err) {
    line(paint(`ERROR: no se pudo leer ${catalogPath}: ${err.message}`, c.red));
    process.exit(2);
  }

  const scripts = loadPackageScripts();

  if (args.includes('--list') || args.includes('list')) {
    printList(catalog);
    return;
  }

  const commandArg = args.find((a) => !a.startsWith('-'));
  if (!commandArg) {
    printOverview(catalog);
    return;
  }

  process.exitCode = printDetail(commandArg, catalog, scripts);
}

main();
