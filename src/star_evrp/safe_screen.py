"""Safe stochastic screen (necessary-condition rejection only)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from star_evrp.deterministic_simulator import SimulatorConfig
from star_evrp.risk_bounds import reliability_upper_bound, safe_reject
from star_evrp.types import Instance, Route


class ScreenMode(str, Enum):
    CERTIFIED = "certified"
    EXPLORATION = "exploration"


@dataclass
class ScreenResult:
    det_feasible: bool
    u_min: float
    u_indep: float
    certified_reject: bool
    keep_for_exploration: bool
    mode: ScreenMode
    notes: str = ""


def screen_candidate(
    instance: Instance,
    route: Route,
    config: SimulatorConfig,
    *,
    target: float = 0.95,
    mode: ScreenMode = ScreenMode.CERTIFIED,
    use_indep_product: bool = False,
) -> ScreenResult:
    """Wrap :func:`reliability_upper_bound` with certified vs exploration semantics."""
    bound = reliability_upper_bound(instance, route, config, target=target)
    u_report = bound.upper_bound_u_indep if use_indep_product else bound.upper_bound_u
    reject = safe_reject(bound.upper_bound_u, target=target)

    if mode == ScreenMode.CERTIFIED:
        keep = bound.det_feasible and not reject
    else:
        # Exploration: never discard solely on bound; still record reject flag.
        keep = True

    return ScreenResult(
        det_feasible=bound.det_feasible,
        u_min=bound.upper_bound_u,
        u_indep=bound.upper_bound_u_indep,
        certified_reject=reject,
        keep_for_exploration=keep,
        mode=mode,
        notes=bound.notes,
    )