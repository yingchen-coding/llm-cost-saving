"""Token-cost + mechanical-waste estimation from transcripts."""
import json

from broker.usage import analyze, is_mechanical_turn, message_cost, tier_of


def test_tier_and_cost():
    assert tier_of("claude-opus-4-8") == "opus"
    assert tier_of("claude-haiku-4-5") == "haiku"
    assert tier_of("claude-sonnet-4-6") == "sonnet"
    # 1M output tokens on opus = $75
    assert round(message_cost("opus", {"output_tokens": 1_000_000})) == 75


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


def test_analyze_end_to_end(tmp_path):
    # one opus mechanical turn (search) + one opus reasoning turn
    rows = [
        {"message": {"role": "assistant", "model": "claude-opus-4-8",
                     "usage": {"input_tokens": 100, "output_tokens": 100},
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


def test_usage_cli_errors_on_missing_path(capsys):
    from broker.cli import main
    rc = main(["usage", "/no/such/path/xyz.jsonl"])
    assert rc == 2
    assert "no such path" in capsys.readouterr().err
