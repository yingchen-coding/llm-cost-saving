"""Coverage for the CLI layer, the real subprocess executor, multi-provider failover, and the
quota-marker matcher — the surfaces test_broker.py doesn't reach."""


from broker import cli
from broker import config as cfgmod
from broker import state as statemod
from broker.config import Provider
from broker.runner import _argv_and_stdin, _subprocess_executor, run_task

THREE = """\
[providers.claude]
command = "claude -p {prompt}"
strengths = ["reasoning"]
reset = "5h"
quota_markers = ["usage limit"]
[providers.codex]
command = "codex exec {prompt}"
strengths = ["codegen"]
reset = "1h"
quota_markers = ["rate limit"]
[providers.gemini]
command = "gemini {prompt}"
strengths = ["long-context"]
reset = "30m"
quota_markers = ["quota"]
[routing]
default = ["claude", "codex", "gemini"]
"""


def _write_cfg(tmp_path, body):
    p = tmp_path / "broker.toml"
    p.write_text(body)
    return p


# ---- CLI ----

def test_cli_init_then_route_status(tmp_path, capsys):
    cfg = tmp_path / "broker.toml"
    assert cli.main(["-c", str(cfg), "init"]) == 0
    assert cfg.exists()
    # init is idempotent-guarded: a second init refuses rather than clobbering
    assert cli.main(["-c", str(cfg), "init"]) == 2

    assert cli.main(["-c", str(cfg), "route", "-t", "codegen"]) == 0
    assert "codex" in capsys.readouterr().out  # codegen routes to codex first

    assert cli.main(["-c", str(cfg), "status"]) == 0
    out = capsys.readouterr().out
    assert "claude" in out and "available" in out


def test_cli_run_uses_executor(monkeypatch, tmp_path, capsys):
    cfg = _write_cfg(tmp_path, THREE)
    monkeypatch.chdir(tmp_path)  # the run-state file is written relative to cwd
    monkeypatch.setattr("broker.runner.subprocess.run", _fake_run({"claude": (0, "hi from claude")}))
    assert cli.main(["-c", str(cfg), "run", "-t", "reasoning", "hello"]) == 0
    assert "hi from claude" in capsys.readouterr().out


def test_cli_missing_config_is_clean_error(tmp_path, capsys):
    missing = tmp_path / "nope.toml"
    assert cli.main(["-c", str(missing), "route"]) == 2
    assert "broker:" in capsys.readouterr().err


# ---- real subprocess executor ----

def test_executor_command_not_found():
    code, out = _subprocess_executor(None)(["definitely-not-a-real-cmd-xyz"], None)
    assert code == 127 and "not found" in out


def test_executor_runs_real_command():
    code, out = _subprocess_executor(None)(["printf", "hello"], None)
    assert code == 0 and out == "hello"


def test_executor_timeout():
    code, out = _subprocess_executor(0.05)(["sleep", "5"], None)
    assert code == 124 and out == "timeout"


# ---- argv building ----

def test_argv_token_substitution_and_stdin_fallback():
    p_tok = Provider(name="x", command="claude -p {prompt}")
    assert _argv_and_stdin(p_tok, "hi there") == (["claude", "-p", "hi there"], None)
    p_pipe = Provider(name="y", command="codex exec")
    assert _argv_and_stdin(p_pipe, "hi") == (["codex", "exec"], "hi")  # no token → stdin


# ---- 3-provider chain ----

def _fake_run(by_first_arg):
    """Return a fake subprocess.run that keys behavior off argv[0] -> (returncode, combined)."""
    class _Proc:
        def __init__(self, code, text):
            self.returncode, self.stdout, self.stderr = code, text, ""

    def runner(argv, **kwargs):
        code, text = by_first_arg.get(argv[0], (0, "ok"))
        return _Proc(code, text)

    return runner


def test_failover_chains_through_three(monkeypatch, tmp_path):
    cfg = cfgmod.load(_write_cfg(tmp_path, THREE))
    state = statemod.State(path=tmp_path / "s.json")
    monkeypatch.setattr(
        "broker.runner.subprocess.run",
        _fake_run({"claude": (1, "usage limit hit"), "codex": (1, "rate limit"), "gemini": (0, "gemini did it")}),
    )
    r = run_task(cfg, state, "go", now_fn=lambda: 1000.0)
    assert [a.provider for a in r.attempts] == ["claude", "codex", "gemini"]
    assert r.provider == "gemini"
    assert state.get("claude").cooldown_remaining(1000.0) == 5 * 3600
    assert state.get("codex").cooldown_remaining(1000.0) == 3600


# ---- quota matcher + now snapshot ----

def test_empty_prompt_spends_no_provider_call(tmp_path):
    cfg = cfgmod.load(_write_cfg(tmp_path, THREE))
    state = statemod.State(path=tmp_path / "s.json")
    called = []
    r = run_task(cfg, state, "   \n", executor=lambda a, s: called.append(a) or (0, "x"),
                 now_fn=lambda: 1.0)
    assert r.provider is None and r.exit_code == 2 and called == []   # no provider invoked


def test_matches_quota_error_is_case_insensitive():
    p = Provider(name="x", command="c", quota_markers=["Usage Limit", "429"])
    assert p.matches_quota_error("ERROR: usage LIMIT reached") is True
    assert p.matches_quota_error("got a 429 back") is True
    assert p.matches_quota_error("all good") is False


def test_now_snapshotted_once_per_run(tmp_path):
    """run_task must take a single timestamp; a now_fn that changes each call would otherwise make
    the cooldown-write and the availability-check disagree."""
    cfg = cfgmod.load(_write_cfg(tmp_path, THREE))
    state = statemod.State(path=tmp_path / "s.json")
    ticks = iter([1000.0, 2000.0, 3000.0, 4000.0, 5000.0])
    # output contains every provider's marker so all three recognize quota and fail over
    r = run_task(cfg, state, "x", task="reasoning",
                 executor=lambda a, s: (1, "usage limit / rate limit / quota"),
                 now_fn=lambda: next(ticks))
    # claude cooled to base+5h using the SAME base as codex's base+1h (single snapshot)
    base = state.get("claude").cooldown_until - 5 * 3600
    assert state.get("codex").cooldown_until == base + 3600
    assert state.get("gemini").cooldown_until == base + 1800
    assert r.exhausted is True
