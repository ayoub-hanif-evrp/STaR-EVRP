"""Vectorized full-route timing for a deterministically validated plan."""

from dataclasses import dataclass

import numpy as np
from scipy.special import ndtr

from star_evrp.deterministic_simulator import SimulatorConfig
from star_evrp.geometry import leg_distance
from star_evrp.types import NUM_TOL, Instance, NodeType, RouteTrace


@dataclass(frozen=True)
class TimingStep:
    travel: float
    ready: float
    duration: float
    start_deadline: float
    end_deadline: float
    slot: int | None


@dataclass(frozen=True)
class RouteTiming:
    steps: tuple[TimingStep, ...]
    mus: np.ndarray
    sigmas: np.ndarray

    @classmethod
    def from_trace(cls, instance: Instance, trace: RouteTrace, config: SimulatorConfig):
        if not trace.feasible or len(trace.stops) < 2:
            raise ValueError("Timing requires a valid explicit route")
        steps, mus, sigmas = [], [], []
        for previous, stop in zip(trace.stops, trace.stops[1:]):
            node = instance.node(stop.node_id)
            travel = leg_distance(instance, previous.node_id, stop.node_id)
            ready, duration = -np.inf, 0.0
            start_deadline, end_deadline = np.inf, np.inf
            slot = None
            if node.node_type == NodeType.STATION:
                attributes = instance.station_attributes[node.node_id]
                slot = len(mus)
                mus.append(attributes.wait_mu)
                sigmas.append(attributes.wait_sigma)
                if stop.energy_charged > NUM_TOL:
                    duration = stop.energy_charged / attributes.charging_rate
                if config.enforce_station_time_windows:
                    ready = node.ready_time
                    end_deadline = node.due_date
            elif node.node_type == NodeType.CUSTOMER:
                ready, duration, start_deadline = node.ready_time, node.service_time, node.due_date
            else:
                end_deadline = instance.depot_closing_time
            steps.append(TimingStep(travel, ready, duration, start_deadline, end_deadline, slot))
        return cls(tuple(steps), np.array(mus), np.array(sigmas))

    def waits(self, shocks: np.ndarray) -> np.ndarray:
        return np.exp(self.mus + self.sigmas * shocks[:, :len(self.mus)])

    def evaluate(self, waits: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        clock = np.zeros(len(waits))
        success = np.ones(len(waits), dtype=bool)
        for step in self.steps:
            clock += step.travel
            np.maximum(clock, step.ready, out=clock)
            if step.slot is not None:
                clock += waits[:, step.slot]
            success &= clock - step.start_deadline <= NUM_TOL
            clock += step.duration
            success &= clock <= step.end_deadline + NUM_TOL
        return success, clock

    def isolated_caps(self, trace: RouteTrace) -> np.ndarray:
        """Upper bound isolated delays by removing all downstream ready-time floors."""
        caps = np.empty(len(self.mus))
        latest = np.inf
        for step, stop in zip(reversed(self.steps), reversed(trace.stops[1:])):
            latest = min(latest, step.end_deadline + NUM_TOL)
            if step.slot is not None:
                cushion = 1e-10 * len(self.steps) * max(1., abs(latest), abs(stop.departure_time))
                caps[step.slot] = max(0., latest - stop.departure_time + cushion)
            latest = min(latest - step.duration, step.start_deadline + NUM_TOL) - step.travel
        return caps

    def marginal_bounds(self, trace: RouteTrace) -> np.ndarray:
        caps = self.isolated_caps(trace)
        with np.errstate(divide="ignore", invalid="ignore"):
            cdfs = ndtr((np.log(caps) - self.mus) / self.sigmas)
        return np.where(self.sigmas == 0, (caps >= np.exp(self.mus)).astype(float), cdfs)
