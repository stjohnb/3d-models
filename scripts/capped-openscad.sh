#!/usr/bin/env bash
# Run OpenSCAD under a memory + wall-clock cap so a runaway render fails
# cleanly instead of freezing the self-hosted runner (see issue #272).
# All arguments are forwarded verbatim to openscad.
#
# Tunables (env, with defaults):
#   RENDER_MEM_MAX  memory ceiling, systemd MemoryMax syntax (default 8G)
#   RENDER_TIMEOUT  wall-clock seconds before SIGTERM/SIGKILL (default 600)
#
# Exit code is propagated from the wrapped command. Notably:
#   124        timeout fired (time cap exceeded)
#   137 (>=128) process SIGKILLed (systemd MemoryMax / OOM killer)
set -uo pipefail

MEM_MAX="${RENDER_MEM_MAX:-8G}"
TIMEOUT="${RENDER_TIMEOUT:-600}"

if command -v systemd-run >/dev/null 2>&1 \
   && systemd-run --user --scope --quiet -- true >/dev/null 2>&1; then
  systemd-run --user --scope -p MemoryMax="$MEM_MAX" --quiet -- \
    timeout "$TIMEOUT" openscad "$@"
  rc=$?
else
  echo "::warning::systemd-run --user unavailable; using ulimit -v + timeout fallback for openscad cap" >&2
  kib="$(numfmt --from=iec "$MEM_MAX" 2>/dev/null || echo "")"
  if [ -n "$kib" ]; then kib=$(( kib / 1024 )); fi
  (
    [ -n "$kib" ] && ulimit -v "$kib" 2>/dev/null || true
    exec timeout "$TIMEOUT" openscad "$@"
  )
  rc=$?
fi

if [ "$rc" -eq 124 ] || [ "$rc" -ge 128 ]; then
  echo "render exceeded memory/time cap (rc=$rc): openscad $*" >&2
fi
exit "$rc"
