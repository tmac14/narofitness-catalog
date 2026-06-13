#!/usr/bin/env node
/**
 * Valida sincronización entre package.json y scripts/commands.catalog.json
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const catalogPath = path.join(repoRoot, 'scripts', 'commands.catalog.json');
const packagePath = path.join(repoRoot, 'package.json');

const EXCLUDED_SCRIPTS = new Set(['help', 'help:validate', 'help:list']);

function fail(messages) {
  for (const msg of messages) {
    console.error(`ERROR: ${msg}`);
  }
  process.exit(1);
}

function loadJson(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (err) {
    fail([`No se pudo leer ${filePath}: ${err.message}`]);
  }
}

function collectCatalogRootNames(catalog) {
  const names = [];
  for (const section of catalog.sections ?? []) {
    for (const cmd of section.commands ?? []) {
      names.push(cmd.name);
    }
  }
  return names;
}

function main() {
  const catalog = loadJson(catalogPath);
  const pkg = loadJson(packagePath);
  const packageScripts = Object.keys(pkg.scripts ?? {});
  const catalogNames = collectCatalogRootNames(catalog);
  const errors = [];

  const catalogSet = new Set(catalogNames);
  const packageSet = new Set(packageScripts);

  for (const name of catalogNames) {
    if (!name || typeof name !== 'string') {
      errors.push('Entrada de catálogo sin name válido.');
      continue;
    }
    const section = catalog.sections.find((s) => s.commands?.some((cmd) => cmd.name === name));
    const cmd = section?.commands?.find((c) => c.name === name);
    if (!cmd?.description) {
      errors.push(`Comando "${name}" sin description.`);
    }
  }

  const duplicateCatalog = catalogNames.filter((n, i) => catalogNames.indexOf(n) !== i);
  if (duplicateCatalog.length) {
    errors.push(`Nombres duplicados en catálogo: ${[...new Set(duplicateCatalog)].join(', ')}`);
  }

  const quickFlowCommands = (catalog.quickFlows ?? [])
    .flatMap((f) => (f.commands ? f.commands : f.command ? [f.command] : []))
    .filter((c) => !c.includes('→'));
  const duplicateQuick = quickFlowCommands.filter((n, i) => quickFlowCommands.indexOf(n) !== i);
  if (duplicateQuick.length) {
    errors.push(`quickFlows duplicados: ${[...new Set(duplicateQuick)].join(', ')}`);
  }

  for (const script of packageScripts) {
    if (EXCLUDED_SCRIPTS.has(script)) continue;
    if (!catalogSet.has(script)) {
      errors.push(`Script "${script}" en package.json no documentado en catálogo.`);
    }
  }

  for (const name of catalogNames) {
    if (!packageSet.has(name)) {
      errors.push(`Entrada de catálogo "${name}" no existe en package.json.`);
    }
  }

  if (errors.length) {
    fail(errors);
  }

  console.log(`OK: catálogo sincronizado (${catalogNames.length} comandos raíz).`);
}

main();
