"""Lognormal wait sampling vs analytical moments."""

from __future__ import annotations

import numpy as np
from scipy import stats

from star_evrp.statistics import lognormal_mean, lognormal_median, lognormal_quantile, make_rng


def test_sample_mean_near_analytical():
    mu, sigma = 1.2, 0.35
    rng = make_rng(99, "wait", "stat_test")
    samples = np.exp(mu + sigma * rng.standard_normal(80_000))
    analytical = lognormal_mean(mu, sigma)
    assert abs(float(samples.mean()) - analytical) < 0.05 * analytical


def test_sample_quantiles_near_analytical():
    mu, sigma = -0.5, 0.4
    rng = make_rng(7, "wait", "quantile_test")
    samples = np.exp(mu + sigma * rng.standard_normal(50_000))
    for q in (0.5, 0.95):
        emp = float(np.quantile(samples, q))
        ana = lognormal_quantile(mu, sigma, q)
        assert abs(emp - ana) / max(ana, 1e-9) < 0.04


def test_median_matches_exp_mu():
    mu, sigma = 2.0, 0.5
    assert lognormal_median(mu, sigma) == float(np.exp(mu))
    ref = float(stats.lognorm.median(sigma, scale=np.exp(mu)))
    assert abs(lognormal_median(mu, sigma) - ref) < 1e-12