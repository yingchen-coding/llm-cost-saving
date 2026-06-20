"""modelbroker — a quota-aware multi-model harness.

Route each task to the model that's strongest at it; when a provider runs out of quota, cool it
down and fail over to the next; resume using it the moment its window resets. Cost control by never
stalling on one model's limit and never burning the scarce model on cheap work.
"""
from importlib.metadata import PackageNotFoundError, version

from .config import Config, ConfigError, Provider, load
from .router import Plan, plan
from .runner import RunResult, run_task
from .state import State

try:
    __version__ = version("modelbroker")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = [
    "Config",
    "ConfigError",
    "Plan",
    "Provider",
    "RunResult",
    "State",
    "__version__",
    "load",
    "plan",
    "run_task",
]
