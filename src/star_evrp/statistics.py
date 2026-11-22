"""Statistical helpers: Wilson intervals, CRN seeds, lognormal summaries."""

from __future__ import annotations

import hashlib
from typing import Iterable

import numpy as np
from numpy.random import Generator, SeedSequence
from scipy import stats


def stable_seed(*parts: object, modulus: int = 2**31 - 1) -> int:
    """Deterministic seed from arbitrary parts (hashlib, not built-in ``hash``)."""
    payload = "|".join(str(p) for p in parts)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return int(digest[:16], 16) % modulus


def derive_seed(master_seed: int, *labels: object) -> int:
    return stable_seed(master_seed, *labels)


def make_rng(master_seed: int, *labels: object) -> Generator:
    """Independent RNG stream for a labeled sub-experiment."""
    child = derive_seed(master_seed, *labels)
    return np.random.default_rng(SeedSequence(child))


def crn_wait_streams(
    master_seed: int,
    route_keys: Iterable[str],
    num_scenarios: int,
) -> dict[str, Generator]:
    """One reproducible wait stream per route (common random numbers across policies)."""
    streams: dict[str, Generator] = {}
    for key in route_keys:
        streams[key] = make_rng(master_seed, "wait", key, num_scenarios)
    return streams


def wilson_ci(
    successes: int,
    trials: int,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if trials <= 0:
        return (0.0, 1.0)
    if successes < 0 or successes > trials:
        raise ValueError("successes must be in [0, trials]")
    z = float(stats.norm.ppf(0.5 + confidence / 2.0))
    phat = successes / trials
    denom = 1.0 + z**2 / trials
    center = (phat + z**2 / (2 * trials)) / denom
    margin = (
        z
        * np.sqrt((phat * (1 - phat) + z**2 / (4 * trials)) / trials)
        / denom
    )
    low = max(0.0, center - margin)
    high = min(1.0, center + margin)
    return (float(low), float(high))


def lognormal_mean(mu: float, sigma: float) -> float:
    return float(np.exp(mu + 0.5 * sigma**2))


def lognormal_median(mu: float, sigma: float) -> float:
    return float(np.exp(mu))


def lognormal_quantile(mu: float, sigma: float, q: float) -> float:
    return float(stats.lognorm.ppf(q, s=sigma, scale=np.exp(mu)))