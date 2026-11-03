# Runnable commands

Every script, console entry point and CLI in this repository, grouped by what you are trying to do.
All commands run from the repository root. `uv run` uses the project venv; `npm` commands need
`npm install` once (Node 20+).

Keys: commands marked **needs keys** read `OPENAI_API_KEY` (and, for the Worldview agents, the
plugin's MCP keys such as `VECTOR_DB_TOOL_KEY`) from `.env` or the shell. Everything else is
offline.

## Setup

| Command | What it does |
|---|---|
| `uv sync` | Installs the library, both demos (Worldview, MapLibre), the benchmark utility and the dev tools into one venv. |
| `npm install` | Installs the `@geoui/react-adapter` SDK and the MapLibre demo app (npm workspaces). |
| `git submodule update --init` | Fetches the `worldview-assistant` plugin (skill + MCP list) the Worldview agents need. |
| `uv run pre-commit install` | Optional. Installs the git hook from `.pre-commit-config.yaml` (whitespace/EOF fixers, YAML/TOML checks, ruff). |
| `npx playwright install chromium` | One-time, ~150 MB. Done automatically by `demo/chromium.sh` on first use. |

## Checks (offline, no keys)

| Command | What it does |
|---|---|
| `uv run pytest` | The whole Python suite: library, both demos, benchmark utility and app tests. |
| `uv run pytest -m "not integration"` | Same, minus the tests that spawn a subprocess (the stdio MCP smoke tests). |
| `uv run pytest -m agents` | Only the agent tests: plugin loader, toolset parity and the model-visible surface golden. |
| `uv run pytest demo/worldview/tests` | One project's tests; any `testpaths` entry in `pyproject.toml` works the same way. |
| `uv run ruff check . && uv run ruff format --check .` | Lint and formatting for Python. |
| `uv run python scripts/export_schemas.py --check` | Exit 1 and list files if `schemas/` no longer matches the pydantic models. |
| `npm test` | SDK unit tests (vitest + jsdom), including the generated-types drift check. `npm test -w @geoui/react-adapter` targets the SDK alone. |
| `npm run typecheck -w @geoui/react-adapter` | `tsc --noEmit` for the SDK. |
| `npm run lint` | eslint over the SDK and the MapLibre app. |
| `npm run build` | Builds every workspace: the SDK (`tsc`) and the MapLibre app (`tsc` + `vite build`). |
| `uv run pre-commit run --all-files` | Runs the hook set over the whole tree. Note: `end-of-file-fixer` will touch the frozen files under `benchmarks/*/results/`; don't commit those. |

## Generated files (run after a model or schema change)

| Command | What it does |
|---|---|
| `uv run python scripts/export_schemas.py` | Rewrites `schemas/`: `geo_intent.json`, one `ext/<name>/v<version>/schema.json` per extension (its `$id` is the extension URI) and `index.html`. A published version never changes; bump the extension's `VERSION` instead. |
| `npm run gen:types` | Regenerates `sdk/geoui-react-adapter/src/generated/` (TypeScript types and the embedded extension specs) from `schemas/`. Run it after `export_schemas.py`. |
| `uv run python scripts/dump_mcp_contract.py local` | Prints the Worldview MCP's tool contract (names, schemas, descriptions) as JSON, in-process. Also takes an `http(s)://…/mcp` URL or a server `.py` path (stdio); `--only <prefix>` filters tools; `--update-golden` rewrites `demo/worldview/tests/mcp/fixtures/akd_contract.json`; `MCP_BEARER_TOKEN` is sent to remote targets. |
| `uv run python scripts/capture_agent_surface.py` | Rewrites `demo/worldview/tests/agents/fixtures/agent_surface.json`, the golden of everything the model sees (prompts, tool lists, descriptions). Only when such a change is intentional; review the diff. |

## Running the MapLibre demo (SDK + CDP bridge)

| Command | What it does |
|---|---|
| `npm run dev` | Serves the MapLibre app at http://127.0.0.1:5173 (Vite, strict port). `npm run preview` serves the built app on the same port. |
| `source demo/chromium.sh && ensure_chromium` | Launches, or reattaches to, a Chromium with remote debugging on `:9222` and exports `PLAYWRIGHT_CDP_ENDPOINT`. Env: `CHROME_BIN`, `CDP_PORT`, `WORLDVIEW_CHROMIUM_PROFILE`, `PLAYWRIGHT_BROWSERS_PATH`. Stop it with `pkill -f "remote-debugging-port=9222"`. |
| `uv run maplibre-mcp` | The GeoUI MCP server for any `window.geoui` page, over stdio, for Claude Code or another host. `--transport http\|sse --host H --port P` (default port 8001) for a network server. Env: `GEOUI_APP_URL` (the page's origin; it finds the tab or opens one), `PLAYWRIGHT_CDP_ENDPOINT` (default `http://localhost:9222`). |
| `uv run python -m maplibre.agents.maplibre_agent "Show MODIS Aqua AOD over California on 2025-09-15"` | **needs keys.** One agent turn with the three GeoUI tools against the running app. The argument is the query; omitted, a default is used. |
| `AGENT=maplibre demo/start.sh` | **needs keys.** Starts Chromium, checks the app is up at `GEOUI_APP_URL`, then opens the multi-turn chat notebook for the MapLibre agent. |

## Running the Worldview demo (URL adapter + plugin)

| Command | What it does |
|---|---|
| `uv run worldview-mcp` | The Worldview MCP server over stdio (`geo_ui_*` tools plus the permalink tool). `--transport http --port 8000` for streamable HTTP at `/mcp`; `MCP_TRANSPORT`, `MCP_HOST`, `MCP_PORT` are the env equivalents. |
| `demo/start.sh` | **needs keys.** Starts Chromium, warms the remote MCPs, then launches the marimo chat notebook. `AGENT=geoui` (default, the GeoUI treatment agent) or `AGENT=vlm` (the Playwright baseline). `MARIMO_MODE=edit` opens the notebook for editing. |
| `uv run marimo run demo/chat.py` | The notebook alone, without the Chromium launch (`AGENT` selects the agent as above). |
| `uv run python -m worldview.agents.geoui_agent` | **needs keys.** One LLM call through the GeoUI agent, as a wiring smoke test. |
| `uv run python -m worldview.agents.vlm_agent` | **needs keys.** The same for the VLM baseline agent. |
| `uv run python -m worldview.agents.warm_mcps` | Hits each enabled remote MCP once to absorb cold-start latency; lists the enabled servers. `start.sh` runs it for you. |

## Benchmarks (`geouibench`)

`<app>` is `worldview` or `maplibre`. Runs write to `benchmarks/<app>/results/<run-id>/`; committed run
directories are frozen records.

| Command | What it does |
|---|---|
| `uv run python -m geouibench datasets benchmarks/<app>` | Lists the app's datasets. |
| `uv run python -m geouibench run benchmarks/<app> gold --smoke --run-id smoke` | **needs keys.** The first golden of each dataset only, every agent kind: a quick end-to-end check. |
| `uv run python -m geouibench run benchmarks/<app> gold --run-id <id>` | **needs keys.** The full dataset against every agent kind (`--agent geoui` repeatable to restrict; `all` instead of `gold` for every dataset). Worldview gold: ~15 min for geoui, 1.5–2.5 h for vlm. MapLibre needs `npm run dev` running. |
| `uv run python -m geouibench score benchmarks/<app>/results/<id>` | Recomputes the four deterministic metrics from the committed traces; no agent, no network. `--metrics all` also re-runs the two LLM-judged metrics (**needs keys**); `--model` overrides the judge. |
| `uv run python -m geouibench summarize benchmarks/<app>/results/<id>` | Writes `summary.json` and `summary.md` for a run and scrubs machine-specific paths so it can be committed. `--reference <kind>` sets which agent the ratios are relative to. |
| `uv run python -m geouibench synthetic benchmarks/<app>` | **needs keys.** Generates a synthetic dataset from the gold one with deepeval (`--gold`, `--out`, `--model`, `--work-dir`). |
| `BENCHMARK_APP=benchmarks/<app> BENCHMARK_AGENT=<kind> BENCHMARK_DATASET=gold BENCHMARK_RUN=<run-id> DEEPEVAL_RESULTS_FOLDER=benchmarks/<app>/results/<run-id>/deepeval uv run deepeval test run benchmarks/geouibench/evals/test_benchmark.py -k core-4 --identifier <run-id>-<kind>` | **needs keys.** What `geouibench run` executes once per agent kind: the deepeval suite for one app, agent and dataset. Run by hand only to repeat a single kind. |
| `uv run pytest -q benchmarks/geouibench/tests` | The benchmark utility's own offline tests. |

## Publishing

| Command | What it does |
|---|---|
| (automatic) `.github/workflows/pages.yml` | On every push to `main` in `NASA-IMPACT/geoui-intent-protocol` that touches `schemas/**`, runs the schema drift check and publishes `schemas/` as https://nasa-impact.github.io/geoui-intent-protocol/, so each extension URI resolves to its file. Skipped in other repositories. Can also be started from the Actions tab (`workflow_dispatch`). |
