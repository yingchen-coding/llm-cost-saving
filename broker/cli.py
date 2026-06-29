"""Command-line interface for modelbroker."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from . import config as cfgmod
from . import state as statemod
from . import trace as tracemod
from .config import ConfigError
from .cost import cost_radar
from .evidence import (
    DEFAULT_EVIDENCE,
    EvidenceError,
    add_incident,
    add_model,
)
from .evidence import (
    load as load_evidence,
)
from .evidence import (
    save as save_evidence,
)
from .quota import quota_report
from .router import plan
from .runner import probe_provider, run_task
from .runtime import runtime_report
from .skills import apply_skills, get_skill, skill_names

_DEFAULT_TOML = """\
# modelbroker config — quota-aware multi-model routing.
[budget]
state_file = ".broker-state.json"
max_cost_per_run_usd = 0.0           # 0 disables per-run cost filtering
cost_strategy = "ordered"            # ordered | cheapest | balanced

# A {prompt} token in `command` is replaced with the prompt as one argument (no shell).
[providers.claude]
command = "claude -p {prompt}"
strengths = ["reasoning", "architecture", "refactor", "debugging", "writing", "review"]
reset = "5h"                       # cool-down when Claude hits its usage limit
quota_markers = ["usage limit", "rate limit", "429", "quota", "resets at", "too many requests", "exceeded"]
cost_per_run_usd = 0.0              # optional local estimate used by `broker trace`

[providers.codex]
command = "codex exec --skip-git-repo-check {prompt}"
strengths = ["codegen", "boilerplate", "tests", "quick-edit", "scripts"]
reset = "1h"
quota_markers = ["rate limit", "429", "quota", "usage limit", "too many requests", "exceeded"]
cost_per_run_usd = 0.0

[routing]
default = ["claude", "codex"]      # global fail-over order

[routing.tasks]                    # route by task to the model that's strongest at it
codegen = ["codex", "claude"]
boilerplate = ["codex", "claude"]
tests = ["codex", "claude"]
reasoning = ["claude", "codex"]
architecture = ["claude", "codex"]
refactor = ["claude", "codex"]
review = ["claude", "codex"]
writing = ["claude", "codex"]
debugging = ["claude", "codex"]
"""


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="broker", description="Quota-aware multi-model task router.")
    p.add_argument("--version", action="version", version=f"modelbroker {__version__}")
    p.add_argument("-c", "--config", default=cfgmod.DEFAULT_CONFIG, help="path to broker.toml")
    # Accept -c AFTER the subcommand too (`broker run -c X`), not just before it. SUPPRESS default so
    # a subcommand only overrides the global value when -c is explicitly given — never resets it.
    cfg_after = argparse.ArgumentParser(add_help=False)
    cfg_after.add_argument("-c", "--config", default=argparse.SUPPRESS, help="path to broker.toml")
    sub = p.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", parents=[cfg_after],
                         help="run a prompt on the strongest available model (with fail-over)")
    run.add_argument("prompt", help="the prompt / task text")
    run.add_argument("-t", "--task", default=None, help="task type (codegen, reasoning, tests, ...)")
    run.add_argument("--skill", action="append", choices=skill_names(),
                     help="apply a prompt skill before routing; may be repeated")
    run.add_argument("--timeout", type=float, default=None, help="per-provider timeout (seconds)")

    route = sub.add_parser("route", parents=[cfg_after],
                           help="show which model a task would go to (no execution)")
    route.add_argument("-t", "--task", default=None)

    sub.add_parser("status", parents=[cfg_after],
                   help="show each provider's availability / cooldown / usage")
    sub.add_parser("doctor", parents=[cfg_after],
                   help="check each provider's CLI is installed/on PATH (no prompt run)")
    sub.add_parser("trace", parents=[cfg_after],
                   help="summarize the run trace (routing, failovers, quota events, time)")
    sub.add_parser("cost", parents=[cfg_after],
                   help="show cost radar and routing optimization recommendations")
    sub.add_parser("runtime", parents=[cfg_after],
                   help="show token throughput, cost/hour, and runtime reliability from traces")
    sub.add_parser("quota", parents=[cfg_after],
                   help="show provider quota pressure and fallback recommendations from traces")
    evidence_parent = argparse.ArgumentParser(add_help=False)
    evidence_parent.add_argument("--evidence", default=DEFAULT_EVIDENCE, help="path to evidence registry JSON")
    evidence = sub.add_parser("evidence", parents=[evidence_parent], help="manage model evidence gates")
    evidence_sub = evidence.add_subparsers(dest="evidence_command", required=True)

    evidence_add = evidence_sub.add_parser("add", help="add or replace a model candidate")
    evidence_add.add_argument("model_id")
    evidence_add.add_argument("--source-url", required=True)
    evidence_add.add_argument("--article", required=True)
    evidence_add.add_argument("--requirement", action="append", default=[])
    evidence_add.add_argument("--notes", default="")

    evidence_verify = evidence_sub.add_parser("verify", help="record local verification")
    evidence_verify.add_argument("model_id")
    evidence_verify.add_argument("--command", dest="verification_command", required=True)
    evidence_verify.add_argument("--passed", action="store_true")
    evidence_verify.add_argument("--notes", default="")

    evidence_incident = evidence_sub.add_parser("incident", help="record a model incident")
    evidence_incident.add_argument("model_id")
    evidence_incident.add_argument("--title", required=True)
    evidence_incident.add_argument("--source-url", default="")
    evidence_incident.add_argument("--severity", choices=["low", "medium", "high", "critical"], required=True)
    evidence_incident.add_argument("--mitigation", required=True)

    evidence_check = evidence_sub.add_parser("check", help="check whether a model may be auto-routed")
    evidence_check.add_argument("model_id")

    evidence_show = evidence_sub.add_parser("show", help="show one model evidence record")
    evidence_show.add_argument("model_id")

    evidence_sub.add_parser("list", help="list model evidence records")
    sub.add_parser("skills", help="list built-in prompt skills")
    sub.add_parser("init", parents=[cfg_after], help="write a starter broker.toml")
    return p


def _trace_path(cfg: cfgmod.Config) -> str:
    # trace lives next to the state file
    base = Path(cfg.state_file).parent
    return str(base / tracemod.DEFAULT_TRACE)


def _cmd_run(args: argparse.Namespace) -> int:
    cfg = cfgmod.load(args.config)
    state = statemod.load(cfg.state_file)
    prompt = apply_skills(args.prompt, args.skill)
    result = run_task(cfg, state, prompt, task=args.task, timeout=args.timeout)
    state.save()
    estimated_cost = 0.0
    if result.provider:
        estimated_cost = cfg.providers[result.provider].cost_per_run_usd
    tracemod.append(_trace_path(cfg), {
        "task": args.task,
        "skills": args.skill or [],
        "provider": result.provider,
        "exit_code": result.exit_code,
        "exhausted": result.exhausted,
        "seconds": round(sum(a.seconds for a in result.attempts), 3),
        "estimated_cost_usd": estimated_cost,
        "attempts": [
            {"provider": a.provider, "exit_code": a.exit_code, "quota_hit": a.quota_hit,
             "unavailable": a.unavailable, "transient": a.transient, "refusal": a.refusal,
             "seconds": a.seconds}
            for a in result.attempts
        ],
    })

    if result.provider is None:
        print(f"broker: {result.output}", file=sys.stderr)
        if result.attempts:
            print(f"  tried: {', '.join(a.label() for a in result.attempts)}", file=sys.stderr)
        return 1
    failovers = [a.label() for a in result.attempts
                 if a.quota_hit or a.unavailable or a.transient or a.refusal]
    if failovers:
        print(f"broker: {', '.join(failovers)} → used {result.provider}", file=sys.stderr)
    print(result.output, end="" if result.output.endswith("\n") else "\n")
    return result.exit_code


def _cmd_route(args: argparse.Namespace) -> int:
    cfg = cfgmod.load(args.config)
    state = statemod.load(cfg.state_file)
    pl = plan(cfg, state, args.task, statemod.now())
    print(f"task: {args.task or '(default)'}  order: {' → '.join(pl.order)}")
    print(f"cost_strategy: {cfg.cost_strategy}")
    if pl.order:
        costs = ", ".join(
            f"{name}=${cfg.providers[name].cost_per_run_usd:.4f}" for name in pl.order
        )
        print(f"estimated_costs: {costs}")
    if pl.chosen:
        print(f"  → would use: {pl.chosen}")
    else:
        print(f"  → all cooled down; {pl.soonest} frees up in {int(pl.soonest_eta)}s")
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    cfg = cfgmod.load(args.config)
    state = statemod.load(cfg.state_file)
    nowt = statemod.now()
    for name, prov in cfg.providers.items():
        st = state.get(name)
        tag = "available" if st.available(nowt) else f"cooldown {int(st.cooldown_remaining(nowt))}s"
        print(f"{name:<10} {tag:<16} runs={st.runs} fails={st.failures}  strengths: {', '.join(prov.strengths)}")
    return 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    cfg = cfgmod.load(args.config)
    all_ok = True
    for name, prov in cfg.providers.items():
        ok, detail = probe_provider(prov)
        mark = "ok " if ok else "MISSING"
        print(f"{name:<10} {mark:<8} {detail}")
        all_ok = all_ok and ok
    if not all_ok:
        print("broker: some provider CLIs are not installed — those models will be skipped on run",
              file=sys.stderr)
    return 0 if all_ok else 1


def _cmd_trace(args: argparse.Namespace) -> int:
    cfg = cfgmod.load(args.config)
    print(tracemod.summarize(_trace_path(cfg)).render())
    return 0


def _cmd_cost(args: argparse.Namespace) -> int:
    cfg = cfgmod.load(args.config)
    print(cost_radar(cfg, tracemod.summarize(_trace_path(cfg))).render())
    return 0


def _cmd_runtime(args: argparse.Namespace) -> int:
    cfg = cfgmod.load(args.config)
    print(runtime_report(_trace_path(cfg)).render())
    return 0


def _cmd_quota(args: argparse.Namespace) -> int:
    cfg = cfgmod.load(args.config)
    print(quota_report(_trace_path(cfg)).render())
    return 0


def _cmd_skills(args: argparse.Namespace) -> int:
    del args
    for name in skill_names():
        skill = get_skill(name)
        print(f"{skill.name:<12} {skill.summary}")
    return 0


def _cmd_evidence(args: argparse.Namespace) -> int:
    registry = load_evidence(args.evidence)
    if args.evidence_command == "add":
        record = add_model(
            registry,
            args.model_id,
            source_url=args.source_url,
            article=args.article,
            requirements=args.requirement,
            notes=args.notes,
        )
        save_evidence(args.evidence, registry)
        print(json.dumps(record.to_dict(), indent=2, sort_keys=True))
        return 0
    if args.evidence_command == "verify":
        record = registry.require_model(args.model_id)
        record.add_verification(args.verification_command, args.passed, args.notes)
        save_evidence(args.evidence, registry)
        print(f"{args.model_id}: {'verified' if args.passed else 'not verified'}")
        return 0
    if args.evidence_command == "incident":
        incident = add_incident(
            registry,
            model=args.model_id,
            title=args.title,
            source_url=args.source_url,
            severity=args.severity,
            mitigation=args.mitigation,
        )
        save_evidence(args.evidence, registry)
        print(json.dumps(incident.to_dict(), indent=2, sort_keys=True))
        return 0
    if args.evidence_command == "check":
        record = registry.require_model(args.model_id)
        allowed, reasons = record.route_decision(registry.incidents)
        print(f"{args.model_id}: {'route-allowed' if allowed else 'blocked'}")
        for reason in reasons:
            print(f"  - {reason}")
        return 0 if allowed else 1
    if args.evidence_command == "show":
        print(json.dumps(registry.require_model(args.model_id).to_dict(), indent=2, sort_keys=True))
        return 0
    if args.evidence_command == "list":
        for model_id, record in sorted(registry.models.items()):
            allowed, reasons = record.route_decision(registry.incidents)
            reason = "; ".join(reasons) if reasons else "ok"
            print(f"{model_id}: status={record.status} route={allowed} reason={reason}")
        return 0
    raise AssertionError(args.evidence_command)


def _cmd_init(args: argparse.Namespace) -> int:
    dest = Path(args.config)
    if dest.exists():
        print(f"broker: {dest} already exists", file=sys.stderr)
        return 2
    dest.write_text(_DEFAULT_TOML, encoding="utf-8")
    print(f"wrote {dest}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    dispatch = {"run": _cmd_run, "route": _cmd_route, "status": _cmd_status,
                "doctor": _cmd_doctor, "trace": _cmd_trace, "cost": _cmd_cost,
                "runtime": _cmd_runtime, "quota": _cmd_quota,
                "skills": _cmd_skills, "evidence": _cmd_evidence,
                "init": _cmd_init}
    try:
        return dispatch[args.command](args)
    except (ConfigError, EvidenceError) as exc:
        print(f"broker: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
