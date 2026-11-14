#!/usr/bin/env python3
"""Check the browser assets served to visitors against the OSV database.

Run as ``python3 scripts/check_browser_asset_vulns.py`` so ``scripts/`` is on
``sys.path``. Failures are recorded in ``.vuln-failures`` (deferred
enforcement); the script itself always exits 0 and the workflow's final step
fails the job when the file is non-empty. Accepted findings are OpenVEX
``not_affected`` statements under ``.vex/``.
"""

import json
import os
import sys
import urllib.error
import urllib.request

from threejs_assets import THREEJS_VERSION

OSV_URL = "https://api.osv.dev/v1/query"
TIMEOUT = 30
FAILURES_FILE = ".vuln-failures"

# (ecosystem, name, version, purl): a future asset is one entry.
TARGETS = [
    ("npm", "three", THREEJS_VERSION, f"pkg:npm/three@{THREEJS_VERSION}"),
]


def _post(body, opener):
    req = urllib.request.Request(
        OSV_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with opener(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode())


def query_osv(ecosystem, name, version, *, opener=urllib.request.urlopen):
    """Return every OSV vuln for the package version, following pagination.

    Each page is tried twice; the last error propagates.
    """
    vulns = []
    token = None
    while True:
        body = {"version": version, "package": {"name": name, "ecosystem": ecosystem}}
        if token:
            body["page_token"] = token
        for attempt in (1, 2):
            try:
                data = _post(body, opener)
                break
            except (urllib.error.URLError, OSError, ValueError):
                if attempt == 2:
                    raise
        if not isinstance(data, dict):
            raise ValueError("OSV response is not a JSON object")
        vulns.extend(data.get("vulns") or [])
        token = data.get("next_page_token")
        if not token:
            return vulns


def load_vex(vex_dir=".vex"):
    """Return ``(accepted, failures)``.

    ``accepted`` is a set of ``(vulnerability id or alias, product purl)``
    pairs from ``not_affected`` statements; ``failures`` lists statements
    missing a justification or impact statement (not accepted).
    """
    accepted = set()
    failures = []
    if not os.path.isdir(vex_dir):
        return accepted, failures
    for fname in sorted(os.listdir(vex_dir)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(vex_dir, fname)
        try:
            with open(path, encoding="utf-8") as f:
                doc = json.load(f)
        except (OSError, ValueError) as e:
            failures.append(f"{path}: unreadable VEX file ({e})")
            continue
        for st in doc.get("statements", []):
            if st.get("status") != "not_affected":
                continue
            vuln = st.get("vulnerability") or {}
            ids = [vuln.get("name")] + list(vuln.get("aliases") or [])
            ids = [i for i in ids if i]
            if not st.get("justification") or not st.get("impact_statement"):
                failures.append(
                    f"{path}: not_affected statement for {', '.join(ids) or '?'} "
                    "needs a justification and an impact_statement"
                )
                continue
            for product in st.get("products", []):
                purl = product.get("@id") if isinstance(product, dict) else None
                for i in ids:
                    if purl:
                        accepted.add((i, purl))
    return accepted, failures


def scan(targets, accepted, *, opener=urllib.request.urlopen, log=print):
    """Scan targets; return failure lines (also logged as annotations)."""
    failures = []
    for ecosystem, name, version, purl in targets:
        try:
            vulns = query_osv(ecosystem, name, version, opener=opener)
        except (urllib.error.URLError, OSError, ValueError) as e:
            log("::error::OSV query failed")
            log(f"osv query failed: package={name} version={version}")
            failures.append(f"OSV query failed for {name}@{version}: {e}")
            continue
        unaccepted = []
        n_accepted = 0
        for v in vulns:
            ids = [v.get("id")] + list(v.get("aliases") or [])
            if any((i, purl) in accepted for i in ids if i):
                n_accepted += 1
                log(f"accepted by .vex: {v.get('id')} for {purl}")
            else:
                unaccepted.append(v)
        log(
            f"osv query {ecosystem}/{name}@{version}: "
            f"{len(vulns)} advisories, {n_accepted} accepted"
        )
        for v in unaccepted:
            msg = f"Browser asset vulnerability: {v.get('id')} affects {name}@{version}"
            summary = " ".join(str(v.get("summary") or "").split())
            log("::error::Browser asset vulnerability found")
            log(
                f"browser asset vulnerability: advisory={v.get('id')} "
                f"package={name} version={version} summary={summary}".rstrip()
            )
            failures.append(f"{msg} {summary}".rstrip())
    return failures


def main():
    accepted, failures = load_vex()
    for f in failures:
        print("::error::Invalid .vex statement")
        print(f"vex failure: {f}")
    failures = list(failures)
    failures += scan(TARGETS, accepted)
    with open(FAILURES_FILE, "w", encoding="utf-8") as f:
        f.write("".join(line + "\n" for line in failures))
    print(f"wrote {FAILURES_FILE}: {len(failures)} failure(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
