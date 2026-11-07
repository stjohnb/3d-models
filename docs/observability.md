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
2. The CI pipeline on Forgejo `[container, linux]` runners (`build.yml`,
   `pages.yml`, `pr-preview-cleanup.yml`), plus the on-demand `render-heavy.yml`
   on `[container, linux, ram-12g]`.
3. Build and helper scripts in `scripts/`, and the OpenSCAD sources.

Which subsections apply: Metrics applies to the site (analytics). Logging
applies to scripts and CI steps. Traces and Latency budgets are `none`, and Dashboards and
alerts has no dashboard and no error-log alert rule, each with a reason below. What every change adds applies to
CI steps and external calls.

### Logging

Scripts and workflow steps write human-readable progress to the Forgejo Actions
step log, and use `::warning::` / `::error::` annotations and the
deferred-enforcement failure files (`.meta-failures`, `.param-failures`,
`.thumb-failures`, `.dxf-failures`). That output stays as it is. Nothing from this repo is
shipped to Loki: CI job output lives only in the Forgejo Actions run log.

Any new structured log output in a Python script or shell script follows the
St-John-Software structured logging contract: one JSON object per line on
stdout, never to files, with the fields below (a Python script prints
`json.dumps` of one dict per line; shell scripts such as
`scripts/capped-openscad.sh` may use logfmt). Loki parses it at query time with
`| json`. No script in this repo emits that JSON today (see
[Known gaps](#known-gaps)).

| Field | Rule |
|---|---|
| `time` | ISO 8601 UTC with milliseconds |
| `level` | lowercase **string**, one of `trace debug info warn error fatal`. Never numeric |
| `msg` | short, constant message. Ids and values go in fields, never interpolated into the message |
| `service` | service name, matching the Kubernetes `app` label |
| `component` | subsystem or job name (e.g. `reminder-monitor`) |
| `err` | object `{ type, message, stack }` for errors. Never a bare string |
| correlation keys | `request_id`, `run_id`, `repo`, `issue`, `pr` when known |
| HTTP access lines | `http.method`, `http.path`, `http.status`, `duration_ms` |

- Keys are `snake_case`; durations end in `_ms`.
- No secrets, tokens or credentials in any field or message.
- Pretty-print only when stdout is a TTY. In containers always emit JSON.
- Shell scripts and CronJobs may use logfmt (`level=info msg="..."`) since JSON is awkward in
  shell. Loki parses both.
- Keep Loki labels low-cardinality: nothing in this contract becomes a Loki label; fields are
  parsed at query time with `| json` / `| logfmt`.

Log route: workflow step output is written to the Forgejo Actions run log and
job summary and is not collected by Promtail or Alloy. The only lines that
reach Loki are the runner pods' own task lines, queryable with
`{app=~"forgejo-runner.*", container="runner"} |= "St-John-Software/3d-models"`
(logfmt, `level=info`); they name the task and repo but carry no step output. A
failed `main` run surfaces as a `Build failure: <workflow name>` issue through
Claws' `main-build-monitor`.

Levels and shipping, as rules for new changes:

- Every action a component takes logs one `info` line naming the action and its outcome or new
  state: an actuation or relay change, a write to another system, a job's start and finish, a
  config or state change. Routine polling and sensor readings stay at `debug`. Failures log at
  `warn` or `error`.
- Every `info`-and-above line a component emits reaches Loki and can be queried per component.
  Never set a log filter or forwarding level that drops `info`.
- A component whose lines cannot reach Loki lists that under Known gaps.

In this repo a script's `info` line is a step-log line that names the action and
its outcome (for example the S3 prefix synced, the cache key written, the
comment posted); the Loki shortfall is the first Known gap.

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

no dashboard: this repo emits no metrics; fleet-infra
`apps/monitoring/dashboards/` has no 3d-models ConfigMap, and no alert rule sets
a `claws_service` value for this repo. The analytics dashboard is the Plausible
UI for `bstjohn.net`.

No Grafana alert rule watches this repo's error and fatal log lines: fleet-infra
`apps/monitoring/kube-prometheus-stack.yaml` has no rule for it, because no
`error`-level line from this repo reaches Loki. Failures are surfaced by
`::error::` annotations and the deferred-enforcement step that fails the run,
which `main-build-monitor` turns into the `Build failure` issue below. A change
that later ships error lines to Loki adds a Grafana-managed rule there with a
`claws_alertname` label templated from `app`, `component` and the constant
`msg`, and names it here.

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
- A new action or state-changing command (an S3 sync or delete, a render-cache
  write, a Forgejo comment or branch operation): print one step-log line naming
  the action and outcome, in the same PR.
- A new `error`/`fatal` path: use a `::error::` annotation with a short constant
  message and ids as values, and record the failure in the matching
  `.<kind>-failures` file so the end-of-build enforcement fails the run.
- A new metric, route family or job worth a Grafana panel is not expected; a PR
  that adds one also adds the panel through a companion PR in fleet-infra on the
  same issue.

### Known gaps

- Accepted: CI jobs and scripts only. Step output is human-readable text and
  `::warning::` / `::error::` annotations, not JSON lines, and only the runner's
  task lines reach Loki, so no `info` line from a script is queryable per
  component.
- Accepted: no Grafana rule watches error or fatal log lines, since none reach
  Loki; `::error::` annotations plus `main-build-monitor` are the alerting path.
- Accepted: static S3 site with no server to probe. The gallery at
  `https://www.bstjohn.net/3d-models/` has no uptime target and no Gatus endpoint
  in fleet-infra `apps/gatus/config.yaml`.
- Accepted: no runtime to trace. CI per-step timing exists only in the Forgejo
  Actions run log, with no spans or metrics for build duration.
