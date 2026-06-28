"""Local evidence gate for routing new or risky models."""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_EVIDENCE = ".broker-evidence.json"
VALID_SEVERITY = {"low", "medium", "high", "critical"}
BLOCKING_SEVERITY = {"high", "critical"}


class EvidenceError(Exception):
    """Raised when the evidence registry is malformed or a request is invalid."""


def now() -> str:
    return datetime.now(UTC).astimezone().isoformat(timespec="seconds")


def local_frameworks() -> list[str]:
    found = []
    for name in ("ollama", "llama-cli", "vllm", "sglang", "mlx_lm", "python"):
        if shutil.which(name):
            found.append(name)
    return found


@dataclass
class Verification:
    command: str
    passed: bool
    notes: str = ""
    at: str = field(default_factory=now)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Verification:
        return cls(
            command=str(data["command"]),
            passed=bool(data["passed"]),
            notes=str(data.get("notes", "")),
            at=str(data.get("at", now())),
        )

    def to_dict(self) -> dict[str, object]:
        return {"command": self.command, "passed": self.passed, "notes": self.notes, "at": self.at}


@dataclass
class Incident:
    model: str
    title: str
    severity: str
    source_url: str = ""
    mitigation: str = ""
    created_at: str = field(default_factory=now)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Incident:
        severity = str(data["severity"]).lower()
        if severity not in VALID_SEVERITY:
            raise EvidenceError(f"invalid severity: {severity}")
        return cls(
            model=str(data["model"]),
            title=str(data["title"]),
            severity=severity,
            source_url=str(data.get("source_url", "")),
            mitigation=str(data.get("mitigation", "")),
            created_at=str(data.get("created_at", now())),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "model": self.model,
            "title": self.title,
            "severity": self.severity,
            "source_url": self.source_url,
            "mitigation": self.mitigation,
            "created_at": self.created_at,
            "route_allowed": self.severity not in BLOCKING_SEVERITY,
        }


@dataclass
class ModelEvidence:
    model_id: str
    source_url: str
    article: str
    requirements: list[str] = field(default_factory=list)
    notes: str = ""
    status: str = "candidate"
    auto_route_allowed: bool = False
    local_frameworks_seen: list[str] = field(default_factory=list)
    missing_requirements: list[str] = field(default_factory=list)
    verification: list[Verification] = field(default_factory=list)
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)

    @classmethod
    def create(
        cls,
        model_id: str,
        *,
        source_url: str,
        article: str,
        requirements: list[str],
        notes: str,
    ) -> ModelEvidence:
        frameworks = local_frameworks()
        missing = [requirement for requirement in requirements if requirement not in frameworks]
        return cls(
            model_id=model_id,
            source_url=source_url,
            article=article,
            requirements=requirements,
            notes=notes,
            status="candidate" if missing else "needs-benchmark",
            auto_route_allowed=False,
            local_frameworks_seen=frameworks,
            missing_requirements=missing,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelEvidence:
        return cls(
            model_id=str(data["id"]),
            source_url=str(data.get("source_url", "")),
            article=str(data.get("article", "")),
            requirements=[str(item) for item in data.get("requirements", [])],
            notes=str(data.get("notes", "")),
            status=str(data.get("status", "candidate")),
            auto_route_allowed=bool(data.get("auto_route_allowed", False)),
            local_frameworks_seen=[str(item) for item in data.get("local_frameworks", [])],
            missing_requirements=[str(item) for item in data.get("missing_requirements", [])],
            verification=[Verification.from_dict(item) for item in data.get("verification", [])],
            created_at=str(data.get("created_at", now())),
            updated_at=str(data.get("updated_at", now())),
        )

    def add_verification(self, command: str, passed: bool, notes: str = "") -> None:
        self.verification.append(Verification(command=command, passed=passed, notes=notes))
        self.updated_at = now()
        self.status = "verified" if passed else "candidate"
        self.auto_route_allowed = bool(passed)

    def route_decision(self, incidents: list[Incident]) -> tuple[bool, list[str]]:
        reasons: list[str] = []
        if not self.auto_route_allowed:
            reasons.append("model has not passed local verification")
        if self.missing_requirements:
            reasons.append("missing local requirements: " + ", ".join(self.missing_requirements))
        blocking = [item for item in incidents if item.model == self.model_id and item.severity in BLOCKING_SEVERITY]
        for incident in blocking:
            reasons.append(f"{incident.severity} incident: {incident.title}")
        return not reasons, reasons

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.model_id,
            "source_url": self.source_url,
            "article": self.article,
            "requirements": self.requirements,
            "local_frameworks": self.local_frameworks_seen,
            "missing_requirements": self.missing_requirements,
            "status": self.status,
            "auto_route_allowed": self.auto_route_allowed,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "verification": [item.to_dict() for item in self.verification],
        }


@dataclass
class EvidenceRegistry:
    models: dict[str, ModelEvidence] = field(default_factory=dict)
    incidents: list[Incident] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceRegistry:
        raw_models = data.get("models", {})
        raw_incidents = data.get("incidents", [])
        if not isinstance(raw_models, dict) or not isinstance(raw_incidents, list):
            raise EvidenceError("invalid evidence registry")
        return cls(
            models={model_id: ModelEvidence.from_dict(item) for model_id, item in raw_models.items()},
            incidents=[Incident.from_dict(item) for item in raw_incidents],
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "version": 1,
            "models": {model_id: item.to_dict() for model_id, item in sorted(self.models.items())},
            "incidents": [item.to_dict() for item in self.incidents],
        }

    def require_model(self, model_id: str) -> ModelEvidence:
        try:
            return self.models[model_id]
        except KeyError as exc:
            raise EvidenceError(f"model not found: {model_id}") from exc


def load(path: str | Path = DEFAULT_EVIDENCE) -> EvidenceRegistry:
    p = Path(path)
    if not p.exists():
        return EvidenceRegistry()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"cannot read evidence registry {p}: {exc}") from exc
    if not isinstance(data, dict):
        raise EvidenceError(f"invalid evidence registry: {p}")
    return EvidenceRegistry.from_dict(data)


def save(path: str | Path, registry: EvidenceRegistry) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(registry.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def add_model(
    registry: EvidenceRegistry,
    model_id: str,
    *,
    source_url: str,
    article: str,
    requirements: list[str],
    notes: str,
) -> ModelEvidence:
    record = ModelEvidence.create(
        model_id,
        source_url=source_url,
        article=article,
        requirements=requirements,
        notes=notes,
    )
    registry.models[model_id] = record
    return record


def add_incident(
    registry: EvidenceRegistry,
    *,
    model: str,
    title: str,
    source_url: str,
    severity: str,
    mitigation: str,
) -> Incident:
    severity = severity.lower()
    if severity not in VALID_SEVERITY:
        raise EvidenceError(f"invalid severity: {severity}")
    incident = Incident(
        model=model,
        title=title,
        source_url=source_url,
        severity=severity,
        mitigation=mitigation,
    )
    registry.incidents.append(incident)
    return incident
