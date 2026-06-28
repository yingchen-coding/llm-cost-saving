# modelbroker

> **Run out of Claude quota? Keep working on Codex. Quota back? Switch back.**
> A quota-aware multi-model router: route each task to the model that's strongest at it, fail over
> when one runs out of quota, and resume the moment its window resets.

[![CI](https://github.com/yingchen-coding/modelbroker/actions/workflows/ci.yml/badge.svg)](https://github.com/yingchen-coding/modelbroker/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Stop babysitting model quotas.

You pay for two or three coding assistants (Claude Code, Codex, ...), each with its own usage limit.
When one hits its limit you either stop, or manually switch. modelbroker does the switch for you,
routes each kind of task to whichever model is best at it, and flips back when the quota window
resets. Zero dependencies, no API keys; it drives the CLIs you already have.

## Star This If

- You use multiple AI coding CLIs and lose time when one hits quota.
- You want task-based routing instead of one default model for every job.
- You need local traces showing which provider handled each task, why failover happened, and when it recovered.

## What it does

- **Strength-based routing.** A `codegen` task goes to Codex; an `architecture` or `reasoning` task
  goes to Claude — you define the policy.
- **Quota-aware fail-over.** A provider that returns a rate-limit / usage-limit error is **cooled
  down** for its reset window and the task automatically retries on the next provider. No wasted
  call, no manual switch.
- **It remembers.** The cooldown is persisted, so the *next* command still knows Claude is limited
  until 4pm and keeps routing to Codex — then flips back when the window resets.
- **Cost visibility.** Add optional `cost_per_run_usd` estimates per provider and `broker trace`
  rolls up spend by provider. It does not invent token counts your CLIs did not expose.
- **Cost-aware routing.** Keep your hand-tuned routing order, force cheapest-first routing, or use a
  balanced policy that keeps task fit first and then picks the cheaper comparable provider.
- **Safe by construction.** The prompt is passed as a single argument (or stdin), never interpolated
  into a shell — no injection from prompt text.

## Quickstart

```bash
pip install -e .          # or: pip install git+https://github.com/yingchen-coding/modelbroker
broker init              # write a starter broker.toml (claude + codex)

broker route -t codegen  # → would use: codex
broker route -t reasoning# → would use: claude
broker status            # availability / cooldown / usage per provider
broker doctor            # check each provider's CLI is installed / on PATH (no prompt run)

broker run -t codegen "write a quicksort in python"
# claude out of quota → uses codex; claude back in window → uses claude. automatically.

broker skills
broker run -t writing --skill stop-slop "rewrite this README section"
# adds a low-fluff quality contract before routing to the best available provider.

broker run -t codegen --skill context-window "fix the failing test"
# tells the model to pass only the smallest useful context, code-only when possible, and compact
# before long-context drift.

broker trace             # see your real routing / failover / cost behavior over time
# runs: 42 · failovers: 7 · quota events: 9 · unresolved: 0
#   claude  handled 31
#   codex   handled 11

broker cost              # see spend risk and cheaper routing recommendations
# estimated_cost: $1.2400
# recommendations:
#   set [budget].cost_strategy = "balanced" ...
```

## How a config looks

`broker.toml` — providers (with strengths + how they signal "out of quota") and a routing policy:

```toml
[providers.claude]
command = "claude -p {prompt}"     # {prompt} = the task, passed as one argument
strengths = ["reasoning", "architecture", "refactor", "review"]
reset = "5h"                       # cool down this long after a usage-limit error
quota_markers = ["usage limit", "rate limit", "429", "resets at"]
cost_per_run_usd = 0.0              # optional estimate for broker trace summaries
# Optional and deliberately provider-specific: retry this request elsewhere without marking
# Claude unhealthy or cooling it down.
refusal_markers = ["classified as a policy risk", "cannot assist with this request"]

[providers.codex]
command = "codex exec {prompt}"
strengths = ["codegen", "boilerplate", "tests"]
reset = "1h"
cost_per_run_usd = 0.0

[routing]
default = ["claude", "codex"]      # global fail-over order
[routing.tasks]
codegen   = ["codex", "claude"]    # route by task to the model that's strongest at it
reasoning = ["claude", "codex"]
```

Any CLI works — add a `[providers.<name>]` with its command and quota markers (gemini, aider, a
local model via `ollama run`, …).

Cost optimization is policy-driven: set `cost_per_run_usd`, inspect `broker trace`, then route cheap
tasks to cheaper providers in `[routing.tasks]` while reserving expensive models for the work they
actually win.

For a hard ceiling, add this under `[budget]`:

```toml
[budget]
state_file = ".broker-state.json"
max_cost_per_run_usd = 0.02
cost_strategy = "balanced"            # ordered | cheapest | balanced
```

Providers whose `cost_per_run_usd` exceeds the ceiling are skipped before execution. Set the value
to `0.0` to disable cost filtering. `cost_strategy` controls the remaining candidates:

- `ordered`: preserve your configured routing order.
- `cheapest`: route to the lowest estimated `cost_per_run_usd` first.
- `balanced`: prefer providers whose `strengths` include the task, then choose the cheaper one.

`refusal_markers` handles over-refusal separately from outages and quota. When a configured phrase
matches, the same prompt is tried on the next provider, the attempt is traced as `refusal`, and the
first provider remains available for unrelated requests. Keep the markers narrow: broad phrases
such as `cannot` can also occur in valid answers.

## Cost Radar

`broker cost` turns trace history and provider price estimates into an operational cost report:

- total estimated spend and average cost per run
- provider-level spend split
- providers over the configured per-run ceiling
- routing recommendations when a cheaper comparable provider exists
- warnings when failovers or unresolved runs show the policy is too brittle

This is deliberately estimate-based. modelbroker does not invent token counts your CLIs did not
emit; it uses the `cost_per_run_usd` numbers you configure so routing decisions stay auditable.

## Prompt Skills

`--skill stop-slop` is for prompts where the real problem is output quality, not model choice. It
wraps your request with a strict response contract: answer directly, use concrete evidence, remove
generic filler, state uncertainty precisely, and keep the final response tight.

`--skill context-window` is for long tasks. It tells the model to pass the smallest sufficient
context for the current step, use code-only context when code is enough, delay bulky logs/data until
the step that needs them, and compact or summarize before the context window gets unstable. If the
environment supports a slash command such as `/compact`, the skill explicitly tells the model to use
it at checkpoints.

```bash
broker run -t review --skill stop-slop "review this PR"
broker run -t writing --skill stop-slop "make this launch copy sharper"
broker run -t codegen --skill context-window "continue this implementation"
broker run -t architecture --skill context-window --skill stop-slop "design the next slice"
```

Skills are applied before routing, so they work with the same quota fail-over and trace behavior as
normal runs. Use `broker skills` to list available skills.

## How fail-over works

```
broker run -t reasoning "refactor this module"
  → claude (preferred for reasoning)
      └─ "Error: usage limit reached, resets at 4pm"   → cool down claude 5h
  → codex (next in order)
      └─ ok                                            → return codex's output
# every later command skips claude until its window resets, then routes back to it
```

## License

MIT © Ying Chen

## Local Review

```bash
scripts/pr_review_check.sh
```
