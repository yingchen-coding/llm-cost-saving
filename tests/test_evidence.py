from broker.evidence import EvidenceRegistry, add_incident, add_model


def test_verified_model_is_route_allowed() -> None:
    registry = EvidenceRegistry()
    record = add_model(
        registry,
        "example-model",
        source_url="https://example.com/model",
        article="Example launch note",
        requirements=[],
        notes="",
    )
    allowed, reasons = record.route_decision(registry.incidents)
    assert allowed is False
    assert "not passed" in reasons[0]

    record.add_verification("pytest local eval", passed=True, notes="passed smoke")
    allowed, reasons = record.route_decision(registry.incidents)
    assert allowed is True
    assert reasons == []


def test_high_incident_blocks_verified_model() -> None:
    registry = EvidenceRegistry()
    record = add_model(
        registry,
        "example-model",
        source_url="https://example.com/model",
        article="Example launch note",
        requirements=[],
        notes="",
    )
    record.add_verification("pytest local eval", passed=True)
    add_incident(
        registry,
        model="example-model",
        title="unsafe jailbreak regression",
        source_url="https://example.com/incident",
        severity="high",
        mitigation="pin previous model",
    )

    allowed, reasons = record.route_decision(registry.incidents)
    assert allowed is False
    assert reasons == ["high incident: unsafe jailbreak regression"]


def test_registry_round_trips() -> None:
    registry = EvidenceRegistry()
    record = add_model(
        registry,
        "example-model",
        source_url="https://example.com/model",
        article="Example launch note",
        requirements=["python"],
        notes="candidate",
    )
    record.add_verification("python eval.py", passed=False, notes="bad refusal rate")
    add_incident(
        registry,
        model="example-model",
        title="refusal regression",
        source_url="",
        severity="medium",
        mitigation="manual review only",
    )

    restored = EvidenceRegistry.from_dict(registry.to_dict())
    assert restored.require_model("example-model").verification[0].passed is False
    assert restored.incidents[0].severity == "medium"
