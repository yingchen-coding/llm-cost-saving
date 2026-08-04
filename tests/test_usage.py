"""Token-cost + mechanical-waste estimation from transcripts."""
import json
import math
from datetime import UTC

from broker.usage import _cost, analyze, is_mechanical_turn, message_cost, prices_for_model, tier_of


def test_tier_and_cost():
    assert tier_of("claude-opus-4-8") == "opus"
    assert tier_of("claude-haiku-4-5") == "haiku"
    assert tier_of("claude-sonnet-4-6") == "sonnet"
    # Current Opus list price is $25/MTok output.
    assert round(message_cost("opus", {"output_tokens": 1_000_000})) == 25
    assert prices_for_model("claude-fable-5") == (10.0, 50.0)
    assert prices_for_model("claude-opus-4-8") == (5.0, 25.0)
    assert prices_for_model("claude-sonnet-5", "2026-07-22T00:00:00Z") == (2.0, 10.0)
    assert prices_for_model("claude-sonnet-5", "2026-09-01T00:00:00Z") == (3.0, 15.0)


def test_is_mechanical_turn():
    mech = [{"type": "tool_use", "name": "Grep", "input": {"pattern": "x"}},
            {"type": "tool_use", "name": "Read", "input": {}}]
    assert is_mechanical_turn(mech) is True
    reasoning = [{"type": "text", "text": "Here is the design tradeoff analysis. " * 40}]
    assert is_mechanical_turn(reasoning) is False
    bash_mech = [{"type": "tool_use", "name": "Bash", "input": {"command": "grep -r foo ."}}]
    assert is_mechanical_turn(bash_mech) is True
    bash_real = [{"type": "tool_use", "name": "Bash", "input": {"command": "python train.py"}}]
    assert is_mechanical_turn(bash_real) is False
    # "LS" is not a real Claude Code tool — listing goes through Bash; must not count as mechanical
    ls_tool = [{"type": "tool_use", "name": "LS", "input": {}}]
    assert is_mechanical_turn(ls_tool) is False


def test_analyze_end_to_end(tmp_path):
    # one opus mechanical turn (search) + one opus reasoning turn
    rows = [
        {"message": {"role": "assistant", "model": "claude-opus-4-8",
                     "usage": {"input_tokens": 100_000, "output_tokens": 100_000},
                     "content": [{"type": "tool_use", "name": "Grep", "input": {"pattern": "x"}}]}},
        {"message": {"role": "assistant", "model": "claude-opus-4-8",
                     "usage": {"input_tokens": 100, "output_tokens": 5000},
                     "content": [{"type": "text", "text": "long reasoning " * 50}]}},
    ]
    f = tmp_path / "session.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in rows))
    rep = analyze([tmp_path], cheap_tier="haiku")
    assert rep.turns == 2
    assert rep.mechanical_turns == 1          # only the Grep turn
    assert rep.total_cost > 0
    assert rep.recoverable > 0                # opus search -> haiku saves money
    assert rep.cost_after < rep.total_cost


def test_analyze_deduplicates_stream_blocks_and_skips_synthetic(tmp_path):
    usage = {"input_tokens": 100, "output_tokens": 200}
    rows = [
        {"uuid": "one", "message": {"id": "msg-1", "role": "assistant", "model": "claude-opus-4-8",
         "usage": usage, "content": [{"type": "tool_use", "name": "Grep", "input": {}}]}},
        {"uuid": "two", "message": {"id": "msg-1", "role": "assistant", "model": "claude-opus-4-8",
         "usage": usage, "content": [{"type": "tool_use", "name": "Read", "input": {}}]}},
        {"uuid": "three", "message": {"id": "msg-2", "role": "assistant", "model": "<synthetic>",
         "usage": usage, "content": [{"type": "text", "text": "fixture"}]}},
    ]
    (tmp_path / "stream.jsonl").write_text("\n".join(json.dumps(row) for row in rows))
    report = analyze([tmp_path])
    assert report.turns == 1
    assert report.mechanical_turns == 1
    assert report.duplicate_records_removed == 1
    assert report.synthetic_records_skipped == 1


def test_one_hour_cache_writes_use_two_times_input_price():
    usage = {
        "cache_creation_input_tokens": 1_000_000,
        "cache_creation": {"ephemeral_1h_input_tokens": 1_000_000, "ephemeral_5m_input_tokens": 0},
    }
    assert message_cost("haiku", usage) == 2.0


def test_usage_cli_errors_on_missing_path(capsys):
    from broker.cli import main
    rc = main(["usage", "/no/such/path/xyz.jsonl"])
    assert rc == 2
    assert "no such path" in capsys.readouterr().err


def test_usage_today_filter(tmp_path):
    from datetime import date, datetime
    today = datetime.now(UTC).isoformat()
    old = "2020-01-01T00:00:00Z"
    rows = [
        {"timestamp": today, "message": {"role": "assistant", "model": "claude-opus-4-8",
                                         "usage": {"output_tokens": 1000}}},
        {"timestamp": old, "message": {"role": "assistant", "model": "claude-opus-4-8",
                                       "usage": {"output_tokens": 999999}}},
    ]
    f = tmp_path / "s.jsonl"
    import json
    f.write_text("\n".join(json.dumps(r) for r in rows))
    all_rep = analyze([tmp_path])
    today_rep = analyze([tmp_path], on_date=date.today())
    assert all_rep.turns == 2
    assert today_rep.turns == 1                       # only today's turn
    assert today_rep.total_cost < all_rep.total_cost  # the big old turn is excluded


def test_usage_cli_threshold_exit(tmp_path, capsys):
    import json

    from broker.cli import main
    f = tmp_path / "s.jsonl"
    f.write_text(json.dumps({"message": {"role": "assistant", "model": "claude-opus-4-8",
                                         "usage": {"output_tokens": 1_000_000}}}))
    assert main(["usage", str(f), "--threshold", "10"]) == 2      # $25 > $10
    assert "OVER" in capsys.readouterr().err
    assert main(["usage", str(f), "--threshold", "1000"]) == 0    # under
    capsys.readouterr()

    assert main(["usage", str(f), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["assistant_turns"] == 1
    assert payload["method"].startswith("API list-price estimate")
    assert "pricing_sources" in payload


def test_cost_tolerates_malformed_token_fields():
    """Real agent-CLI transcripts occasionally carry a corrupted usage field — a string count from a
    buggy provider, a negative correction, or a NaN. One bad field must not crash `broker usage` or
    poison the cost total (NaN propagates through every sum it touches); it should be treated as 0,
    same grace runtime.py's `_num` already gives malformed trace fields."""
    prices = (3.0, 15.0)
    # non-numeric token count must not raise
    assert _cost(prices, {"input_tokens": "not-a-number", "output_tokens": 200}) == round(200 * 15 / 1_000_000, 10)
    # a negative token count (corrupted/adjusted record) must not go negative or crash
    assert _cost(prices, {"input_tokens": -500_000, "output_tokens": 100}) >= 0
    # NaN/inf must not poison the result
    assert math.isfinite(_cost(prices, {"input_tokens": float("nan"), "output_tokens": 100}))
    assert math.isfinite(_cost(prices, {"input_tokens": float("inf"), "output_tokens": 100}))


def test_analyze_end_to_end_survives_one_malformed_usage_record(tmp_path):
    """A single transcript line with a malformed usage field (e.g. a stringified token count from a
    buggy provider) must not take down the whole `broker usage` report — the other, well-formed
    turns in the same file still get costed."""
    rows = [
        {"message": {"role": "assistant", "model": "claude-opus-4-8",
                     "usage": {"input_tokens": 100, "output_tokens": 200}}},
        {"message": {"role": "assistant", "model": "claude-opus-4-8",
                     "usage": {"input_tokens": "500", "output_tokens": 200}}},
    ]
    f = tmp_path / "session.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in rows))
    rep = analyze([tmp_path])  # must not raise
    assert rep.turns == 2
    assert rep.total_cost > 0


def test_analyze_dedup_survives_malformed_output_tokens(tmp_path):
    """The streaming-dedup comparison keeps whichever re-emitted chunk has the higher
    output_tokens; a malformed count there (str vs int) used to raise TypeError before the
    two chunks ever reached _cost(). Same message id as the stream-dedup fixture above."""
    rows = [
        {"uuid": "one", "message": {"id": "msg-1", "role": "assistant", "model": "claude-opus-4-8",
         "usage": {"input_tokens": 100, "output_tokens": "not-a-number"},
         "content": [{"type": "tool_use", "name": "Grep", "input": {}}]}},
        {"uuid": "two", "message": {"id": "msg-1", "role": "assistant", "model": "claude-opus-4-8",
         "usage": {"input_tokens": 100, "output_tokens": 200},
         "content": [{"type": "tool_use", "name": "Read", "input": {}}]}},
    ]
    f = tmp_path / "stream.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in rows))
    rep = analyze([tmp_path])  # must not raise
    assert rep.turns == 1
    assert rep.total_cost > 0
