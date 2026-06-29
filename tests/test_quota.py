from broker import cli
from broker.quota import quota_report
from broker.trace import append


def test_quota_report_finds_provider_pressure(tmp_path):
    trace = tmp_path / ".broker-trace.jsonl"
    append(
        trace,
        {
            "provider": "codex",
            "attempts": [
                {"provider": "claude", "quota_hit": True},
                {"provider": "codex", "quota_hit": False},
            ],
        },
    )
    append(
        trace,
        {
            "provider": None,
            "attempts": [
                {"provider": "claude", "quota_hit": True},
                {"provider": "codex", "transient": True},
            ],
        },
    )

    report = quota_report(trace)

    assert report.runs == 2
    assert report.unresolved == 1
    assert report.failover_runs == 2
    assert report.providers["claude"].quota_hit_rate == 1.0
    assert report.providers["codex"].handled == 1
    assert "demote" in report.providers["claude"].to_dict()["recommendation"]
    assert any("exhausted all providers" in warning for warning in report.warnings)


def test_quota_report_handles_missing_trace(tmp_path):
    report = quota_report(tmp_path / "missing.jsonl")

    assert report.runs == 0
    assert report.render() == "no quota traces yet"


def test_cli_quota_reads_trace_next_to_state_file(tmp_path, monkeypatch, capsys):
    cfg = tmp_path / "broker.toml"
    cfg.write_text(
        """\
[budget]
state_file = "state.json"
[providers.codex]
command = "codex {prompt}"
reset = "1h"
[routing]
default = ["codex"]
""",
        encoding="utf-8",
    )
    append(
        tmp_path / ".broker-trace.jsonl",
        {
            "provider": None,
            "attempts": [{"provider": "codex", "quota_hit": True}],
        },
    )
    monkeypatch.chdir(tmp_path)

    assert cli.main(["-c", str(cfg), "quota"]) == 0
    out = capsys.readouterr().out
    assert "quota_hits=1" in out
    assert "codex quota hit rate is high" in out
