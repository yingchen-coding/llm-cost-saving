"""Cost radar for model routing decisions."""
from __future__ import annotations

from dataclasses import dataclass, field

from .config import Config
from .trace import TraceSummary


@dataclass(frozen=True)
class TaskOverpay:
    task: str
    runs: int
    actual_cost_usd: float
    cheapest_cost_usd: float       # what those runs would have cost on the cheapest capable provider
    overpay_usd: float             # actual - cheapest, i.e. money that bought nothing
    cheapest_provider: str
    mechanical: bool               # a low-difficulty task that should NEVER touch a premium model


@dataclass(frozen=True)
class CostRadar:
    total_estimated_cost_usd: float
    total_runs: int
    average_cost_per_run_usd: float
    cost_by_provider: dict[str, float]
    over_ceiling_providers: list[str]
    budget_warnings: list[str]
    recommendations: list[str]
    overpay_by_task: list[TaskOverpay] = field(default_factory=list)
    mechanical_waste_usd: float = 0.0          # overpay on mechanical tasks — pure waste, always fix
    quality_tradeoff_savings_usd: float = 0.0  # overpay on hard tasks — only fix if cheaper is good enough

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
        if self.mechanical_waste_usd > 0:
            lines.append(
                f"⚠ mechanical_waste: ${self.mechanical_waste_usd:.4f} — low-difficulty work billed to "
                "a premium model. This is pure waste; route it cheaper, always."
            )
        if self.quality_tradeoff_savings_usd > 0:
            lines.append(
                f"possible_savings (quality tradeoff): ${self.quality_tradeoff_savings_usd:.4f} — "
                "harder tasks where a cheaper provider exists; route down only if quality holds."
            )
        if self.overpay_by_task:
            lines.append("overpay_by_task:")
            for o in self.overpay_by_task:
                flag = "  ⚠ MECHANICAL WASTE" if o.mechanical else "  (quality tradeoff)"
                lines.append(
                    f"  {o.task:<12} {o.runs} run(s)  spent ${o.actual_cost_usd:.4f}  "
                    f"vs ${o.cheapest_cost_usd:.4f} on {o.cheapest_provider}  "
                    f"→ overpaid ${o.overpay_usd:.4f}{flag}"
                )
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


def _overpay_by_task(config: Config, summary: TraceSummary) -> list[TaskOverpay]:
    """For each task type in the trace, how much was spent vs the cheapest provider that could have
    done it. Overpay is money that bought nothing — most of all when a *mechanical* task (search,
    scan, count, boilerplate) was billed to a premium model. This is the real cost leak."""
    runs_by_task = summary.runs_by_task or {}
    cost_by_task = summary.cost_by_task or {}
    rows: list[TaskOverpay] = []
    for task, runs in runs_by_task.items():
        if runs <= 0:
            continue
        candidates = config.order_for(None if task == "(none)" else task)
        capable = [name for name in candidates if name in config.providers]
        if not capable:
            continue
        cheapest = min(capable, key=lambda name: config.providers[name].cost_per_run_usd)
        cheapest_total = runs * config.providers[cheapest].cost_per_run_usd
        actual = cost_by_task.get(task, 0.0)
        overpay = round(actual - cheapest_total, 6)
        if overpay <= 0:
            continue
        rows.append(TaskOverpay(
            task=task, runs=runs, actual_cost_usd=round(actual, 6),
            cheapest_cost_usd=round(cheapest_total, 6), overpay_usd=overpay,
            cheapest_provider=cheapest, mechanical=task in config.mechanical_tasks,
        ))
    # biggest leak first; mechanical waste ranks above equal-size non-mechanical overpay
    rows.sort(key=lambda r: (r.mechanical, r.overpay_usd), reverse=True)
    return rows


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

    # The real cost leak: money spent on a pricier provider than the task needed — quantified from
    # the trace, not guessed. Split into MECHANICAL waste (unambiguous: cheap work billed to a
    # premium model — always fix) and a quality tradeoff (a hard task where a cheaper option exists —
    # only fix if quality holds). Conflating the two gives the naive, wrong advice "route reasoning
    # to the cheapest model".
    overpay = _overpay_by_task(config, summary)
    mechanical_waste = round(sum(o.overpay_usd for o in overpay if o.mechanical), 6)
    quality_tradeoff = round(sum(o.overpay_usd for o in overpay if not o.mechanical), 6)
    # Strong, unconditional recommendation only for mechanical waste. Non-mechanical overpay is
    # already covered above by the softer "cheaper provider exists ... when quality allows" note.
    for o in overpay:
        if o.mechanical:
            recommendations.append(
                f"task {o.task!r} is mechanical but ran on a premium provider: overpaid "
                f"${o.overpay_usd:.4f} over {o.runs} run(s). Route it to {o.cheapest_provider} — a "
                "low-difficulty task should never touch a premium model."
            )
    if config.mechanical_tasks and mechanical_waste == 0 and any(
        t in (summary.runs_by_task or {}) for t in config.mechanical_tasks
    ):
        recommendations.append(
            "mechanical_tasks are already routing to the cheapest capable provider — good."
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
        overpay_by_task=overpay,
        mechanical_waste_usd=mechanical_waste,
        quality_tradeoff_savings_usd=quality_tradeoff,
    )
