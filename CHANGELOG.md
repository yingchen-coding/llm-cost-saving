# Changelog

## 0.2.0 — 2026-06-20

- **`broker trace`** — every `run` now appends a JSONL trace (provider, exit, quota events,
  per-attempt latency); `broker trace` summarizes routing / failover / quota / wall-time so you can
  see real cost behavior over time.
- **Fix:** default `codex` command now passes `--skip-git-repo-check`, so `broker run` works outside
  a trusted git dir (found by dogfooding — codex aborted otherwise).
- Per-attempt latency recorded via a monotonic clock, independent of the cooldown clock.

## 0.1.0 — 2026-06-20

Initial release. Quota-aware multi-model router (`broker`):

- **Strength routing** — per-task provider order (`[routing.tasks]`) over a global fail-over default.
- **Quota fail-over** — a provider whose output matches its `quota_markers` on a nonzero exit is
  cooled down for its `reset` window; the task automatically retries on the next provider.
- **Persisted cooldown state** (`.broker-state.json`) — later commands keep routing around a
  limited provider until its window resets, then flip back.
- **Safe invocation** — the prompt is passed as a single argv token (or stdin), never shell-interpolated.
- **CLI** — `broker run | route | status | init`. Zero runtime dependencies, Python ≥3.11.
