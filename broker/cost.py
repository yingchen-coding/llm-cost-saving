"""Cost radar for model routing decisions."""
from __future__ import annotations

from dataclasses import dataclass

from .config import Config
from .trace import TraceSummary


@dataclass(frozen=True)
class CostRadar:
    total_estimated_cost_usd: float
    total_runs: int
    average_cost_per_run_usd: float
    cost_by_provider: dict[str, float]
    over_ceiling_providers: list[str]
    budget_warnings: list[str]
    recommendations: list[str]

    def render(self) -> str:
        lines = [
            f"runs: {self.total_runs}",
            f"estimated_cost: ${self.total_estimated_cost_usd:.4f}",
            f"average_cost_per_run: ${self.average_cost_per_run_usd:.4f}",
        ]
        if self.cost_by_provider:
            lines.append("by_provider:")
            for provider, cost in sorted(self.cost_by_provider.items(), key=lambda item: -item[1]):
                lines.append(f"  {provider:<12} ${cost:.4f}")
        if self.over_ceiling_providers:
            lines.append("over_ceiling:")
            for provider in self.over_ceiling_providers:
                lines.append(f"  {provider}")
        if self.budget_warnings:
            lines.append("budget_warnings:")
            for warning in self.budget_warnings:
                lines.append(f"  {warning}")
        if self.recommendations:
            lines.append("recommendations:")
            for recommendation in self.recommendations:
                lines.append(f"  {recommendation}")
        return "\n".join(lines)


def _cheapest_provider(config: Config, candidates: list[str]) -> str | None:
    available = [name for name in candidates if name in config.providers]
    if not available:
        return None
    return min(available, key=lambda name: config.providers[name].cost_per_run_usd)


def cost_radar(config: Config, summary: TraceSummary) -> CostRadar:
    cost_by_provider = summary.cost_by_provider or {}
    total = summary.estimated_cost_usd
    average = total / summary.runs if summary.runs else 0.0
    over_ceiling = [
        name
        for name, provider in sorted(config.providers.items())
        if config.max_cost_per_run_usd > 0
        and provider.cost_per_run_usd > config.max_cost_per_run_usd
    ]

    budget_warnings: list[str] = []
    if config.max_cost_per_run_usd > 0 and average > config.max_cost_per_run_usd:
        budget_warnings.append(
            f"average run cost ${average:.4f} exceeds per-run ceiling "
            f"${config.max_cost_per_run_usd:.4f}"
        )

    recommendations: list[str] = []
    if config.cost_strategy == "ordered":
        recommendations.append(
            "set [budget].cost_strategy = \"balanced\" to keep task fit while preferring cheaper "
            "comparable providers"
        )
    for task, order in sorted(config.task_order.items()):
        cheapest = _cheapest_provider(config, order)
        if not cheapest or not order:
            continue
        first = order[0]
        if cheapest != first:
            first_cost = config.providers[first].cost_per_run_usd
            cheap_cost = config.providers[cheapest].cost_per_run_usd
            if first_cost > cheap_cost:
                recommendations.append(
                    f"task {task!r}: {cheapest} is cheaper than first-choice {first} "
                    f"(${cheap_cost:.4f} vs ${first_cost:.4f}); use balanced/cheapest when quality "
                    "allows"
                )

    if summary.failovers:
        recommendations.append(
            f"{summary.failovers} traced run(s) failed over; review provider order and quota windows"
        )
    if summary.unresolved:
        recommendations.append(
            f"{summary.unresolved} traced run(s) were unresolved; add a fallback provider or relax "
            "cost ceilings for critical tasks"
        )

    return CostRadar(
        total_estimated_cost_usd=total,
        total_runs=summary.runs,
        average_cost_per_run_usd=round(average, 6),
        cost_by_provider=cost_by_provider,
        over_ceiling_providers=over_ceiling,
        budget_warnings=budget_warnings,
        recommendations=recommendations,
    )
