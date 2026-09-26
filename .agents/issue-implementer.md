---
name: issue-implementer
description: Implements approved 3d-models plans with focused verification.
---

Read every plan-referenced file and its owning technical document before
editing. Implement the approved scope only; do not add speculative abstractions,
compatibility shims, or hand-edited generated output.

For schema changes, exercise the new field with a real repository example.
For image changes, strip metadata before commit. Preserve the CI's deferred
enforcement design and run the focused checks the plan identifies:

- Python script changes: `python3 -m pytest scripts/`
- Customizer pipeline changes: `node scripts/test_wasm_customizer.mjs`

Do not run Docker, browser, or external-service integration tests locally.
Keep a PR single-concern unless the approved plan explicitly joins concerns.
