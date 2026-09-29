# Reliable Numerical Simulation of Financial SDEs

Project 1, Financial SDE extension pathway, Team H.

This package contains the complete reproducible code for the GBM and
non-affine stochastic-volatility experiments reported in the team report.
It generates all seven report figures, the numerical results, the console
summary, and the automatic validation checks from one command.

## Requirements

- Python 3.10 or later
- NumPy 2.0.2
- Matplotlib 3.9.4

Install the Python dependencies from the project root:

```bash
python -m pip install -r requirements.txt
```

## Run the project

Run the reduced smoke test first:

```bash
python code/run_all.py --quick
```

The quick mode checks that the complete workflow runs, but its reduced path
counts and reference grid must not be used as the source of report values.

Reproduce the final report results with:

```bash
python code/run_all.py
```

The full run uses the fixed seed `20260918`, 300,000 GBM paths, 20,000
non-affine paths, and a 2048-step main numerical reference. It also performs
the independent 2048-to-4096-to-8192 reference-refinement experiment on 4,000
fresh coupled paths.

The command returns exit status 0 only when every automatic validation check
passes.

## Outputs

All outputs are overwritten in `generated/` using fixed file names:

- `fig01_gbm_convergence.png`: GBM strong and weak convergence.
- `fig02_gbm_distribution.png`: terminal density and quantile validation.
- `fig03_gbm_positivity.png`: coarse-grid positivity stress test.
- `fig04_nonaffine_convergence.png`: non-affine strong error and payoff bias.
- `fig05_nonaffine_paths.png`: representative price and volatility paths.
- `fig06_reference_sensitivity.png`: numerical-reference refinement checks.
- `fig07_gbm_cost_accuracy.png`: matched-accuracy error-versus-cost comparison.
- `results.json`: parameters, gridwise results, confidence intervals, and
  validation data.
- `run_output.txt`: human-readable summary and PASS/FAIL results.

## Reproducibility and cost definition

All pseudo-random number generators use deterministic seeds. The program uses
paths relative to `financial_sde_project.py`; it contains no machine-specific
absolute paths.

The matched-accuracy cost measure is the number of time steps per path. It
excludes plotting, file I/O, setup, compilation, vector-allocation overhead,
hardware effects, and the extra arithmetic in a Milstein step. Therefore, the
reported 64:1 ratio is a step-count comparison and not a claim of a 64-fold
wall-clock speedup.

## Package structure

```text
Team_H_Code/
|-- README.md
|-- requirements.txt
|-- .gitignore
|-- financial_sde_project.py
|-- code/
|   `-- run_all.py
`-- generated/
    |-- fig01_gbm_convergence.png
    |-- fig02_gbm_distribution.png
    |-- fig03_gbm_positivity.png
    |-- fig04_nonaffine_convergence.png
    |-- fig05_nonaffine_paths.png
    |-- fig06_reference_sensitivity.png
    |-- fig07_gbm_cost_accuracy.png
    |-- results.json
    `-- run_output.txt
```

`code/run_all.py` is the required single entry point. It locates and runs the
main experiment module without depending on the current machine's directory
layout.
