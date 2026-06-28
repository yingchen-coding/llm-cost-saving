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
