from broker.config import Config, Provider
from broker.cost import cost_radar
from broker.trace import TraceSummary


def test_cost_radar_flags_ceiling_and_unresolved() -> None:
    config = Config(
        providers={
            "expensive": Provider("expensive", "expensive {prompt}", cost_per_run_usd=0.2),
            "cheap": Provider("cheap", "cheap {prompt}", cost_per_run_usd=0.01),
        },
        default_order=["expensive", "cheap"],
        task_order={"reasoning": ["expensive", "cheap"]},
        max_cost_per_run_usd=0.05,
        cost_strategy="ordered",
    )
    summary = TraceSummary(
        runs=2,
        by_provider={"expensive": 1},
        failovers=1,
        quota_events=0,
        unresolved=1,
        total_seconds=3.0,
        estimated_cost_usd=0.2,
        cost_by_provider={"expensive": 0.2},
    )

    radar = cost_radar(config, summary)

    assert radar.average_cost_per_run_usd == 0.1
    assert radar.over_ceiling_providers == ["expensive"]
    assert any("average run cost" in warning for warning in radar.budget_warnings)
    assert any("cheap is cheaper" in recommendation for recommendation in radar.recommendations)
    assert any("unresolved" in recommendation for recommendation in radar.recommendations)


def _tiered_config() -> Config:
    return Config(
        providers={
            "opus": Provider("opus", "opus {prompt}", strengths=["reasoning"], cost_per_run_usd=0.075),
            "haiku": Provider("haiku", "haiku {prompt}", strengths=["search", "scan"], cost_per_run_usd=0.004),
        },
        default_order=["opus", "haiku"],
        task_order={"reasoning": ["opus", "haiku"], "search": ["haiku", "opus"]},
        cost_strategy="ordered",
        mechanical_tasks=["search", "scan", "count"],
    )


def test_mechanical_task_routes_cheapest_regardless_of_order() -> None:
    # A mechanical task must go to the cheapest capable provider even if the configured order and
    # cost_strategy would send it to the premium one — this is the guard against paying premium for
    # low-difficulty work.
    cfg = _tiered_config()
    # configured order for 'scan' is not set → default ["opus","haiku"]; mechanical guard flips it
    assert cfg.optimized_order_for("scan")[0] == "haiku"
    # a non-mechanical task keeps its configured order
    assert cfg.optimized_order_for("reasoning")[0] == "opus"


def test_overpay_separates_mechanical_waste_from_quality_tradeoff() -> None:
    cfg = _tiered_config()
    # 10 search runs (mechanical) + 4 reasoning runs, all billed to opus at 0.075
    summary = TraceSummary(
        runs=14, by_provider={"opus": 14}, failovers=0, quota_events=0, unresolved=0,
        total_seconds=0.0, estimated_cost_usd=14 * 0.075, cost_by_provider={"opus": 14 * 0.075},
        runs_by_task={"search": 10, "reasoning": 4},
        cost_by_task={"search": round(10 * 0.075, 6), "reasoning": round(4 * 0.075, 6)},
    )
    radar = cost_radar(cfg, summary)

    # search: mechanical waste = 10*(0.075-0.004) = 0.71
    assert round(radar.mechanical_waste_usd, 4) == 0.71
    # reasoning: quality tradeoff = 4*(0.075-0.004) = 0.284 (NOT counted as waste)
    assert round(radar.quality_tradeoff_savings_usd, 4) == 0.284
    tasks = {o.task: o for o in radar.overpay_by_task}
    assert tasks["search"].mechanical is True
    assert tasks["reasoning"].mechanical is False
    # strong advice only for the mechanical task; reasoning must NOT get "route it to haiku" waste advice
    assert any("mechanical but ran on a premium" in r and "search" in r for r in radar.recommendations)
    assert not any("reasoning" in r and "should never touch" in r for r in radar.recommendations)


def test_no_overpay_when_mechanical_already_cheapest() -> None:
    cfg = _tiered_config()
    summary = TraceSummary(
        runs=5, by_provider={"haiku": 5}, failovers=0, quota_events=0, unresolved=0,
        total_seconds=0.0, estimated_cost_usd=5 * 0.004, cost_by_provider={"haiku": 5 * 0.004},
        runs_by_task={"search": 5}, cost_by_task={"search": round(5 * 0.004, 6)},
    )
    radar = cost_radar(cfg, summary)
    assert radar.mechanical_waste_usd == 0.0
    assert any("already routing to the cheapest" in r for r in radar.recommendations)
