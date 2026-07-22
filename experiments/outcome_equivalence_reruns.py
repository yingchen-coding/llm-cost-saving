#!/usr/bin/env python3
"""Prospective cheap-tier outcome-equivalence check for the mechanical-token-waste contract.

The token-austerity contract claims a mechanical turn (tool orchestration, low generated text) can
be rerouted to a cheap tier with no change in outcome. The aggregate replay measures how much spend
that recovers; this script tests the *outcome* half prospectively: real mechanical tasks were run by
blind subagents on a cheap tier and a premium tier, neither seeing the answer, each doing the tool
work itself. Equivalence = cheap == premium == ground truth.

Reproducibility split (kept honest):
  * Ground truth is recomputed from hash-pinned local inputs and a public source revision.
  * The per-tier answers live in experiment_results/outcome_equivalence_reruns.json as recorded
    evidence, each with the exact prompt so a reviewer can re-issue the identical task to any tier.

Run:  python3 experiments/outcome_equivalence_reruns.py
Use --require-equivalence when this evidence gates an automatic routing change.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PUBLIC = REPO.parent
RESULT = REPO / "experiment_results" / "outcome_equivalence_reruns.json"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _revision_file(repo: Path, revision: str, path: str) -> str:
    return _git(repo, "show", f"{revision}:{path}")


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def ground_truth(agentguard: Path, loopforge: Path, snapshot: dict[str, str]) -> dict[str, str]:
    """Recompute each task after verifying the exact source snapshot."""
    eval_files = sorted((agentguard / "eval").glob("*.py"))
    manifest = "".join(f"eval/{path.name}\n" for path in eval_files).encode()
    trifecta_bytes = (agentguard / "eval" / "trifecta_reach.py").read_bytes()
    marketplace_bytes = (agentguard / "results" / "trifecta_reach_marketplace.json").read_bytes()
    rules_source = _revision_file(loopforge, snapshot["loopforge_revision"], "loopforge/rules.py")
    observed = {
        "agentguard_eval_manifest_sha256": _sha256(manifest),
        "agentguard_trifecta_reach_sha256": _sha256(trifecta_bytes),
        "agentguard_marketplace_sha256": _sha256(marketplace_bytes),
        "loopforge_rules_sha256": _sha256(rules_source.encode()),
    }
    for key, value in observed.items():
        if value != snapshot[key]:
            raise RuntimeError(f"source snapshot mismatch for {key}: expected {snapshot[key]}, got {value}")
    trifecta_source = trifecta_bytes.decode()
    rows = json.loads(marketplace_bytes)["rows"]
    return {
        "T1": str(len(eval_files)),
        "T2": str(sum(1 for line in trifecta_source.splitlines() if line.startswith("def "))),
        "T3": next(line for line in trifecta_source.splitlines() if line.startswith(("import ", "from "))),
        "T4": str(rules_source.count('@rule("L')),
        "T5": str(sum(1 for r in rows if r.get("trifecta_complete") is True)),
        "T6": str(len(rows)),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agentguard", type=Path, default=PUBLIC / "agentguard")
    parser.add_argument("--loopforge", type=Path, default=PUBLIC / "loopforge")
    parser.add_argument("--require-equivalence", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = json.loads(RESULT.read_text())
    gt = ground_truth(args.agentguard, args.loopforge, data["source_snapshot"])
    model_mismatches = source_drifts = 0
    print(f"{'task':5} {'ground_truth':38} {'cheap':8} {'premium':8} equiv")
    for t in data["tasks"]:
        g = gt[t["id"]]
        ok = (t["cheap"] == g == t["premium"])
        gt_recomputed_matches = (g == t["ground_truth"])
        model_mismatches += not ok
        source_drifts += not gt_recomputed_matches
        flag = "OK" if ok else "MODEL_MISMATCH"
        if not gt_recomputed_matches:
            flag = "SOURCE_DRIFT"
        print(f"{t['id']:5} {g[:38]:38} {t['cheap'][:8]:8} {t['premium'][:8]:8} {flag}")
    n = len(data["tasks"])
    mean_cheap_tokens = round(sum(t["cheap_tokens"] for t in data["tasks"]) / n)
    mean_premium_tokens = round(sum(t["premium_tokens"] for t in data["tasks"]) / n)
    expected_results = {
        "tasks": n,
        "cheap_matches_ground_truth": sum(t["cheap"] == gt[t["id"]] for t in data["tasks"]),
        "premium_matches_ground_truth": sum(t["premium"] == gt[t["id"]] for t in data["tasks"]),
        "cheap_matches_premium": sum(t["cheap"] == t["premium"] for t in data["tasks"]),
        "outcome_equivalence_rate": (n - model_mismatches) / n,
        "mean_cheap_tokens": mean_cheap_tokens,
        "mean_premium_tokens": mean_premium_tokens,
        "token_reduction_at_cheap_tier": 1 - (mean_cheap_tokens / mean_premium_tokens),
    }
    evidence_errors = 0
    for key, expected in expected_results.items():
        actual = data["results"].get(key)
        matches = math.isclose(actual, expected) if isinstance(expected, float) else actual == expected
        if not matches:
            evidence_errors += 1
            print(f"evidence summary mismatch for {key}: expected {expected}, got {actual}")
    print(f"\noutcome-equivalence: {n - model_mismatches}/{n} tasks cheap==premium==ground_truth")
    print(f"mean tokens  cheap={data['results']['mean_cheap_tokens']}  "
          f"premium={data['results']['mean_premium_tokens']}  "
          f"(cheap tier used {data['results']['token_reduction_at_cheap_tier']*100:.0f}% fewer)")
    return 1 if source_drifts or evidence_errors or (args.require_equivalence and model_mismatches) else 0


if __name__ == "__main__":
    raise SystemExit(main())
