"""Run a task: pick the strongest available provider, invoke it, and on a quota error cool it down
and fail over to the next — so work keeps moving instead of stalling on one model's limit."""
from __future__ import annotations

import shlex
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from .config import Config, Provider
from .router import plan
from .state import State, now

# An executor takes (argv, stdin_text) and returns (exit_code, combined_output).
Executor = Callable[[list[str], str | None], "tuple[int, str]"]


_CMD_NOT_FOUND = 127       # provider CLI is missing/uninstalled
_UNAVAILABLE_COOLDOWN = 60  # short cooldown for a missing CLI (not a quota window)


@dataclass
class Attempt:
    provider: str
    exit_code: int
    quota_hit: bool
    seconds: float = 0.0
    unavailable: bool = False   # the provider CLI was missing (exit 127) — failed over like quota

    def label(self) -> str:
        """Provider name annotated with why it failed over (for status/trace lines)."""
        if self.quota_hit:
            return f"{self.provider}(quota)"
        if self.unavailable:
            return f"{self.provider}(unavailable)"
        return self.provider


@dataclass
class RunResult:
    provider: str | None          # provider that ultimately handled it, or None if none could
    exit_code: int
    output: str
    attempts: list[Attempt] = field(default_factory=list)
    exhausted: bool = False       # every candidate was cooled down / hit quota


def _argv_and_stdin(provider: Provider, prompt: str) -> tuple[list[str], str | None]:
    """Build argv from the command template. A literal `{prompt}` token becomes the prompt as a
    single argument (no shell interpolation); otherwise the prompt is piped on stdin."""
    tokens = shlex.split(provider.command)
    if "{prompt}" in tokens:
        return [prompt if tok == "{prompt}" else tok for tok in tokens], None
    return tokens, prompt


def _subprocess_executor(timeout: float | None) -> Executor:
    def run(argv: list[str], stdin_text: str | None) -> tuple[int, str]:
        try:
            proc = subprocess.run(  # noqa: S603 - argv from operator config, prompt passed as data
                argv, input=stdin_text, capture_output=True, text=True, timeout=timeout
            )
        except FileNotFoundError:
            return 127, f"command not found: {argv[0]}"
        except subprocess.TimeoutExpired:
            return 124, "timeout"
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")

    return run


def run_task(
    config: Config,
    state: State,
    prompt: str,
    *,
    task: str | None = None,
    executor: Executor | None = None,
    now_fn: Callable[[], float] = now,
    timeout: float | None = None,
) -> RunResult:
    """Try providers in routing order, failing over on quota errors. Mutates + (the caller) saves state."""
    if not prompt.strip():
        # cost control starts here: never spend a provider call on an empty prompt
        return RunResult(provider=None, exit_code=2, output="empty prompt — nothing to run")

    exec_fn = executor or _subprocess_executor(timeout)
    started = now_fn()  # one logical timestamp per invocation — keeps routing decisions consistent
    p = plan(config, state, task, started)
    result = RunResult(provider=None, exit_code=1, output="")

    if not p.order:
        result.output = f"no providers configured for task {task!r}"
        return result

    for name in p.order:
        provider = config.providers[name]
        if not state.get(name).available(started):
            continue  # still cooling down — skip
        argv, stdin_text = _argv_and_stdin(provider, prompt)
        before = time.monotonic()  # latency uses a monotonic clock, independent of the cooldown now_fn
        code, output = exec_fn(argv, stdin_text)
        elapsed = round(time.monotonic() - before, 3)
        quota = code != 0 and provider.matches_quota_error(output)
        unavailable = code == _CMD_NOT_FOUND
        result.attempts.append(Attempt(provider=name, exit_code=code, quota_hit=quota,
                                       seconds=elapsed, unavailable=unavailable))
        if quota or unavailable:
            # a quota-exhausted OR missing-CLI provider is cooled down and we fail over to the next,
            # so a broken/uninstalled model doesn't stall the whole run
            cooldown = provider.reset_seconds if quota else _UNAVAILABLE_COOLDOWN
            state.cool_down(name, started + cooldown)
            continue
        state.record_run(name, started)
        result.provider, result.exit_code, result.output = name, code, output
        return result

    # everyone was cooled down or hit quota this pass
    result.exhausted = True
    p2 = plan(config, state, task, started)
    if p2.soonest is not None:
        result.output = (
            f"all providers exhausted; {p2.soonest} frees up in {int(p2.soonest_eta)}s"
        )
    else:
        result.output = "all providers exhausted"
    return result
