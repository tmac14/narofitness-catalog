/**
 * Production runtime: start embedded PostgreSQL + catalog-api.exe
 */
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const http = require("http");

const API_PORT = 8000;
const PG_PORT = 5434;

function waitForHealth(url, attempts = 60) {
  return new Promise((resolve, reject) => {
    let n = 0;
    const tick = () => {
      http
        .get(`${url}/api/v1/health`, (res) => {
          if (res.statusCode === 200) resolve();
          else retry();
        })
        .on("error", retry);
    };
    const retry = () => {
      if (++n >= attempts) reject(new Error("API health timeout"));
      else setTimeout(tick, 500);
    };
    tick();
  });
}

function pgBin(resourcesPath, name) {
  const win = path.join(resourcesPath, "postgres", "bin", `${name}.exe`);
  if (fs.existsSync(win)) return win;
  return name;
}

async function startRuntime(app) {
  const userData = app.getPath("userData");
  const dataDir = path.join(userData, "data");
  const pgData = path.join(userData, "pg", "data");
  const logsDir = path.join(userData, "logs");
  fs.mkdirSync(dataDir, { recursive: true });
  fs.mkdirSync(logsDir, { recursive: true });

  const resources = process.resourcesPath;
  const engineExe = path.join(resources, "engine", "catalog-api.exe");
  const initdb = pgBin(resources, "initdb");
  const pgctl = pgBin(resources, "pg_ctl");
  const createdb = pgBin(resources, "createdb");

  const pgBinDir = path.join(resources, "postgres", "bin");
  const pgLibDir = path.join(resources, "postgres", "lib");
  const hasPg = fs.existsSync(path.join(pgBinDir, "initdb.exe"));
  const pgPath = hasPg
    ? `${pgBinDir};${fs.existsSync(pgLibDir) ? pgLibDir + ";" : ""}${process.env.PATH || ""}`
    : process.env.PATH;

  if (hasPg && !fs.existsSync(path.join(pgData, "PG_VERSION"))) {
    fs.mkdirSync(path.dirname(pgData), { recursive: true });
    await new Promise((res, rej) => {
      const p = spawn(initdb, ["-D", pgData, "-U", "narocatalog", "-A", "trust", "-E", "UTF8"], {
        env: { ...process.env, PATH: pgPath },
        stdio: "inherit",
      });
      p.on("exit", (c) => (c === 0 ? res() : rej(new Error(`initdb exit ${c}`))));
    });
  }

  if (hasPg) {
    const logFile = path.join(logsDir, "postgresql.log");
    spawn(pgctl, ["-D", pgData, "-l", logFile, "-o", `-p ${PG_PORT}`, "start"], {
      env: { ...process.env, PATH: pgPath },
      shell: true,
    });
    await new Promise((r) => setTimeout(r, 2000));
    if (
      fs.existsSync(createdb + (createdb.endsWith(".exe") ? "" : ".exe")) ||
      createdb.endsWith(".exe")
    ) {
      spawn(
        createdb,
        ["-h", "127.0.0.1", "-p", String(PG_PORT), "-U", "narocatalog", "narocatalog"],
        {
          env: { ...process.env, PATH: pgPath },
        },
      );
    }
  }

  const dbUrl = `postgresql+asyncpg://narocatalog@127.0.0.1:${PG_PORT}/narocatalog`;
  const env = {
    ...process.env,
    DATA_DIR: dataDir,
    DATABASE_URL: dbUrl,
    NAROCATALOG_RUNTIME: "1",
  };

  let apiProc = null;
  if (fs.existsSync(engineExe)) {
    apiProc = spawn(engineExe, [], {
      env,
      cwd: path.dirname(engineExe),
      stdio: ["ignore", "pipe", "pipe"],
    });
    const log = fs.createWriteStream(path.join(logsDir, "api.log"), { flags: "a" });
    apiProc.stdout.pipe(log);
    apiProc.stderr.pipe(log);
  }

  const apiBase = `http://127.0.0.1:${API_PORT}`;
  if (apiProc) {
    await waitForHealth(apiBase);
  }

  const shutdown = () => {
    if (apiProc) apiProc.kill();
    if (hasPg && pgctl) {
      spawn(pgctl, ["-D", pgData, "stop"], { shell: true, env: { ...process.env, PATH: pgPath } });
    }
  };

  return { apiBase, shutdown, dataDir };
}

module.exports = { startRuntime, API_PORT };
