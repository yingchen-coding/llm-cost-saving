"""Estimate real token cost from agent-CLI transcripts, and how much of it is *mechanical* work
(search / scan / read orchestration) billed to a premium model that a cheap model would do fine.

This is the observability behind the routing guard: point `broker usage` at your Claude-Code-style
transcripts (JSONL with per-message `usage` token counts) and it shows the estimated spend by model
tier, the mechanical waste, and the before/after cost of routing that work to a cheap tier.
Estimate-based and auditable: it uses linked published list prices and never invents token counts.
"""
from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

# Anthropic list prices, USD per 1M tokens: (input, output). Model-specific exceptions are handled
# by prices_for_model so historical transcripts are not priced as whichever tier is current today.
TIER_PRICES: dict[str, tuple[float, float]] = {
    "fable": (10.0, 50.0),
    "opus": (5.0, 25.0),
    "sonnet": (3.0, 15.0),
    "haiku": (1.0, 5.0),
}
PRICING_SOURCES = {
    "fable_5": "https://www.anthropic.com/claude/fable",
    "opus_4_7_4_8": "https://www.anthropic.com/research/claude-opus-4-8",
    "sonnet_5": "https://www.anthropic.com/news/claude-sonnet-5",
    "haiku_4_5": "https://www.anthropic.com/claude/haiku",
}

# tool calls that are pure search/scan/read orchestration — a cheap model handles these fine
_MECH_TOOLS = {"Grep", "Glob", "Read"}
_MECH_BASH = ("grep", "ls ", "cat ", "find ", "head ", "tail ", "wc ", "sed -n", "rg ",
              "git log", "git status", "git diff", "git show", "awk ", "sort", "uniq")


def tier_of(model: str) -> str:
    m = (model or "").lower()
    if "fable" in m or "mythos" in m:
        return "fable"
    if "opus" in m:
        return "opus"
    if "haiku" in m:
        return "haiku"
    return "sonnet"  # sonnet or unknown -> standard tier


def prices_for_model(model: str, timestamp: str | None = None) -> tuple[float, float]:
    """Return published API list prices for model/version, including dated launch pricing."""
    m = (model or "").lower()
    if "fable-5" in m or "fable_5" in m or "mythos-5" in m or "mythos_5" in m:
        return TIER_PRICES["fable"]
    if any(version in m for version in ("opus-4-5", "opus-4-6", "opus-4-7", "opus-4-8")):
        return TIER_PRICES["opus"]
    if "sonnet-5" in m or "sonnet_5" in m:
        when = _parse_timestamp(timestamp)
        if when is None or when.date() <= date(2026, 8, 31):
            return (2.0, 10.0)
    return TIER_PRICES.get(tier_of(model), TIER_PRICES["sonnet"])


def _parse_timestamp(timestamp: str | None) -> datetime | None:
    if not timestamp:
        return None
    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None


def _cost(prices: tuple[float, float], usage: dict[str, Any]) -> float:
    inp, out = prices
    it = usage.get("input_tokens", 0) or 0
    ct = usage.get("cache_creation_input_tokens", 0) or 0
    rt = usage.get("cache_read_input_tokens", 0) or 0
    ot = usage.get("output_tokens", 0) or 0
    cache = usage.get("cache_creation")
    if isinstance(cache, dict):
        one_hour = cache.get("ephemeral_1h_input_tokens", 0) or 0
        five_minute = cache.get("ephemeral_5m_input_tokens", 0) or 0
        unspecified = max(0, ct - one_hour - five_minute)
    else:
        one_hour = five_minute = 0
        unspecified = ct
    return (
        it * inp
        + (five_minute + unspecified) * (1.25 * inp)
        + one_hour * (2.0 * inp)
        + rt * (0.1 * inp)
        + ot * out
    ) / 1_000_000


def message_cost(tier: str, usage: dict[str, Any]) -> float:
    return _cost(TIER_PRICES.get(tier, TIER_PRICES["sonnet"]), usage)


def model_message_cost(model: str, usage: dict[str, Any], timestamp: str | None = None) -> float:
    return _cost(prices_for_model(model, timestamp), usage)


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
    records_scanned: int = 0
    duplicate_records_removed: int = 0
    synthetic_records_skipped: int = 0

    @property
    def total_cost(self) -> float:
        return round(sum(self.cost_by_tier.values()), 2)

    @property
    def recoverable(self) -> float:
        return round(self.mechanical_cost_now - self.mechanical_cost_cheap, 2)

    @property
    def cost_after(self) -> float:
        return round(self.total_cost - self.recoverable, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": "API list-price estimate; not an invoice or subscription charge",
            "sessions": self.sessions,
            "assistant_turns": self.turns,
            "records_scanned": self.records_scanned,
            "duplicate_records_removed": self.duplicate_records_removed,
            "synthetic_records_skipped": self.synthetic_records_skipped,
            "cost_by_tier_usd": self.cost_by_tier,
            "tokens_by_tier": self.tokens_by_tier,
            "estimated_cost_usd": self.total_cost,
            "mechanical_turns": self.mechanical_turns,
            "mechanical_cost_current_usd": self.mechanical_cost_now,
            "mechanical_cost_at_cheap_tier_usd": self.mechanical_cost_cheap,
            "cheap_tier": self.cheap_tier,
            "estimated_recoverable_usd": self.recoverable,
            "estimated_cost_after_rerouting_usd": self.cost_after,
            "pricing_sources": PRICING_SOURCES,
        }

    def render(self) -> str:
        total = self.total_cost
        lines = [
            f"sessions: {self.sessions}  ·  assistant turns: {self.turns:,}",
            f"estimated cost (list prices): ${total:,.2f}",
        ]
        for t in ("fable", "opus", "sonnet", "haiku"):
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
        if self.duplicate_records_removed or self.synthetic_records_skipped:
            lines += [
                "",
                f"data hygiene: {self.duplicate_records_removed:,} duplicate stream records removed; "
                f"{self.synthetic_records_skipped:,} synthetic records skipped",
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
    messages: dict[str, dict[str, Any]] = {}
    content_seen: dict[str, set[str]] = {}
    contributing_files: set[Path] = set()
    records_scanned = eligible_records = synthetic_records = 0
    for fp in files:
        for sequence, rec in enumerate(_iter_assistant_records(fp)):
            records_scanned += 1
            if on_date is not None and not _on_local_date(rec, on_date, tz):
                continue
            eligible_records += 1
            msg = rec["message"]
            model = str(msg.get("model", ""))
            if model.startswith("<") and model.endswith(">"):
                synthetic_records += 1
                continue
            key = str(msg.get("id") or f"{fp}:{sequence}")
            contributing_files.add(fp)
            if key not in messages:
                messages[key] = {
                    "message": {**msg, "content": []},
                    "timestamp": rec.get("timestamp"),
                }
                content_seen[key] = set()
            aggregate = messages[key]["message"]
            if (msg.get("usage", {}).get("output_tokens", 0) or 0) > (
                aggregate.get("usage", {}).get("output_tokens", 0) or 0
            ):
                aggregate["usage"] = msg["usage"]
            content = msg.get("content")
            if isinstance(content, list):
                for block in content:
                    marker = json.dumps(block, sort_keys=True, ensure_ascii=False)
                    if marker not in content_seen[key]:
                        aggregate["content"].append(block)
                        content_seen[key].add(marker)

    cost_by_tier: dict[str, float] = {}
    tokens_by_tier: dict[str, int] = {}
    mech_turns = 0
    mech_now = mech_cheap = 0.0
    turns = 0
    for rec in messages.values():
        msg = rec["message"]
        usage = msg["usage"]
        model = str(msg.get("model", ""))
        t = tier_of(model)
        c = model_message_cost(model, usage, rec.get("timestamp"))
        cost_by_tier[t] = cost_by_tier.get(t, 0.0) + c
        tokens_by_tier[t] = tokens_by_tier.get(t, 0) + sum(
            usage.get(k, 0) or 0 for k in
            ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
        )
        turns += 1
        if t in ("fable", "opus", "sonnet") and is_mechanical_turn(msg.get("content")):
            mech_turns += 1
            mech_now += c
            mech_cheap += message_cost(cheap_tier, usage)
    return UsageReport(
        sessions=len(contributing_files),
        turns=turns,
        cost_by_tier={k: round(v, 2) for k, v in cost_by_tier.items()},
        tokens_by_tier=tokens_by_tier,
        mechanical_turns=mech_turns,
        mechanical_cost_now=round(mech_now, 2),
        mechanical_cost_cheap=round(mech_cheap, 2),
        cheap_tier=cheap_tier,
        records_scanned=records_scanned,
        duplicate_records_removed=max(0, eligible_records - synthetic_records - len(messages)),
        synthetic_records_skipped=synthetic_records,
    )
