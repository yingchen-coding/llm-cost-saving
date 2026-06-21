from broker.cli import _build_parser


def _config(argv: list[str]) -> str:
    return _build_parser().parse_args(argv).config


def test_config_flag_accepted_before_or_after_subcommand() -> None:
    # -c works both before the subcommand and after it (the latter used to argparse-error: exit 2)
    assert _config(["-c", "x.toml", "route", "-t", "codegen"]) == "x.toml"
    assert _config(["route", "-t", "codegen", "-c", "x.toml"]) == "x.toml"
    assert _config(["run", "hi", "-c", "x.toml"]) == "x.toml"


def test_config_default_intact_when_flag_absent() -> None:
    # SUPPRESS on the subcommand parser must not reset the global default to None
    assert _config(["route"]) == "broker.toml"
    assert _config(["status"]) == "broker.toml"
