"""Prompt skills applied before routing a task to a provider."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Skill:
    name: str
    summary: str
    instruction: str


STOP_SLOP = Skill(
    name="stop-slop",
    summary="Make the answer direct, concrete, and low-fluff before sending it to a model.",
    instruction="""\
Use the stop-slop quality contract for this response:
- Answer the actual request directly; do not pad with generic framing.
- Prefer concrete decisions, commands, file paths, examples, and measurable checks.
- Remove hype, cheerleading, fake certainty, vague adjectives, and filler transitions.
- State assumptions only when they change the answer.
- If something is unknown, say exactly what is unknown and how to verify it.
- Keep the final response concise unless the user explicitly asks for depth.

User request:
""",
)


CONTEXT_WINDOW = Skill(
    name="context-window",
    summary="Keep long tasks inside the context window by passing only the context needed now.",
    instruction="""\
Use the context-window optimization method for this task:
- Pass the smallest sufficient context for the current step.
- If code alone is enough, use code only; do not include unrelated logs, transcripts, raw data, or prior discussion.
- Delay bulky data until the step that actually needs it.
- Preserve compact state explicitly: goal, decisions, changed files, commands run, failures, and next action.
- When context is getting long, compact or summarize before continuing. If the environment supports a
  slash command such as /compact, run it at the appropriate checkpoint.
- Before the final answer, sanity-check that the latest user request is still being answered.

User request:
""",
)


LLM_COST_SAVING = Skill(
    name="llm-cost-saving",
    summary="Cut LLM spend by routing to the cheapest model/approach for each unit of work.",
    instruction="""\
Apply these LLM cost-saving rules before executing this task:

MODEL ROUTING — match model tier to cognitive difficulty, not task size:
- Opus: genuine judgment only (architecture decisions, real bug diagnosis, security review, ambiguous requirements).
- Sonnet subagent (model:"sonnet"): search, grep-and-summarize, file inventory, log scan, read-many-files tasks.
- Haiku subagent (model:"haiku"): bulk mechanical work (rename, format, boilerplate, test scaffolding, string munging).
- No model (script): counting rows, scanning S3, diffing files, aggregating data, checking job status.

DATA ANALYSIS — never load large datasets into context:
- Before reading any file >10K rows or >10MB: check size with `du -h` first.
- Code-first (CHEAPEST): generate a script → user runs it → user pastes result (200 tokens vs 11M for 231K rows).
- Sampling (MIDDLE): `df.sample(n=1000)` or `df.group_by(...).sample(n=100)` for representative rows.
- Image compression (LAST RESORT): render chart, downscale 1000:1, send as vision (~10K tokens vs 11M text tokens).
- When user asks "how many / what's in / check data quality": generate the script, don't load the data.

BACKGROUND JOBS — never sleep-poll:
- Bad: `while status != "COMPLETE": sleep(30); check_status()` — burns 1 Opus turn per poll cycle.
- Good: `run_in_background=True` on the original command; notification fires when done (0 turns while waiting).

MEMORY ACCESS — search before loading:
- Tier 1 (FREE): `rg -l "keyword" ~/.claude/projects/*/memory/` — returns filenames only.
- Tier 2 (CHEAP): `head -10` on matched files to read frontmatter/description only (~50 tokens per file).
- Tier 3 (EXPENSIVE): full file load — only when the file is confirmed directly relevant.

RESPONSES — stop slop:
- Cut filler phrases ("I'll help you", "Let me", "Here's what", "After analyzing").
- Active voice, no em-dashes, no vague declaratives.
- Filler-free prose saves 10-20% tokens per response.
- Minimum outward print by default: no progress narration unless it helps the user decide or unblock.
- Final answers should be compact: changed files, verification, blockers. Do not dump raw logs.
- When exploring, use line-limited reads and report counts/paths instead of pasted output.

COST-AWARE ≠ QUALITY-BLIND: never route a genuinely hard reasoning/safety task to a weak model.
A wrong fix costs a dev cycle, far more than the token delta saved.

User request:
""",
)


_SKILLS = {
    STOP_SLOP.name: STOP_SLOP,
    CONTEXT_WINDOW.name: CONTEXT_WINDOW,
    LLM_COST_SAVING.name: LLM_COST_SAVING,
}


def skill_names() -> list[str]:
    """Return known skill names in stable CLI display order."""
    return sorted(_SKILLS)


def get_skill(name: str) -> Skill:
    try:
        return _SKILLS[name]
    except KeyError as exc:
        known = ", ".join(skill_names())
        raise ValueError(f"unknown skill {name!r}; known skills: {known}") from exc


def apply_skill(prompt: str, name: str) -> str:
    """Return a prompt wrapped with the named skill's instruction."""
    skill = get_skill(name)
    return f"{skill.instruction}{prompt}"


def apply_skills(prompt: str, names: list[str] | None) -> str:
    """Apply skills in the order requested by the operator."""
    result = prompt
    for name in names or []:
        result = apply_skill(result, name)
    return result
