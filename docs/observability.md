# Observability policy

This is the repo's observability policy under the St-John-Software observability
contract (<https://git.home.bstjohn.net/St-John-Software/claws/src/branch/main/docs/observability-contract.md>).
Each subsection gives this repo's real answer, or `none` with the reason.

## Observability

### Scope

This repo runs no long-running service, HTTP server, database or CronJob. Three
things exist:

1. A static gallery site built by `.forgejo/workflows/build.yml` and synced to
   `s3://www.bstjohn.net/3d-models/` (served at
   `https://www.bstjohn.net/3d-models/`), with PR previews under `pr-preview/`
   and issue previews under `issue-preview/`. Spec pages publish via
   `pages.yml` to the private pages host.
2. The CI pipeline on Forgejo `[container, linux]` runners, plus the on-demand
   `render-heavy.yml`.
3. Build and helper scripts in `scripts/`, and the OpenSCAD sources.

Which subsections apply: Metrics applies to the site (analytics). Logging
applies to scripts and CI steps. Traces, Latency budgets and Dashboards and
alerts are `none`, each with a reason below. What every change adds applies to
CI steps and external calls.

### Logging

Scripts and workflow steps write human-readable progress to the Forgejo Actions
step log, and use `::warning::` / `::error::` annotations and the
deferred-enforcement failure files (`.meta-failures`, `.param-failures`,
`.thumb-failures`, `.dxf-failures`). That output stays as it is. Nothing from this repo is
shipped to Loki: CI job output lives only in the Forgejo Actions run log.

Any new structured log output in a Python or Node script follows the contract
below: one JSON object per line on stdout, lowercase string `level`, an `err`
object `{ type, message, stack }` for errors, and no secrets, tokens or
credentials (for example credentials derived from `AWS_ROLE_ARN`, or Forgejo
tokens). Shell scripts such as `scripts/capped-openscad.sh` may use logfmt.

Any new structured log output in a script or a future service must follow the
St-John-Software structured logging contract: one JSON object per line on stdout,
never to files. Loki parses it at query time with `| json`. No script in this repo
emits that JSON today (see [Known gaps](#known-gaps)).

| Field | Rule |
|---|---|
| `time` | ISO 8601 UTC with milliseconds |
| `level` | lowercase **string**, one of `trace debug info warn error fatal`. Never numeric (pino's default numeric levels are not detected by Loki) |
| `msg` | short, constant message. Ids and values go in fields, never interpolated into the message |
| `service` | service name, matching the Kubernetes `app` label |
| `component` | subsystem or job name (e.g. `reminder-monitor`) |
| `err` | object `{ type, message, stack }` for errors. Never a bare string |
| correlation keys | `request_id`, `run_id`, `repo`, `issue`, `pr` when known |
| HTTP access lines | `http.method`, `http.path`, `http.status`, `duration_ms` |

- Keys are `snake_case`; durations end in `_ms`.
- No secrets, tokens or credentials in any field or message.
- Pretty-print only when stdout is a TTY (e.g. `pino-pretty` in dev). In containers always emit JSON.
- Shell scripts and CronJobs may use logfmt (`level=info msg="..."`) since JSON is awkward in
  shell. Loki parses both.
- Keep Loki labels low-cardinality: nothing in this contract becomes a Loki label; fields are
  parsed at query time with `| json` / `| logfmt`.
- Do not add direct `console.*` calls to service code; log through the shared logger module.

Reference Node implementation (pino):

```ts
import pino from "pino";

export const logger = pino({
  base: { service: "my-service", component: "api" },
  timestamp: pino.stdTimeFunctions.isoTime,
  formatters: { level: (label) => ({ level: label }) },
  serializers: { err: pino.stdSerializers.err },
});
```

The `formatters.level` line is required: without it pino emits numeric levels (`"level":30`),
which Loki does not detect.

### Metrics

Metrics endpoint: `none`. The site is static files on S3, so there is nothing
to scrape.

Analytics: the gallery's `index.html` and `embed.html` load a Plausible script
tag, self-hosted at `plausible.bstjohn.net` with `data-domain="bstjohn.net"`.
It is cookieless. The series are the built-in page views, outbound-link clicks
and file downloads of the loaded script variant, shown in the Plausible site
dashboard for `bstjohn.net`. The gallery makes no custom `plausible()` event calls. The collector is the Plausible deployment in
production-infra `apps/plausible`, whose `ingestion-probe.yaml` CronJob checks
ingestion every 15 minutes.

The standalone viewers under `site/standalone/` deliberately omit the script so
they stay self-contained and offline. This matches the Analytics row of
[OVERVIEW.md](OVERVIEW.md).

### Traces

`none`. There is no tracing SDK, no spans and no backend. Per-step timing is
visible only in the Forgejo Actions run log.

### Latency budgets

`none` as a numeric target. The site is static files on S3, and no uptime probe
exists for it (fleet-infra Gatus probes no `www.bstjohn.net` endpoint). The
viewer's client-side render budget (on-demand rendering, requestAnimationFrame
suspension after about 90 idle frames) in
[web-viewer.md](web-viewer.md#render-budget) is a performance policy, not an
SLO. If an uptime target is ever adopted it belongs here, together with a Gatus
endpoint in fleet-infra `apps/gatus/config.yaml`.

### Dashboards and alerts

There is no Grafana dashboard or alert rule for this repo (fleet-infra
`apps/monitoring/dashboards/` has none). The analytics dashboard is the
Plausible UI for `bstjohn.net`.

Alerts that notify someone:

- Claws' `main-build-monitor` opens or bumps a `Build failure: <workflow name>`
  issue in this repo when any workflow fails on `main`, for example
  `Build failure: Build Models` (`build.yml`) or the spec-pages workflow
  (`pages.yml`). It retries a transient failure once and closes the issue when a
  later run of that workflow passes (see
  [ci-pipeline.md](ci-pipeline.md#main-branch-failure-monitoring)).
- growth-engine's site-visit issue filer files `site-review-*` issues here via
  the `issueFiler` entry in `claws.json`.

PR runs produce a preview comment and step summary, never an alert.

### What every change adds

What a change must instrument when it adds:

- A new HTTP route: `none`, the repo serves no routes. A new page or viewer must
  keep the Plausible tag policy: gallery pages carry it, standalone viewers never do.
- A new DB query: `none`, there is no database.
- A new background job (a new workflow, scheduled run or build step): record
  failures through the deferred-enforcement pattern enforced at the end of
  `build.yml`, print its start and result to the step log, and document it in
  [ci-pipeline.md](ci-pipeline.md) so `main-build-monitor` covers it.
- A new external call (S3 sync, upstream Three.js or openscad-wasm download,
  Forgejo API, terrain data): log the target and outcome in the step log, pin
  and verify any downloaded artefact (SHA-256, as `scripts/fetch_threejs.py`
  does), state whether failure is best-effort (`::warning::`) or fatal, and
  never print credentials.

### Known gaps

- Accepted: CI jobs and scripts only, nothing ships to Loki. Script and workflow
  output is human-readable step-log text and `::warning::` / `::error::`
  annotations, not JSON lines. No script in this repo uses a shared JSON logger.
- Accepted: static S3 site with no server to probe. The gallery at
  `https://www.bstjohn.net/3d-models/` has no uptime target and no Gatus endpoint
  in fleet-infra `apps/gatus/config.yaml`.
- Accepted: no runtime to trace. CI per-step timing exists only in the Forgejo
  Actions run log, with no spans or metrics for build duration.
