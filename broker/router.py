"""Decide which provider a task should go to, given the routing policy and live cooldown state."""
from __future__ import annotations

from dataclasses import dataclass

from .config import Config
from .state import State


@dataclass
class Plan:
    task: str | None
    order: list[str]              # the routing candidate order (task override or default)
    available: list[str]          # of those, the ones not currently cooled down (in order)
    chosen: str | None            # first available, or None if all are cooled down
    soonest: str | None           # if all cooled: the provider that frees up first
    soonest_eta: float            # seconds until `soonest` is available


def plan(config: Config, state: State, task: str | None, now: float) -> Plan:
    order = [
        n
        for n in config.optimized_order_for(task)
        if n in config.providers and config.within_cost_ceiling(n)
    ]
    available = [n for n in order if state.get(n).available(now)]
    chosen = available[0] if available else None

    soonest: str | None = None
    soonest_eta = 0.0
    if not available and order:
        soonest = min(order, key=lambda n: state.get(n).cooldown_until)
        soonest_eta = state.get(soonest).cooldown_remaining(now)

    return Plan(task=task, order=order, available=available, chosen=chosen,
                soonest=soonest, soonest_eta=soonest_eta)
