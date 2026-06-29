"""Quota and reliability pressure report from broker traces."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProviderQuota:
    attempts: int = 0
    handled: int = 0
    quota_hits: int = 0
    unavailable: int = 0
    transient: int = 0
    refusals: int = 0

    @property
    def quota_hit_rate(self) -> float:
        return _ratio(self.quota_hits, self.attempts)

    @property
    def failure_pressure(self) -> float:
        return _ratio(
            self.quota_hits + self.unavailable + self.transient + self.refusals,
            self.attempts,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempts": self.attempts,
            "handled": self.handled,
            "quota_hits": self.quota_hits,
            "unavailable": self.unavailable,
            "transient": self.transient,
            "refusals": self.refusals,
            "quota_hit_rate": self.quota_hit_rate,
            "failure_pressure": self.failure_pressure,
            "recommendation": provider_recommendation(self),
        }


@dataclass(frozen=True)
class QuotaReport:
    runs: int
    unresolved: int
    failover_runs: int
    providers: dict[str, ProviderQuota]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "runs": self.runs,
            "unresolved": self.unresolved,
            "failover_runs": self.failover_runs,
            "providers": {name: row.to_dict() for name, row in sorted(self.providers.items())},
            "warnings": self.warnings,
        }

    def render(self) -> str:
        if self.runs == 0:
            return "no quota traces yet"
        lines = [
            f"runs: {self.runs}",
            f"failover_runs: {self.failover_runs}",
            f"unresolved: {self.unresolved}",
            "providers:",
        ]
        for provider, row in sorted(
            self.providers.items(),
            key=lambda item: (-item[1].failure_pressure, item[0]),
        ):
            lines.append(
                f"  {provider:<12} attempts={row.attempts} handled={row.handled} "
                f"quota_hits={row.quota_hits} quota_rate={row.quota_hit_rate:.1%} "
                f"pressure={row.failure_pressure:.1%} :: {provider_recommendation(row)}"
            )
        if self.warnings:
            lines.append("warnings:")
            lines.extend(f"  {warning}" for warning in self.warnings)
        return "\n".join(lines)


def quota_report(path: str | Path) -> QuotaReport:
    rows = _load_rows(Path(path))
    providers: dict[str, dict[str, int]] = {}
    unresolved = 0
    failover_runs = 0

    for row in rows:
        if row.get("provider") is None:
            unresolved += 1
        handled = row.get("provider")
        if handled:
            bucket = providers.setdefault(str(handled), _empty())
            bucket["handled"] += 1
        attempts = row.get("attempts") or []
        run_failed_over = False
        if isinstance(attempts, list):
            for attempt in attempts:
                if not isinstance(attempt, dict):
                    continue
                provider = str(attempt.get("provider") or row.get("provider") or "unknown")
                bucket = providers.setdefault(provider, _empty())
                bucket["attempts"] += 1
                for key in ("quota_hit", "unavailable", "transient", "refusal"):
                    if attempt.get(key):
                        bucket[_bucket_key(key)] += 1
                        run_failed_over = True
        if run_failed_over:
            failover_runs += 1

    report_rows = {
        name: ProviderQuota(
            attempts=value["attempts"],
            handled=value["handled"],
            quota_hits=value["quota_hits"],
            unavailable=value["unavailable"],
            transient=value["transient"],
            refusals=value["refusals"],
        )
        for name, value in providers.items()
    }
    warnings = []
    if rows and not providers:
        warnings.append("Trace has no attempt/provider fields; quota reliability cannot be measured.")
    for name, provider_row in sorted(report_rows.items()):
        if provider_row.quota_hit_rate >= 0.3:
            warnings.append(f"{name} quota hit rate is high; lower its route priority or add fallback.")
        if provider_row.failure_pressure >= 0.5:
            warnings.append(f"{name} failure pressure is high; do not rely on it as the only route.")
    if unresolved:
        warnings.append("Some runs exhausted all providers; add a fallback or reduce quota-heavy tasks.")
    return QuotaReport(
        runs=len(rows),
        unresolved=unresolved,
        failover_runs=failover_runs,
        providers=report_rows,
        warnings=warnings,
    )


def provider_recommendation(row: ProviderQuota) -> str:
    if row.attempts == 0 and row.handled:
        return "handled runs but trace lacks attempt detail"
    if row.failure_pressure >= 0.5:
        return "demote or keep behind a fallback until reliability improves"
    if row.quota_hit_rate >= 0.3:
        return "keep as fallback; quota is too volatile for primary routing"
    if row.unavailable or row.transient:
        return "usable with fallback; investigate local/provider failures"
    if row.refusals:
        return "usable with policy-aware fallback"
    return "healthy"


def _load_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _empty() -> dict[str, int]:
    return {
        "attempts": 0,
        "handled": 0,
        "quota_hits": 0,
        "unavailable": 0,
        "transient": 0,
        "refusals": 0,
    }


def _bucket_key(key: str) -> str:
    return {
        "quota_hit": "quota_hits",
        "unavailable": "unavailable",
        "transient": "transient",
        "refusal": "refusals",
    }[key]


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)
