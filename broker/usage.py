"""Estimate real token cost from agent-CLI transcripts, and how much of it is *mechanical* work
(search / scan / read orchestration) billed to a premium model that a cheap model would do fine.

This is the observability behind the routing guard: point `broker usage` at your Claude-Code-style
transcripts (JSONL with per-message `usage` token counts) and it shows the real spend by model tier,
the mechanical waste, and the before/after cost of routing that work to a cheap tier. Estimate-based
and auditable: it uses published list prices you can override, and never invents token counts.
"""
from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

# Anthropic list prices, USD per 1M tokens: (input, output). cache-read ≈ 0.1x input, cache-write ≈ 1.25x input.
TIER_PRICES: dict[str, tuple[float, float]] = {
    "opus": (15.0, 75.0),
    "sonnet": (3.0, 15.0),
    "haiku": (1.0, 5.0),
}

# tool calls that are pure search/scan/read orchestration — a cheap model handles these fine
_MECH_TOOLS = {"Grep", "Glob", "LS", "Read"}
_MECH_BASH = ("grep", "ls ", "cat ", "find ", "head ", "tail ", "wc ", "sed -n", "rg ",
              "git log", "git status", "git diff", "git show", "awk ", "sort", "uniq")


def tier_of(model: str) -> str:
    m = (model or "").lower()
    if "opus" in m:
        return "opus"
    if "haiku" in m:
        return "haiku"
    return "sonnet"  # sonnet or unknown -> standard tier


def message_cost(tier: str, usage: dict[str, Any]) -> float:
    inp, out = TIER_PRICES.get(tier, TIER_PRICES["sonnet"])
    it = usage.get("input_tokens", 0) or 0
    ct = usage.get("cache_creation_input_tokens", 0) or 0
    rt = usage.get("cache_read_input_tokens", 0) or 0
    ot = usage.get("output_tokens", 0) or 0
    return (it * inp + ct * (1.25 * inp) + rt * (0.1 * inp) + ot * out) / 1_000_000


def is_mechanical_turn(content: object) -> bool:
    """A turn is mechanical if it is dominated by search/scan/read tool calls with little generated
    text — orchestration a cheap model can do. Substantial reasoning or code output is not."""
    if not isinstance(content, list):
        return False
    text_len = tool_calls = mech_calls = 0
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            text_len += len(block.get("text", "") or "")
        elif block.get("type") == "tool_use":
            tool_calls += 1
            name = block.get("name", "")
            if name in _MECH_TOOLS:
                mech_calls += 1
            elif name == "Bash":
                cmd = str((block.get("input") or {}).get("command", "")).lower()
                if any(p in cmd for p in _MECH_BASH):
                    mech_calls += 1
    return bool(tool_calls) and mech_calls / tool_calls >= 0.5 and text_len < 400


@dataclass(frozen=True)
class UsageReport:
    sessions: int
    turns: int
    cost_by_tier: dict[str, float]
    tokens_by_tier: dict[str, int]
    mechanical_turns: int
    mechanical_cost_now: float
    mechanical_cost_cheap: float
    cheap_tier: str

    @property
    def total_cost(self) -> float:
        return round(sum(self.cost_by_tier.values()), 2)

    @property
    def recoverable(self) -> float:
        return round(self.mechanical_cost_now - self.mechanical_cost_cheap, 2)

    @property
    def cost_after(self) -> float:
        return round(self.total_cost - self.recoverable, 2)

    def render(self) -> str:
        total = self.total_cost
        lines = [
            f"sessions: {self.sessions}  ·  assistant turns: {self.turns:,}",
            f"estimated cost (list prices): ${total:,.2f}",
        ]
        for t in ("opus", "sonnet", "haiku"):
            if self.cost_by_tier.get(t):
                lines.append(f"  {t:<7} ${self.cost_by_tier[t]:>11,.2f}   "
                             f"({self.tokens_by_tier.get(t, 0) / 1e6:,.1f}M tokens)")
        if self.mechanical_turns and total:
            pct = self.recoverable / total * 100 if total else 0
            lines += [
                "",
                f"mechanical work on a premium model: {self.mechanical_turns:,} turns  "
                f"·  ${self.mechanical_cost_now:,.2f} now  vs  ${self.mechanical_cost_cheap:,.2f} on "
                f"{self.cheap_tier}",
                f"→ recoverable: ${self.recoverable:,.2f} ({pct:.0f}% of total)",
                f"BEFORE ${total:,.2f}   AFTER ${self.cost_after:,.2f}",
            ]
        return "\n".join(lines)


def _iter_assistant_records(path: Path) -> Iterable[dict[str, Any]]:
    """Yield full transcript records whose message is a costed assistant turn (keeps the top-level
    `timestamp` so callers can filter by day)."""
    try:
        fh = path.open(encoding="utf-8")
    except OSError:
        return
    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = rec.get("message")
            if isinstance(msg, dict) and msg.get("role") == "assistant" and msg.get("usage"):
                yield rec


def _on_local_date(rec: dict[str, Any], on_date: date, tz: Any) -> bool:
    ts = rec.get("timestamp")
    if not isinstance(ts, str):
        return False
    try:
        when = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(tz)
    except ValueError:
        return False
    return when.date() == on_date


def analyze(paths: Iterable[str | Path], cheap_tier: str = "haiku",
            on_date: date | None = None) -> UsageReport:
    """Estimate cost across transcripts. If `on_date` is given, count only turns from that local date
    (for a daily budget check)."""
    files = []
    for p in paths:
        p = Path(p)
        files.extend(sorted(p.rglob("*.jsonl")) if p.is_dir() else [p])
    tz = datetime.now().astimezone().tzinfo
    cost_by_tier: dict[str, float] = {}
    tokens_by_tier: dict[str, int] = {}
    mech_turns = 0
    mech_now = mech_cheap = 0.0
    turns = 0
    for fp in files:
        for rec in _iter_assistant_records(fp):
            if on_date is not None and not _on_local_date(rec, on_date, tz):
                continue
            msg = rec["message"]
            usage = msg["usage"]
            t = tier_of(msg.get("model", ""))
            c = message_cost(t, usage)
            cost_by_tier[t] = cost_by_tier.get(t, 0.0) + c
            tokens_by_tier[t] = tokens_by_tier.get(t, 0) + sum(
                usage.get(k, 0) or 0 for k in
                ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
            )
            turns += 1
            if t in ("opus", "sonnet") and is_mechanical_turn(msg.get("content")):
                mech_turns += 1
                mech_now += c
                mech_cheap += message_cost(cheap_tier, usage)
    return UsageReport(
        sessions=len(files),
        turns=turns,
        cost_by_tier={k: round(v, 2) for k, v in cost_by_tier.items()},
        tokens_by_tier=tokens_by_tier,
        mechanical_turns=mech_turns,
        mechanical_cost_now=round(mech_now, 2),
        mechanical_cost_cheap=round(mech_cheap, 2),
        cheap_tier=cheap_tier,
    )
