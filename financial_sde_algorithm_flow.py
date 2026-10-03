#!/usr/bin/env python3
"""Algorithm-only Financial SDE workflow, ordered for an oral presentation.

This is extracted and reorganised from ``Python代码第二版.py``.  It contains
the numerical algorithms and the calculations that turn simulated paths into
error data.  It deliberately contains no Matplotlib code, figures, LaTeX,
JSON output, or group-level run wrapper.

Study/run:
    python financial_sde_algorithm_flow.py --quick

Full report-size calculation (computationally expensive):
    python financial_sde_algorithm_flow.py

The numbered sections follow this presentation logic:
    1. mathematical objects and parameters
    2. discrete update formulae
    3. random-increment generation
    4. common-path and nested-path construction
    5. Monte Carlo loops
    6. error data and numerical conclusions
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from statistics import NormalDist

import numpy as np


SEED = 20260918
STANDARD_NORMAL = NormalDist()


# =============================================================================
# 1. MATHEMATICAL OBJECTS AND PARAMETERS
# =============================================================================
# GBM:
#     dS = mu*S*dt + sigma*S*dW
#
# Non-affine stochastic volatility, with X = log(S):
#     dX = (mu - 0.5*g(Y)^2)dt + g(Y)dW1
#     dY = kappa*(theta-Y)dt + xi*sqrt(1+Y^2)dW2
#     Corr(dW1,dW2) = rho


@dataclass(frozen=True)
class GBMParameters:
    s0: float = 100.0
    mu: float = 0.05
    sigma: float = 0.40
    maturity: float = 1.0


@dataclass(frozen=True)
class NonAffineParameters:
    s0: float = 100.0
    y0: float = 0.0
    mu: float = 0.05
    kappa: float = 2.0
    theta: float = -0.2
    xi: float = 0.6
    rho: float = -0.7
    sigma_min: float = 0.10
    sigma_max: float = 0.50
    maturity: float = 1.0
    strike: float = 100.0


# =============================================================================
# 2. DISCRETE UPDATE FORMULAE
# =============================================================================


def gbm_exact_step(
    s: np.ndarray, p: GBMParameters, h: float, dw: np.ndarray
) -> np.ndarray:
    """Exact GBM transition on one interval."""
    return s * np.exp((p.mu - 0.5 * p.sigma**2) * h + p.sigma * dw)


def gbm_em_step(
    s: np.ndarray, p: GBMParameters, h: float, dw: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """One Euler--Maruyama step and its non-positive-multiplier flag."""
    multiplier = 1.0 + p.mu * h + p.sigma * dw
    return s * multiplier, multiplier <= 0.0


def gbm_milstein_step(
    s: np.ndarray, p: GBMParameters, h: float, dw: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """One scalar Milstein step and its non-positive-multiplier flag."""
    multiplier = (
        1.0
        + p.mu * h
        + p.sigma * dw
        + 0.5 * p.sigma**2 * (dw**2 - h)
    )
    return s * multiplier, multiplier <= 0.0


def logistic_vol(y: np.ndarray, p: NonAffineParameters) -> np.ndarray:
    """Bounded g(y), evaluated in two branches to avoid overflow."""
    y = np.asarray(y, dtype=float)
    nonnegative = y >= 0.0
    logistic = np.empty_like(y)
    logistic[nonnegative] = 1.0 / (1.0 + np.exp(-y[nonnegative]))
    exp_y = np.exp(y[~nonnegative])
    logistic[~nonnegative] = exp_y / (1.0 + exp_y)
    return p.sigma_min + (p.sigma_max - p.sigma_min) * logistic


def nonaffine_em_terminal(
    p: NonAffineParameters,
    dw1: np.ndarray,
    dw2: np.ndarray,
    h: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Apply the log-price EM formula to supplied correlated increments."""
    if dw1.ndim != 2 or dw1.shape != dw2.shape:
        raise ValueError("dw1 and dw2 must have the same two-dimensional shape")

    n_paths, n_steps = dw1.shape
    x = np.full(n_paths, math.log(p.s0), dtype=float)
    y = np.full(n_paths, p.y0, dtype=float)

    for step in range(n_steps):
        g_y = logistic_vol(y, p)
        x += (p.mu - 0.5 * g_y**2) * h + g_y * dw1[:, step]
        y += (
            p.kappa * (p.theta - y) * h
            + p.xi * np.sqrt(1.0 + y**2) * dw2[:, step]
        )

    # Reconstructing S as exp(X) preserves positivity.
    return np.exp(x), y


# =============================================================================
# 3. RANDOM-INCREMENT GENERATION
# =============================================================================


def brownian_increment(
    n_paths: int, h: float, rng: np.random.Generator
) -> np.ndarray:
    """Generate dW = sqrt(h) Z, where Z is standard normal."""
    return math.sqrt(h) * rng.standard_normal(n_paths)


def correlated_brownian_increments(
    n_paths: int,
    n_steps: int,
    h: float,
    rho: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate two Brownian-increment arrays with correlation rho."""
    if not -1.0 <= rho <= 1.0:
        raise ValueError("rho must lie in [-1, 1]")
    z1 = rng.standard_normal((n_paths, n_steps))
    z2 = rng.standard_normal((n_paths, n_steps))
    sqrt_h = math.sqrt(h)
    dw1 = sqrt_h * z1
    dw2 = sqrt_h * (rho * z1 + math.sqrt(1.0 - rho**2) * z2)
    return dw1, dw2


# =============================================================================
# 4. COMMON-PATH AND NESTED-PATH CONSTRUCTION
# =============================================================================


def coupled_gbm_terminal(
    p: GBMParameters,
    n_paths: int,
    n_steps: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Drive exact GBM, EM and Milstein with exactly the same dW values."""
    h = p.maturity / n_steps
    exact = np.full(n_paths, p.s0, dtype=float)
    em = exact.copy()
    milstein = exact.copy()
    ever_nonpositive_em = np.zeros(n_paths, dtype=bool)
    ever_nonpositive_milstein = np.zeros(n_paths, dtype=bool)

    for _ in range(n_steps):
        # Generate dW once, then share it between all three updates.
        dw = brownian_increment(n_paths, h, rng)
        exact = gbm_exact_step(exact, p, h, dw)
        em, failed_em = gbm_em_step(em, p, h, dw)
        milstein, failed_milstein = gbm_milstein_step(milstein, p, h, dw)
        ever_nonpositive_em |= failed_em
        ever_nonpositive_milstein |= failed_milstein

    return (
        exact,
        em,
        milstein,
        ever_nonpositive_em,
        ever_nonpositive_milstein,
    )


def aggregate_increments(dw_fine: np.ndarray, factor: int) -> np.ndarray:
    """Sum fine increments so a coarse solution uses the same Brownian path."""
    if dw_fine.ndim != 2 or factor <= 0 or dw_fine.shape[1] % factor:
        raise ValueError("factor must divide the number of fine-grid steps")
    n_paths, n_fine = dw_fine.shape
    return dw_fine.reshape(n_paths, n_fine // factor, factor).sum(axis=2)


# =============================================================================
# 5. MONTE CARLO LOOPS
# =============================================================================


def mean_ci95(samples: np.ndarray) -> tuple[float, float, float]:
    """Monte Carlo sample mean and normal-approximation 95% interval."""
    samples = np.asarray(samples, dtype=float)
    mean = float(np.mean(samples))
    half_width = 1.96 * float(np.std(samples, ddof=1)) / math.sqrt(samples.size)
    return mean, mean - half_width, mean + half_width


def fitted_slope(
    h: np.ndarray, error: np.ndarray
) -> tuple[float, float]:
    """Fit log(error) = intercept + p*log(h); return p and its OLS SE."""
    x = np.log(np.asarray(h, dtype=float))
    y = np.log(np.asarray(error, dtype=float))
    coefficients, covariance = np.polyfit(x, y, 1, cov=True)
    return float(coefficients[0]), float(math.sqrt(covariance[0, 0]))


def run_gbm_monte_carlo(p: GBMParameters, n_paths: int) -> dict:
    """Compute all non-visual GBM experiment data from the second-version code."""
    step_counts = np.array([1, 2, 4, 8, 16, 32, 64, 128, 256], dtype=int)
    rows: list[dict] = []
    terminal_at_64: tuple[np.ndarray, np.ndarray, np.ndarray] | None = None

    for n_steps in step_counts:
        rng = np.random.default_rng(SEED + int(n_steps))
        exact, em, milstein, negative_em, negative_milstein = coupled_gbm_terminal(
            p, n_paths, int(n_steps), rng
        )

        strong_em = mean_ci95(np.abs(em - exact))
        strong_milstein = mean_ci95(np.abs(milstein - exact))
        weak_em = mean_ci95(em - exact)
        weak_milstein = mean_ci95(milstein - exact)

        # For phi(s)=s, both EM and Milstein have this exact numerical mean.
        numerical_mean = p.s0 * (1.0 + p.mu * p.maturity / n_steps) ** n_steps
        exact_mean = p.s0 * math.exp(p.mu * p.maturity)

        rows.append(
            {
                "n_steps": int(n_steps),
                "h": p.maturity / n_steps,
                "strong_em": strong_em[0],
                "strong_em_ci": strong_em[1:],
                "strong_milstein": strong_milstein[0],
                "strong_milstein_ci": strong_milstein[1:],
                "paired_weak_em": weak_em[0],
                "paired_weak_em_ci": weak_em[1:],
                "paired_weak_milstein": weak_milstein[0],
                "paired_weak_milstein_ci": weak_milstein[1:],
                "analytic_mean_bias": numerical_mean - exact_mean,
                "negative_path_em_rate": float(np.mean(negative_em)),
                "negative_path_milstein_rate": float(np.mean(negative_milstein)),
            }
        )
        if n_steps == 64:
            terminal_at_64 = (exact.copy(), em.copy(), milstein.copy())

    h = np.array([row["h"] for row in rows])
    strong_em_values = np.array([row["strong_em"] for row in rows])
    strong_milstein_values = np.array([row["strong_milstein"] for row in rows])
    analytic_bias = np.abs([row["analytic_mean_bias"] for row in rows])
    asymptotic = step_counts >= 4

    em_order = fitted_slope(h[asymptotic], strong_em_values[asymptotic])
    milstein_order = fitted_slope(
        h[asymptotic], strong_milstein_values[asymptotic]
    )
    weak_order = fitted_slope(h[asymptotic], analytic_bias[asymptotic])

    # Matched-accuracy comparison: same error target, not same N.
    target_mae = 0.85
    matched_cost: dict[str, dict | float] = {}
    for name, column in (("EM", "strong_em"), ("Milstein", "strong_milstein")):
        feasible = [row for row in rows if row[column] <= target_mae]
        selected = min(feasible, key=lambda row: row["n_steps"])
        matched_cost[name] = {
            "target_mae": target_mae,
            "n_steps": selected["n_steps"],
            "mae": selected[column],
        }
    matched_cost["step_count_ratio_em_over_milstein"] = (
        matched_cost["EM"]["n_steps"] / matched_cost["Milstein"]["n_steps"]
    )

    if terminal_at_64 is None:
        raise RuntimeError("the selected grids must include N=64")
    exact_64, em_64, milstein_64 = terminal_at_64
    exact_mean = p.s0 * math.exp(p.mu * p.maturity)
    exact_variance = p.s0**2 * math.exp(2.0 * p.mu * p.maturity) * (
        math.exp(p.sigma**2 * p.maturity) - 1.0
    )
    probabilities = np.array([0.01, 0.05, 0.50, 0.95, 0.99])
    exact_quantiles = p.s0 * np.exp(
        (p.mu - 0.5 * p.sigma**2) * p.maturity
        + p.sigma
        * math.sqrt(p.maturity)
        * np.array([STANDARD_NORMAL.inv_cdf(float(q)) for q in probabilities])
    )
    distribution = {
        "exact_mean_formula": exact_mean,
        "exact_variance_formula": exact_variance,
        "exact_sample_mean": float(np.mean(exact_64)),
        "exact_sample_variance": float(np.var(exact_64, ddof=1)),
        "em_sample_mean_n64": float(np.mean(em_64)),
        "milstein_sample_mean_n64": float(np.mean(milstein_64)),
        "probabilities": probabilities.tolist(),
        "exact_quantiles": exact_quantiles.tolist(),
        "em_quantiles_n64": np.quantile(em_64, probabilities).tolist(),
        "milstein_quantiles_n64": np.quantile(milstein_64, probabilities).tolist(),
    }

    return {
        "n_paths": n_paths,
        "rows": rows,
        "orders": {
            "strong_em": em_order,
            "strong_milstein": milstein_order,
            "weak_mean_bias": weak_order,
        },
        "matched_cost": matched_cost,
        "distribution": distribution,
    }


def run_nonaffine_monte_carlo(
    p: NonAffineParameters, n_paths: int, reference_steps: int
) -> dict:
    """Compute coupled coarse/reference errors, payoff bias and diagnostics."""
    coarse_steps = np.array([16, 32, 64, 128, 256], dtype=int)
    if any(reference_steps % n for n in coarse_steps):
        raise ValueError("reference_steps must be divisible by every coarse N")

    batch_size = min(1000, n_paths)
    strong_batches = {int(n): [] for n in coarse_steps}
    payoff_bias_batches = {int(n): [] for n in coarse_steps}
    reference_prices: list[np.ndarray] = []
    reference_factors: list[np.ndarray] = []
    reference_payoffs: list[np.ndarray] = []
    increment_samples_1: list[np.ndarray] = []
    increment_samples_2: list[np.ndarray] = []

    rng = np.random.default_rng(SEED + 5000)
    h_reference = p.maturity / reference_steps

    # Batching changes memory use, not the mathematics.
    for start in range(0, n_paths, batch_size):
        batch_paths = min(batch_size, n_paths - start)
        fine_dw1, fine_dw2 = correlated_brownian_increments(
            batch_paths, reference_steps, h_reference, p.rho, rng
        )
        increment_samples_1.append(fine_dw1[:, : min(8, reference_steps)].ravel())
        increment_samples_2.append(fine_dw2[:, : min(8, reference_steps)].ravel())

        s_reference, y_reference = nonaffine_em_terminal(
            p, fine_dw1, fine_dw2, h_reference
        )
        payoff_reference = np.maximum(s_reference - p.strike, 0.0)
        reference_prices.append(s_reference)
        reference_factors.append(y_reference)
        reference_payoffs.append(payoff_reference)

        for n_steps in coarse_steps:
            factor = reference_steps // int(n_steps)
            coarse_dw1 = aggregate_increments(fine_dw1, factor)
            coarse_dw2 = aggregate_increments(fine_dw2, factor)
            s_coarse, _ = nonaffine_em_terminal(
                p, coarse_dw1, coarse_dw2, p.maturity / n_steps
            )
            strong_batches[int(n_steps)].append(np.abs(s_coarse - s_reference))
            payoff_bias_batches[int(n_steps)].append(
                np.maximum(s_coarse - p.strike, 0.0) - payoff_reference
            )

    rows: list[dict] = []
    for n_steps in coarse_steps:
        strong = mean_ci95(np.concatenate(strong_batches[int(n_steps)]))
        payoff_bias = mean_ci95(
            np.concatenate(payoff_bias_batches[int(n_steps)])
        )
        rows.append(
            {
                "n_steps": int(n_steps),
                "h": p.maturity / n_steps,
                "strong_mae_vs_reference": strong[0],
                "strong_ci": strong[1:],
                "call_bias_vs_reference": payoff_bias[0],
                "call_bias_ci": payoff_bias[1:],
            }
        )

    # Exclude the finest coarse grid because it lies closest to a finite
    # numerical reference and can bend the fitted line.
    h = np.array([row["h"] for row in rows])
    strong_error = np.array([row["strong_mae_vs_reference"] for row in rows])
    empirical_order = fitted_slope(h[:-1], strong_error[:-1])

    sampled_dw1 = np.concatenate(increment_samples_1)
    sampled_dw2 = np.concatenate(increment_samples_2)
    increment_diagnostics = {
        "var_dw1_over_h": float(np.var(sampled_dw1, ddof=1) / h_reference),
        "var_dw2_over_h": float(np.var(sampled_dw2, ddof=1) / h_reference),
        "sample_correlation": float(np.corrcoef(sampled_dw1, sampled_dw2)[0, 1]),
        "target_correlation": p.rho,
    }

    s_reference = np.concatenate(reference_prices)
    y_reference = np.concatenate(reference_factors)
    payoff_reference = np.concatenate(reference_payoffs)
    reference_diagnostics = {
        "n_steps": reference_steps,
        "mean_s": float(np.mean(s_reference)),
        "se_mean_s": float(np.std(s_reference, ddof=1) / math.sqrt(n_paths)),
        "mean_call": float(np.mean(payoff_reference)),
        "se_mean_call": float(
            np.std(payoff_reference, ddof=1) / math.sqrt(n_paths)
        ),
        "finite_fraction": float(
            np.mean(np.isfinite(s_reference) & np.isfinite(y_reference))
        ),
        "positive_s_fraction": float(np.mean(s_reference > 0.0)),
    }

    return {
        "n_paths": n_paths,
        "rows": rows,
        "empirical_strong_order": empirical_order,
        "increment_diagnostics": increment_diagnostics,
        "reference_diagnostics": reference_diagnostics,
    }


def refine_nonaffine_reference(
    p: NonAffineParameters, n_paths: int, base_reference_steps: int
) -> dict:
    """Compare Nref, 2*Nref and 4*Nref on fresh, mutually coupled paths."""
    reference_grids = [
        base_reference_steps,
        2 * base_reference_steps,
        4 * base_reference_steps,
    ]
    coarse_grids = [16, 32, 64, 128, 256]
    finest_steps = reference_grids[-1]
    batch_size = min(500, n_paths)
    rng = np.random.default_rng(SEED + 9000)

    adjacent_batches = {
        pair: [] for pair in zip(reference_grids[:-1], reference_grids[1:])
    }
    error_batches = {
        (reference, coarse): []
        for reference in reference_grids
        for coarse in coarse_grids
    }

    for start in range(0, n_paths, batch_size):
        batch_paths = min(batch_size, n_paths - start)
        h_finest = p.maturity / finest_steps
        finest_dw1, finest_dw2 = correlated_brownian_increments(
            batch_paths, finest_steps, h_finest, p.rho, rng
        )
        terminal: dict[int, np.ndarray] = {}

        for n_steps in reference_grids + coarse_grids:
            factor = finest_steps // n_steps
            dw1 = aggregate_increments(finest_dw1, factor)
            dw2 = aggregate_increments(finest_dw2, factor)
            terminal[n_steps], y = nonaffine_em_terminal(
                p, dw1, dw2, p.maturity / n_steps
            )
            if not (
                np.isfinite(terminal[n_steps]).all()
                and np.isfinite(y).all()
                and (terminal[n_steps] > 0.0).all()
            ):
                raise ValueError(f"invalid terminal state at N={n_steps}")

        for coarse_reference, fine_reference in adjacent_batches:
            adjacent_batches[coarse_reference, fine_reference].append(
                np.abs(terminal[coarse_reference] - terminal[fine_reference])
            )
        for reference, coarse in error_batches:
            error_batches[reference, coarse].append(
                np.abs(terminal[coarse] - terminal[reference])
            )

    adjacent_comparisons = []
    for (coarse_reference, fine_reference), batches in adjacent_batches.items():
        interval = mean_ci95(np.concatenate(batches))
        adjacent_comparisons.append(
            {
                "coarse_reference_steps": coarse_reference,
                "fine_reference_steps": fine_reference,
                "mean_absolute_difference": interval[0],
                "ci": interval[1:],
            }
        )

    slope_sensitivity = []
    for reference in reference_grids:
        rows = []
        for coarse in coarse_grids:
            interval = mean_ci95(
                np.concatenate(error_batches[reference, coarse])
            )
            rows.append(
                {
                    "n_steps": coarse,
                    "h": p.maturity / coarse,
                    "mae": interval[0],
                    "ci": interval[1:],
                }
            )
        slope = fitted_slope(
            np.array([row["h"] for row in rows[:-1]]),
            np.array([row["mae"] for row in rows[:-1]]),
        )
        slope_sensitivity.append(
            {"reference_steps": reference, "order": slope, "rows": rows}
        )

    return {
        "n_paths": n_paths,
        "finest_steps": finest_steps,
        "adjacent_comparisons": adjacent_comparisons,
        "slope_sensitivity": slope_sensitivity,
    }


# =============================================================================
# 6. ERROR DATA AND NUMERICAL CONCLUSIONS
# =============================================================================


def print_error_data(gbm: dict, nonaffine: dict, refinement: dict) -> None:
    """Print only the quantities needed to explain the algorithmic evidence."""
    print("\nGBM convergence orders")
    for name, (slope, standard_error) in gbm["orders"].items():
        print(f"  {name}: {slope:.4f} +/- {standard_error:.4f}")

    print("\nGBM matched-accuracy step counts")
    print(f"  EM: {gbm['matched_cost']['EM']}")
    print(f"  Milstein: {gbm['matched_cost']['Milstein']}")
    print(
        "  EM/Milstein step-count ratio: "
        f"{gbm['matched_cost']['step_count_ratio_em_over_milstein']:.1f}"
    )

    diagnostics = nonaffine["increment_diagnostics"]
    print("\nNon-affine Brownian-increment diagnostics")
    print(f"  Var(dW1)/h: {diagnostics['var_dw1_over_h']:.5f}")
    print(f"  Var(dW2)/h: {diagnostics['var_dw2_over_h']:.5f}")
    print(
        f"  Corr(dW1,dW2): {diagnostics['sample_correlation']:.5f} "
        f"(target {diagnostics['target_correlation']:.2f})"
    )
    slope, slope_se = nonaffine["empirical_strong_order"]
    print(f"  empirical strong order: {slope:.4f} +/- {slope_se:.4f}")
    print(f"  reference diagnostics: {nonaffine['reference_diagnostics']}")

    print("\nNon-affine reference refinement")
    for comparison in refinement["adjacent_comparisons"]:
        print(f"  {comparison}")
    for sensitivity in refinement["slope_sensitivity"]:
        order, standard_error = sensitivity["order"]
        print(
            f"  reference N={sensitivity['reference_steps']}: "
            f"order={order:.4f} +/- {standard_error:.4f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quick", action="store_true", help="use smaller samples for learning"
    )
    args = parser.parse_args()

    gbm_paths = 40_000 if args.quick else 300_000
    nonaffine_paths = 3_000 if args.quick else 20_000
    reference_steps = 512 if args.quick else 2048
    refinement_paths = max(3_000, nonaffine_paths // 5)

    gbm = run_gbm_monte_carlo(GBMParameters(), gbm_paths)
    nonaffine = run_nonaffine_monte_carlo(
        NonAffineParameters(), nonaffine_paths, reference_steps
    )
    refinement = refine_nonaffine_reference(
        NonAffineParameters(), refinement_paths, reference_steps
    )
    print_error_data(gbm, nonaffine, refinement)


if __name__ == "__main__":
    main()
