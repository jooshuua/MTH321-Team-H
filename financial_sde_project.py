#!/usr/bin/env python3
"""Reproducible experiments for the MTH321 Financial SDE project.

The script implements, rather than delegates, the numerical methods used in
the report: exact GBM coupling, Euler--Maruyama, scalar Milstein, and coupled
Euler--Maruyama for the two-factor non-affine stochastic-volatility model.

Run from the repository root:
    python financial_sde_project.py

Dependencies: Python >= 3.10, NumPy, Matplotlib.
Outputs are written to latex/generated/ with stable file names.  Use --quick
for a faster smoke test; the report numbers are produced by the default mode.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import math
import platform
from statistics import NormalDist
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import NullLocator


SEED = 20260918
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "latex" / "generated"
CB = ["#0077BB", "#EE7733", "#009988", "#CC3311", "#33BBEE", "#000000"]
STD_NORMAL = NormalDist()

matplotlib.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial"],
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "figure.dpi": 160,
        "savefig.dpi": 220,
        "savefig.bbox": "tight",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.22,
    }
)


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


def ci95(x: np.ndarray) -> tuple[float, float, float]:
    """Return sample mean and normal-approximation 95% confidence interval."""
    x = np.asarray(x, dtype=float)
    mean = float(np.mean(x))
    half = 1.96 * float(np.std(x, ddof=1)) / math.sqrt(x.size)
    return mean, mean - half, mean + half


def fitted_slope(h: np.ndarray, error: np.ndarray) -> tuple[float, float]:
    """Log--log slope and its ordinary least-squares standard error."""
    x, y = np.log(np.asarray(h)), np.log(np.asarray(error))
    coef, cov = np.polyfit(x, y, 1, cov=True)
    return float(coef[0]), float(math.sqrt(cov[0, 0]))


def add_loglog_fit_band(
    ax: plt.Axes, h: np.ndarray, error: np.ndarray, color: str, label: str
) -> None:
    """Add an OLS log--log fit and a 95% pointwise regression band."""
    lx, ly = np.log(np.asarray(h)), np.log(np.asarray(error))
    coef, cov = np.polyfit(lx, ly, 1, cov=True)
    gx = np.linspace(lx.min(), lx.max(), 100)
    gy = coef[0] * gx + coef[1]
    se = np.sqrt(cov[1, 1] + 2.0 * gx * cov[0, 1] + gx**2 * cov[0, 0])
    ax.plot(np.exp(gx), np.exp(gy), "--", color=color, lw=1.0, label=label)
    ax.fill_between(np.exp(gx), np.exp(gy - 1.96 * se), np.exp(gy + 1.96 * se), color=color, alpha=0.12)


def gbm_terminal_coupled(
    p: GBMParameters, n_paths: int, n_steps: int, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Couple exact GBM, EM, and Milstein with the same Brownian increments."""
    h = p.maturity / n_steps
    sqh = math.sqrt(h)
    exact = np.full(n_paths, p.s0)
    em = exact.copy()
    mil = exact.copy()
    ever_negative_em = np.zeros(n_paths, dtype=bool)
    ever_negative_mil = np.zeros(n_paths, dtype=bool)
    for _ in range(n_steps):
        z = rng.standard_normal(n_paths)
        dw = sqh * z
        exact *= np.exp((p.mu - 0.5 * p.sigma**2) * h + p.sigma * dw)
        em_factor = 1.0 + p.mu * h + p.sigma * dw
        mil_factor = em_factor + 0.5 * p.sigma**2 * (dw**2 - h)
        ever_negative_em |= em_factor <= 0.0
        ever_negative_mil |= mil_factor <= 0.0
        em *= em_factor
        mil *= mil_factor
    return exact, em, mil, ever_negative_em, ever_negative_mil


def run_gbm(p: GBMParameters, n_paths: int) -> dict:
    steps = np.array([1, 2, 4, 8, 16, 32, 64, 128, 256], dtype=int)
    rows = []
    terminal_for_distribution = None
    for n in steps:
        rng = np.random.default_rng(SEED + int(n))
        exact, em, mil, neg_em, neg_mil = gbm_terminal_coupled(p, n_paths, int(n), rng)
        em_abs = np.abs(em - exact)
        mil_abs = np.abs(mil - exact)
        em_diff = em - exact
        mil_diff = mil - exact
        em_ci = ci95(em_abs)
        mil_ci = ci95(mil_abs)
        weak_em_ci = ci95(em_diff)
        weak_mil_ci = ci95(mil_diff)
        analytic_mean_num = p.s0 * (1.0 + p.mu * p.maturity / n) ** n
        exact_mean = p.s0 * math.exp(p.mu * p.maturity)
        rows.append(
            {
                "n_steps": int(n),
                "h": p.maturity / n,
                "strong_em": em_ci[0],
                "strong_em_ci_low": em_ci[1],
                "strong_em_ci_high": em_ci[2],
                "strong_milstein": mil_ci[0],
                "strong_milstein_ci_low": mil_ci[1],
                "strong_milstein_ci_high": mil_ci[2],
                "weak_em_paired": weak_em_ci[0],
                "weak_em_ci_low": weak_em_ci[1],
                "weak_em_ci_high": weak_em_ci[2],
                "weak_milstein_paired": weak_mil_ci[0],
                "weak_milstein_ci_low": weak_mil_ci[1],
                "weak_milstein_ci_high": weak_mil_ci[2],
                "weak_bias_exact": analytic_mean_num - exact_mean,
                "negative_path_em_rate": float(np.mean(neg_em)),
                "negative_path_milstein_rate": float(np.mean(neg_mil)),
            }
        )
        if n == 64:
            terminal_for_distribution = (exact.copy(), em.copy(), mil.copy())

    h = np.array([r["h"] for r in rows])
    strong_em = np.array([r["strong_em"] for r in rows])
    strong_mil = np.array([r["strong_milstein"] for r in rows])
    weak_exact = np.abs([r["weak_bias_exact"] for r in rows])
    asymptotic = steps >= 4
    slope_em, slope_em_se = fitted_slope(h[asymptotic], strong_em[asymptotic])
    slope_mil, slope_mil_se = fitted_slope(h[asymptotic], strong_mil[asymptotic])
    slope_weak, slope_weak_se = fitted_slope(h[asymptotic], weak_exact[asymptotic])

    target = 0.85
    matched = {}
    for label, key in [("EM", "strong_em"), ("Milstein", "strong_milstein")]:
        feasible = [r for r in rows if r[key] <= target]
        selected = min(feasible, key=lambda r: r["n_steps"]) if feasible else None
        matched[label] = (
            {"target_mae": target, "n_steps": selected["n_steps"], "mae": selected[key]}
            if selected
            else {"target_mae": target, "n_steps": None, "mae": None}
        )
    if matched["EM"]["n_steps"] and matched["Milstein"]["n_steps"]:
        matched["work_ratio_em_over_milstein"] = (
            matched["EM"]["n_steps"] / matched["Milstein"]["n_steps"]
        )

    exact, em64, mil64 = terminal_for_distribution
    exact_mean = p.s0 * math.exp(p.mu * p.maturity)
    exact_var = p.s0**2 * math.exp(2 * p.mu * p.maturity) * (
        math.exp(p.sigma**2 * p.maturity) - 1.0
    )
    distribution = {
        "exact_mean_formula": exact_mean,
        "exact_variance_formula": exact_var,
        "exact_sample_mean": float(np.mean(exact)),
        "exact_sample_variance": float(np.var(exact, ddof=1)),
        "em_sample_mean_n64": float(np.mean(em64)),
        "milstein_sample_mean_n64": float(np.mean(mil64)),
        "quantiles": {},
    }
    probs = np.array([0.01, 0.05, 0.50, 0.95, 0.99])
    exact_q = p.s0 * np.exp(
        (p.mu - 0.5 * p.sigma**2) * p.maturity
        + p.sigma * math.sqrt(p.maturity) * np.array([STD_NORMAL.inv_cdf(float(q)) for q in probs])
    )
    for label, values in [("exact_formula", exact_q), ("EM_n64", np.quantile(em64, probs)), ("Milstein_n64", np.quantile(mil64, probs))]:
        distribution["quantiles"][label] = [float(v) for v in values]

    plot_gbm_convergence(rows, slope_em, slope_mil, slope_weak)
    plot_gbm_distribution(p, exact, em64, mil64)
    plot_gbm_positivity(rows)
    return {
        "parameters": asdict(p),
        "n_paths": n_paths,
        "rows": rows,
        "slopes": {
            "strong_em": slope_em,
            "strong_em_se": slope_em_se,
            "strong_milstein": slope_mil,
            "strong_milstein_se": slope_mil_se,
            "weak_exact_bias": slope_weak,
            "weak_exact_bias_se": slope_weak_se,
        },
        "matched_cost": matched,
        "distribution": distribution,
    }


def logistic_vol(y: np.ndarray, p: NonAffineParameters) -> np.ndarray:
    """Bounded logistic volatility, evaluated without overflow."""
    positive = y >= 0
    q = np.empty_like(y, dtype=float)
    q[positive] = 1.0 / (1.0 + np.exp(-y[positive]))
    ey = np.exp(y[~positive])
    q[~positive] = ey / (1.0 + ey)
    return p.sigma_min + (p.sigma_max - p.sigma_min) * q


def em_nonaffine_from_increments(
    p: NonAffineParameters, dw1: np.ndarray, dw2: np.ndarray, h: float
) -> tuple[np.ndarray, np.ndarray]:
    """Euler--Maruyama terminal state for supplied correlated increments."""
    n_paths, n_steps = dw1.shape
    x = np.full(n_paths, math.log(p.s0))
    y = np.full(n_paths, p.y0)
    for j in range(n_steps):
        gy = logistic_vol(y, p)
        x += (p.mu - 0.5 * gy**2) * h + gy * dw1[:, j]
        y += p.kappa * (p.theta - y) * h + p.xi * np.sqrt(1.0 + y**2) * dw2[:, j]
    return np.exp(x), y


def aggregate_increments(dw: np.ndarray, factor: int) -> np.ndarray:
    n_paths, n_fine = dw.shape
    if n_fine % factor:
        raise ValueError("Fine grid must be divisible by the coarse-grid factor")
    return dw.reshape(n_paths, n_fine // factor, factor).sum(axis=2)


def run_nonaffine(p: NonAffineParameters, n_paths: int, n_ref: int) -> dict:
    coarse_steps = np.array([16, 32, 64, 128, 256], dtype=int)
    if any(n_ref % n for n in coarse_steps):
        raise ValueError("n_ref must be divisible by every coarse step count")
    batch_size = min(1000, n_paths)
    strong_samples = {int(n): [] for n in coarse_steps}
    weak_samples = {int(n): [] for n in coarse_steps}
    ref_payoffs = []
    all_ref_s = []
    all_ref_y = []
    inc1 = []
    inc2 = []
    rng = np.random.default_rng(SEED + 5000)
    h_ref = p.maturity / n_ref
    for start in range(0, n_paths, batch_size):
        b = min(batch_size, n_paths - start)
        z1 = rng.standard_normal((b, n_ref))
        z2 = rng.standard_normal((b, n_ref))
        dw1 = math.sqrt(h_ref) * z1
        dw2 = math.sqrt(h_ref) * (p.rho * z1 + math.sqrt(1.0 - p.rho**2) * z2)
        inc1.append(dw1[:, : min(8, n_ref)].ravel())
        inc2.append(dw2[:, : min(8, n_ref)].ravel())
        s_ref, y_ref = em_nonaffine_from_increments(p, dw1, dw2, h_ref)
        payoff_ref = np.maximum(s_ref - p.strike, 0.0)
        all_ref_s.append(s_ref)
        all_ref_y.append(y_ref)
        ref_payoffs.append(payoff_ref)
        for n in coarse_steps:
            factor = n_ref // int(n)
            c1 = aggregate_increments(dw1, factor)
            c2 = aggregate_increments(dw2, factor)
            s_coarse, _ = em_nonaffine_from_increments(p, c1, c2, p.maturity / n)
            strong_samples[int(n)].append(np.abs(s_coarse - s_ref))
            weak_samples[int(n)].append(np.maximum(s_coarse - p.strike, 0.0) - payoff_ref)

    rows = []
    for n in coarse_steps:
        strong = np.concatenate(strong_samples[int(n)])
        weak = np.concatenate(weak_samples[int(n)])
        sc = ci95(strong)
        wc = ci95(weak)
        rows.append(
            {
                "n_steps": int(n),
                "h": p.maturity / n,
                "strong_mae_vs_ref": sc[0],
                "strong_ci_low": sc[1],
                "strong_ci_high": sc[2],
                "call_bias_vs_ref": wc[0],
                "call_bias_ci_low": wc[1],
                "call_bias_ci_high": wc[2],
            }
        )
    h = np.array([r["h"] for r in rows])
    strong = np.array([r["strong_mae_vs_ref"] for r in rows])
    slope, slope_se = fitted_slope(h[:-1], strong[:-1])

    a = np.concatenate(inc1)
    b = np.concatenate(inc2)
    increment_diagnostics = {
        "fine_h": h_ref,
        "var_dw1_over_h": float(np.var(a, ddof=1) / h_ref),
        "var_dw2_over_h": float(np.var(b, ddof=1) / h_ref),
        "sample_correlation": float(np.corrcoef(a, b)[0, 1]),
        "target_correlation": p.rho,
    }
    ref_s = np.concatenate(all_ref_s)
    ref_y = np.concatenate(all_ref_y)
    payoff = np.concatenate(ref_payoffs)
    reference = {
        "n_steps": n_ref,
        "mean_s": float(np.mean(ref_s)),
        "se_mean_s": float(np.std(ref_s, ddof=1) / math.sqrt(ref_s.size)),
        "mean_call": float(np.mean(payoff)),
        "se_mean_call": float(np.std(payoff, ddof=1) / math.sqrt(payoff.size)),
        "min_s": float(np.min(ref_s)),
        "max_abs_y": float(np.max(np.abs(ref_y))),
        "finite_fraction": float(np.mean(np.isfinite(ref_s) & np.isfinite(ref_y))),
        "positive_s_fraction": float(np.mean(ref_s > 0.0)),
    }
    refinement = nonaffine_reference_refinement(p, max(3000, n_paths // 5), n_ref)
    plot_nonaffine_convergence(rows, slope)
    plot_nonaffine_paths(p)
    return {
        "parameters": asdict(p),
        "n_paths": n_paths,
        "reference": reference,
        "reference_refinement": refinement,
        "increment_diagnostics": increment_diagnostics,
        "rows": rows,
        "empirical_strong_slope_excluding_finest": slope,
        "empirical_strong_slope_se": slope_se,
    }


def nonaffine_reference_refinement(
    p: NonAffineParameters, n_paths: int, n_ref: int
) -> dict:
    """Compare h_ref with h_ref/2 on a fresh, coupled validation sample."""
    n_fine = 2 * n_ref
    rng = np.random.default_rng(SEED + 9000)
    batch_size = min(500, n_paths)
    differences = []
    for start in range(0, n_paths, batch_size):
        b = min(batch_size, n_paths - start)
        z1 = rng.standard_normal((b, n_fine))
        z2 = rng.standard_normal((b, n_fine))
        hf = p.maturity / n_fine
        d1f = math.sqrt(hf) * z1
        d2f = math.sqrt(hf) * (p.rho * z1 + math.sqrt(1.0 - p.rho**2) * z2)
        sf, _ = em_nonaffine_from_increments(p, d1f, d2f, hf)
        d1c = aggregate_increments(d1f, 2)
        d2c = aggregate_increments(d2f, 2)
        sc, _ = em_nonaffine_from_increments(p, d1c, d2c, 2 * hf)
        differences.append(np.abs(sc - sf))
    diff = np.concatenate(differences)
    est = ci95(diff)
    return {
        "n_paths": n_paths,
        "coarse_reference_steps": n_ref,
        "fine_reference_steps": n_fine,
        "mean_abs_terminal_difference": est[0],
        "ci_low": est[1],
        "ci_high": est[2],
    }


def plot_gbm_convergence(rows: list[dict], slope_em: float, slope_mil: float, slope_weak: float) -> None:
    h = np.array([r["h"] for r in rows])
    em = np.array([r["strong_em"] for r in rows])
    mil = np.array([r["strong_milstein"] for r in rows])
    weak = np.abs([r["weak_bias_exact"] for r in rows])
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.15))
    ax = axes[0]
    ax.loglog(h, em, "o-", color=CB[0], label=f"EM, fit {slope_em:.3f}")
    ax.loglog(h, mil, "s-", color=CB[1], label=f"Milstein, fit {slope_mil:.3f}")
    mask = h <= 0.25
    add_loglog_fit_band(ax, h[mask], em[mask], CB[0], "EM 95% fit band")
    add_loglog_fit_band(ax, h[mask], mil[mask], CB[1], "Milstein 95% fit band")
    href = np.array([h.min(), h.max()])
    ax.loglog(href, em[-1] * (href / h[-1]) ** 0.5, "--", color=CB[5], label="order 1/2")
    ax.loglog(href, mil[-1] * (href / h[-1]), ":", color=CB[5], label="order 1")
    ax.set_xlabel("step size h [year]")
    ax.set_ylabel("mean absolute terminal error [price units]")
    ax.set_title("Strong orders: EM 1/2 and Milstein 1")
    ax.legend()
    ax = axes[1]
    ax.loglog(h, weak, "d-", color=CB[2], label=f"analytic mean bias, fit {slope_weak:.3f}")
    ax.loglog(href, weak[-1] * (href / h[-1]), "--", color=CB[5], label="order 1")
    ax.set_xlabel("step size h [year]")
    ax.set_ylabel(r"$|E[S_N]-E[S(T)]|$ [price units]")
    ax.set_title("Mean weak bias is first order")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "fig01_gbm_convergence.png")
    plt.close(fig)


def plot_gbm_distribution(p: GBMParameters, exact: np.ndarray, em: np.ndarray, mil: np.ndarray) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.15))
    lo, hi = np.quantile(exact, [0.002, 0.998])
    x = np.linspace(lo, hi, 400)
    shape = p.sigma * math.sqrt(p.maturity)
    scale = p.s0 * math.exp((p.mu - 0.5 * p.sigma**2) * p.maturity)
    axes[0].hist(em, bins=70, density=True, alpha=0.42, color=CB[0], label="EM, N=64")
    axes[0].hist(mil, bins=70, density=True, histtype="step", linewidth=1.4, color=CB[1], label="Milstein, N=64")
    density = np.exp(-0.5 * (np.log(x / scale) / shape) ** 2) / (x * shape * math.sqrt(2.0 * math.pi))
    axes[0].plot(x, density, color=CB[5], lw=1.5, label="exact lognormal density")
    axes[0].set_xlabel("terminal asset price $S_T$ [price units]")
    axes[0].set_ylabel("density [1/price unit]")
    axes[0].set_title("Terminal density agrees at N=64")
    axes[0].legend()
    probs = np.linspace(0.01, 0.99, 99)
    q_formula = p.s0 * np.exp(
        (p.mu - 0.5 * p.sigma**2) * p.maturity
        + shape * np.array([STD_NORMAL.inv_cdf(float(q)) for q in probs])
    )
    axes[1].plot(q_formula, np.quantile(em, probs), color=CB[0], label="EM")
    axes[1].plot(q_formula, np.quantile(mil, probs), color=CB[1], label="Milstein")
    axes[1].plot([q_formula.min(), q_formula.max()], [q_formula.min(), q_formula.max()], "--", color=CB[5], label="45-degree line")
    axes[1].set_xlabel("exact lognormal quantile [price units]")
    axes[1].set_ylabel("simulated quantile [price units]")
    axes[1].set_title("Quantile tails expose residual error")
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(OUT / "fig02_gbm_distribution.png")
    plt.close(fig)


def plot_gbm_positivity(rows: list[dict]) -> None:
    h = np.array([r["h"] for r in rows])
    em = np.array([r["negative_path_em_rate"] for r in rows])
    mil = np.array([r["negative_path_milstein_rate"] for r in rows])
    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    floor = 0.5 / max(1, rows[0].get("n_paths", 1))
    ax.semilogy(h, np.maximum(em, 1e-7), "o-", color=CB[0], label="EM: any non-positive multiplier")
    ax.semilogy(h, np.maximum(mil, 1e-7), "s-", color=CB[1], label="Milstein: any non-positive multiplier")
    ax.axhline(1e-7, color=CB[5], ls=":", lw=0.8)
    ax.set_xlabel("step size h [year]")
    ax.set_xscale("log")
    ax.set_ylabel("fraction of paths [proportion]")
    ax.set_title("Positivity failures are a coarse-step risk, not an unconditional guarantee")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "fig03_gbm_positivity.png")
    plt.close(fig)


def plot_nonaffine_convergence(rows: list[dict], slope: float) -> None:
    h = np.array([r["h"] for r in rows])
    strong = np.array([r["strong_mae_vs_ref"] for r in rows])
    slo = np.array([r["strong_ci_low"] for r in rows])
    shi = np.array([r["strong_ci_high"] for r in rows])
    bias = np.array([r["call_bias_vs_ref"] for r in rows])
    blo = np.array([r["call_bias_ci_low"] for r in rows])
    bhi = np.array([r["call_bias_ci_high"] for r in rows])
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.15))
    axes[0].errorbar(h, strong, yerr=[strong - slo, shi - strong], fmt="o-", capsize=2, color=CB[0], label=f"coupled MAE, fit {slope:.3f}")
    add_loglog_fit_band(axes[0], h[:-1], strong[:-1], CB[0], "95% fit band")
    href = np.array([h.min(), h.max()])
    axes[0].loglog(href, strong[-1] * (href / h[-1]) ** 0.5, "--", color=CB[5], label="order 1/2")
    axes[0].set_xscale("log")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("coarse step size h [year]")
    axes[0].set_ylabel("$E|S_T^{(h)}-S_T^{(h_{ref})}|$ [price units]")
    axes[0].set_title("Empirical strong rate is one half")
    axes[0].legend()
    axes[1].errorbar(h, bias, yerr=[bias - blo, bhi - bias], fmt="d-", capsize=2, color=CB[1], label="paired call-payoff bias")
    axes[1].axhline(0.0, color=CB[5], ls="--", lw=1.0)
    axes[1].set_xscale("log")
    axes[1].set_xlabel("coarse step size h [year]")
    axes[1].set_ylabel("payoff difference [price units]")
    axes[1].set_title("Payoff-bias intervals include zero")
    axes[1].legend()
    tick_values = np.array([1.0 / 256.0, 1.0 / 64.0, 1.0 / 16.0])
    for ax in axes:
        ax.set_xticks(tick_values)
        ax.set_xticklabels(["1/256", "1/64", "1/16"])
        ax.xaxis.set_minor_locator(NullLocator())
    fig.tight_layout()
    fig.savefig(OUT / "fig04_nonaffine_convergence.png")
    plt.close(fig)


def plot_nonaffine_paths(p: NonAffineParameters) -> None:
    n_paths, n_steps = 12, 1024
    h = p.maturity / n_steps
    rng = np.random.default_rng(SEED + 12000)
    x = np.full(n_paths, math.log(p.s0))
    y = np.full(n_paths, p.y0)
    s_hist = np.empty((n_steps + 1, n_paths))
    g_hist = np.empty((n_steps + 1, n_paths))
    s_hist[0] = np.exp(x)
    g_hist[0] = logistic_vol(y, p)
    for j in range(n_steps):
        z1 = rng.standard_normal(n_paths)
        z2 = rng.standard_normal(n_paths)
        d1 = math.sqrt(h) * z1
        d2 = math.sqrt(h) * (p.rho * z1 + math.sqrt(1.0 - p.rho**2) * z2)
        gy = logistic_vol(y, p)
        x += (p.mu - 0.5 * gy**2) * h + gy * d1
        y += p.kappa * (p.theta - y) * h + p.xi * np.sqrt(1.0 + y**2) * d2
        s_hist[j + 1] = np.exp(x)
        g_hist[j + 1] = logistic_vol(y, p)
    t = np.linspace(0.0, p.maturity, n_steps + 1)
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.15))
    for k in range(n_paths):
        axes[0].plot(t, s_hist[:, k], lw=0.8, alpha=0.72, color=CB[0])
        axes[1].plot(t, g_hist[:, k], lw=0.8, alpha=0.72, color=CB[1])
    axes[0].set_xlabel("time t [year]")
    axes[0].set_ylabel("asset price $S_t$ [price units]")
    axes[0].set_title("Log-price paths remain positive")
    axes[1].set_xlabel("time t [year]")
    axes[1].set_ylabel("instantaneous volatility $g(Y_t)$ [year$^{-1/2}$]")
    axes[1].set_ylim(p.sigma_min - 0.01, p.sigma_max + 0.01)
    axes[1].axhline(p.sigma_min, color=CB[5], ls=":", lw=0.8)
    axes[1].axhline(p.sigma_max, color=CB[5], ls=":", lw=0.8)
    axes[1].set_title("Logistic volatility remains bounded")
    fig.tight_layout()
    fig.savefig(OUT / "fig05_nonaffine_paths.png")
    plt.close(fig)


def validate(results: dict) -> dict:
    gbm = results["gbm"]
    non = results["nonaffine"]
    checks = {
        "gbm_em_strong_order_in_expected_band": 0.40 <= gbm["slopes"]["strong_em"] <= 0.65,
        "gbm_milstein_strong_order_in_expected_band": 0.85 <= gbm["slopes"]["strong_milstein"] <= 1.15,
        "gbm_weak_order_in_expected_band": 0.90 <= gbm["slopes"]["weak_exact_bias"] <= 1.10,
        "gbm_exact_mean_within_4_mc_se": abs(gbm["distribution"]["exact_sample_mean"] - gbm["distribution"]["exact_mean_formula"])
        <= 4.0 * math.sqrt(gbm["distribution"]["exact_variance_formula"] / gbm["n_paths"]),
        "brownian_variance_1_within_3_percent": abs(non["increment_diagnostics"]["var_dw1_over_h"] - 1.0) < 0.03,
        "brownian_variance_2_within_3_percent": abs(non["increment_diagnostics"]["var_dw2_over_h"] - 1.0) < 0.03,
        "brownian_correlation_within_0_02": abs(non["increment_diagnostics"]["sample_correlation"] - non["increment_diagnostics"]["target_correlation"]) < 0.02,
        "nonaffine_all_paths_finite": non["reference"]["finite_fraction"] == 1.0,
        "nonaffine_all_prices_positive": non["reference"]["positive_s_fraction"] == 1.0,
        "nonaffine_empirical_strong_order_plausible": 0.35 <= non["empirical_strong_slope_excluding_finest"] <= 0.75,
    }
    return {"checks": checks, "all_pass": bool(all(checks.values()))}


def print_summary(results: dict) -> None:
    g = results["gbm"]
    n = results["nonaffine"]
    print("Financial SDE reproducibility run")
    print(f"seed={SEED}")
    print("GBM fitted strong orders: "
          f"EM={g['slopes']['strong_em']:.4f} +/- {g['slopes']['strong_em_se']:.4f}, "
          f"Milstein={g['slopes']['strong_milstein']:.4f} +/- {g['slopes']['strong_milstein_se']:.4f}")
    print(f"GBM analytic weak-bias order={g['slopes']['weak_exact_bias']:.4f} +/- {g['slopes']['weak_exact_bias_se']:.4f}")
    print("Matched strong-MAE cost: " + json.dumps(g["matched_cost"], sort_keys=True))
    print(f"GBM exact terminal mean: formula={g['distribution']['exact_mean_formula']:.6f}, "
          f"sample={g['distribution']['exact_sample_mean']:.6f}")
    print(f"GBM exact terminal variance: formula={g['distribution']['exact_variance_formula']:.6f}, "
          f"sample={g['distribution']['exact_sample_variance']:.6f}")
    d = n["increment_diagnostics"]
    print(f"Increment diagnostics: Var(dW1)/h={d['var_dw1_over_h']:.5f}, "
          f"Var(dW2)/h={d['var_dw2_over_h']:.5f}, Corr={d['sample_correlation']:.5f}")
    print(f"Non-affine empirical strong slope={n['empirical_strong_slope_excluding_finest']:.4f} "
          f"+/- {n['empirical_strong_slope_se']:.4f}")
    print("Non-affine reference: " + json.dumps(n["reference"], sort_keys=True))
    print("Reference refinement: " + json.dumps(n["reference_refinement"], sort_keys=True))
    for name, passed in results["validation"]["checks"].items():
        print(f"{'PASS' if passed else 'FAIL'}: {name}")
    print(f"OVERALL: {'PASS' if results['validation']['all_pass'] else 'FAIL'}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="run a reduced smoke test")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    gbm_paths = 40_000 if args.quick else 300_000
    non_paths = 3_000 if args.quick else 20_000
    n_ref = 512 if args.quick else 2048
    start = time.perf_counter()
    results = {
        "metadata": {
            "seed": SEED,
            "quick_mode": args.quick,
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "numpy": np.__version__,
            "matplotlib": matplotlib.__version__,
            "cost_measure": "time steps (one drift/diffusion coefficient evaluation per path-step); plotting, I/O, and setup excluded",
        },
        "gbm": run_gbm(GBMParameters(), gbm_paths),
        "nonaffine": run_nonaffine(NonAffineParameters(), non_paths, n_ref),
    }
    results["validation"] = validate(results)
    results["metadata"]["wall_time_seconds"] = time.perf_counter() - start
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        print_summary(results)
    output_text = buffer.getvalue()
    print(output_text, end="")
    (OUT / "run_output.txt").write_text(output_text, encoding="utf-8")
    (OUT / "results.json").write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")
    return 0 if results["validation"]["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
