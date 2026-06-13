import { spawnSync } from "node:child_process";

const checks = [
  ["Frontend ESLint", "lint:frontend"],
  ["Frontend Prettier", "format:check:frontend"],
  ["Frontend TypeScript", "typecheck:frontend"],
  ["Python Ruff lint", "lint:python"],
  ["Python Ruff format", "format:check:python"],
  ["Python Pyright", "typecheck:python"],
];

const strict = process.argv.includes("--strict");
const results = checks.map(([label, script]) => {
  console.log(`\n=== ${label} ===`);
  const result = spawnSync("npm", ["run", script], {
    shell: true,
    stdio: "inherit",
  });
  return { label, status: result.status ?? 1 };
});

console.log("\n=== Quality summary ===");
for (const result of results) {
  console.log(`${result.status === 0 ? "PASS" : "DEBT"} ${result.label}`);
}

const failures = results.filter((result) => result.status !== 0).length;
console.log(`Mode: ${strict ? "strict" : "baseline"}; checks with debt: ${failures}`);
process.exitCode = strict && failures > 0 ? 1 : 0;
