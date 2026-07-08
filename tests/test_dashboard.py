"""The HTML dashboard renders self-contained and reflects the trace analysis."""
import json

from broker.config import Config, Provider
from broker.dashboard import render_html, write_dashboard


def _cfg() -> Config:
    return Config(
        providers={"opus": Provider("opus", "opus {prompt}", strengths=["reasoning"], cost_per_run_usd=0.075),
                   "haiku": Provider("haiku", "haiku {prompt}", strengths=["search"], cost_per_run_usd=0.004)},
        default_order=["opus", "haiku"],
        task_order={"search": ["haiku", "opus"], "reasoning": ["opus", "haiku"]},
        mechanical_tasks=["search"],
    )


def _trace(tmp_path):
    rows = [{"task": "search", "provider": "opus", "estimated_cost_usd": 0.075, "attempts": []}] * 5
    rows += [{"task": "reasoning", "provider": "opus", "estimated_cost_usd": 0.075, "attempts": []}] * 2
    p = tmp_path / ".broker-trace.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows))
    return p


def test_render_html_self_contained_with_data(tmp_path):
    html = render_html(_cfg(), _trace(tmp_path))
    # no external resources — a real dashboard must open offline
    assert 'src="http' not in html and 'href="http' not in html
    assert "<!doctype html>" in html.lower()
    for section in ("modelbroker dashboard", "Spend by provider", "Overpay by task", "Quota pressure"):
        assert section in html
    assert "opus" in html
    # the mechanical search overpay must surface as waste
    assert "mechanical waste" in html


def test_render_html_empty_trace_is_graceful(tmp_path):
    html = render_html(_cfg(), tmp_path / "missing.jsonl")
    assert "no cost recorded yet" in html
    assert "no quota data yet" in html


def test_write_dashboard_creates_file(tmp_path):
    out = write_dashboard(_cfg(), _trace(tmp_path), tmp_path / "d.html")
    assert out.exists() and out.read_text().startswith("<!doctype html>")


def test_render_html_usage_panel_no_duplicate_total(tmp_path):
    # The usage panel must show total_spend, mechanical_waste, after_rerouting, turns — not
    # two cards both showing the same total ("total" and "before" were identical in the old bug).
    import json
    transcript = tmp_path / "session.jsonl"
    rec = {"message": {"role": "assistant", "model": "claude-opus-4",
                        "content": [{"type": "tool_use", "name": "Grep", "input": {"command": "grep foo"}}],
                        "usage": {"input_tokens": 100, "output_tokens": 20,
                                  "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}},
           "timestamp": "2026-01-01T12:00:00Z"}
    transcript.write_text(json.dumps(rec) + "\n", encoding="utf-8")
    html = render_html(_cfg(), tmp_path / "missing.jsonl",
                       usage=__import__("broker.usage", fromlist=["analyze"]).analyze([transcript]))
    # "before" was the duplicate card label — must not appear, "total spend" and "after rerouting" must
    assert "total spend" in html
    assert "after rerouting" in html
    assert "turns analyzed" in html
    # old duplicate label must be gone
    assert ">before<" not in html
