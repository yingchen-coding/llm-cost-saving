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


_SKILLS = {STOP_SLOP.name: STOP_SLOP, CONTEXT_WINDOW.name: CONTEXT_WINDOW}


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
