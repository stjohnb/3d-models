# Security policy

This is the repo's security policy under the St-John-Software security contract
(<https://git.home.bstjohn.net/St-John-Software/claws/src/branch/main/docs/security-contract.md>).
Each subsection gives this repo's real answer, or `does not apply` with the reason.

## Security

### Scope

The repo ships OpenSCAD sources and a static Three.js gallery. It is detected as
firmware/hardware but builds no firmware: the enclosures are models only. It runs
no long-running service, server or database.

- `build.yml` syncs the gallery to `s3://www.bstjohn.net/3d-models/`, served
  publicly at `https://www.bstjohn.net/3d-models/`, with `pr-preview/` and
  `issue-preview/` prefixes.
- `pages.yml` publishes spec pages to the Garage host `pages.home.bstjohn.net`.
- `scripts/sync_public_snapshot.py` builds a sanitised mirror that the
  maintainer pushes by hand to `github.com/stjohnb/3d-models`.
- CI runs on Forgejo `[container, linux]` runners; `render-heavy.yml` runs on
  `[container, linux, ram-12g]`.

### Dependency and image vulnerabilities

No container image is published (there is no Dockerfile and no image push), so
the image scan gate does not apply.

No dependency vulnerability scanner runs. Three dependency sets are unscanned:

- the nixpkgs toolchain locked by `flake.lock` (CI-only);
- Three.js `0.170.0`, pinned in `scripts/threejs_assets.py`;
- openscad-wasm `2022.03.20`, pinned in `scripts/fetch_openscad_wasm.py`.

Both browser assets are SHA-256-verified before staging. Rule for new changes: a
workflow that starts pushing an image must scan it first with trivy
(`--severity HIGH,CRITICAL --ignore-unfixed --exit-code 1`) and cover accepted
findings with `.vex/` statements.

### Accepted findings

`none`: no scanner runs and no image exists, so there is no `.vex/` directory.
Rule for new changes: an accepted finding is an OpenVEX `not_affected` statement
under `.vex/`, with a justification and an impact statement.

### Secrets

- `secrets.AWS_ROLE_ARN`: the role ARN, assumed through Forgejo OIDC with
  `configure-aws-credentials` in `build.yml`, `render-heavy.yml` and
  `pr-preview-cleanup.yml`. There are no long-lived AWS keys.
- Org-level `PAGES_S3_ACCESS_KEY_ID` / `PAGES_S3_SECRET_ACCESS_KEY`: Garage keys
  used by `pages.yml` and `pr-preview-cleanup.yml`.
- `secrets.GITHUB_TOKEN`: Forgejo's automatic job token, used for PR comments
  and the gallery commit (`build.yml`, `pages.yml`).
- The gitignored local `.mcp-claws.json` holds `HOME_ASSISTANT_TOKEN` and
  `CLAWS_MCP_AUTH_TOKEN`. The public snapshot uses a tracked-files-only manifest
  and a secret-pattern denylist, which keep these out of the mirror.
- `claws.json` `issueFiler.tokenSha256` is a hash only.

Rule for new changes: never commit credentials, Wi-Fi passwords or API keys in
SCAD, `meta.json` or scripts.

### Supply chain

- Remote actions are pinned to full commit SHAs with `# vX.Y.Z` comments
  (`actions/checkout` v7.0.1, `aws-actions/configure-aws-credentials` v6.3.0).
- The toolchain comes from `flake.nix`, locked by `flake.lock`. admesh is
  fetched by URL with a hash.
- The browser assets are pinned by version and SHA-256; an unpinned hash is a
  hard build failure.
- `.openscad-version` records the expected OpenSCAD version.
- Freshness is not automated today (see Known gaps). Rule for new changes: pin
  new dependencies and actions the same way.

### Exposure and authentication

- The public gallery and its PR and issue previews: S3 static hosting,
  read-only and unauthenticated by design.
- Spec pages at `pages.home.bstjohn.net`: behind Authentik, LAN and tailnet
  only, per fleet-infra `docs/pages.md`.
- The public GitHub mirror: updated by a manual push by the maintainer.
- The gallery page loads the self-hosted Plausible script from
  `plausible.bstjohn.net`.
- Nothing runs in a cluster, so there is no ingress or network policy in
  fleet-infra or production-infra.
- The deploy role's trust policy is in bstjohn-blog
  `tofu/3d-models-deploy-role.tf`.

### Known gaps

1. The repo is not in fleet-infra `apps/renovate/configmap.yaml`
   `repositories`, so the SHA-pinned actions and `flake.lock` get no update PRs.
2. `flake.lock` has no automated refresh; it was last bumped on 2026-08-05.
3. Nothing scans for vulnerabilities in Three.js `0.170.0` or openscad-wasm
   `2022.03.20`, which are served to visitors' browsers.
4. Accepted: the deploy role trusts `repo:St-John-Software/3d-models:ref:refs/heads/*`
   and `:pull_request`, so a same-repo PR run can write to the production
   bucket. Previews need it, only collaborators can push same-repo branches, and
   fork PRs get no secrets.
5. Accepted: the role's permission policies are console-owned and deliberately
   unmanaged in bstjohn-blog tofu; only the trust policy is reviewed IaC.
6. Accepted: the Plausible script loads cross-origin without SRI. It is
   first-party and self-hosted, and its content changes with Plausible upgrades.
7. Accepted: the CI toolchain is not vulnerability-scanned. It runs only in
   ephemeral job containers and is not shipped.
