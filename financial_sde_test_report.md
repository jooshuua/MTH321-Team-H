[financial_sde_test_report.md](https://github.com/user-attachments/files/32998918/financial_sde_test_report.md)
# Financial SDE Testing and Numerical Validation Report

## 1. Test Overview

| Item | Details |
| --- | --- |
| Tester | Hao Dongdong |
| Date | 2026-10-03 |
| Team repository | https://github.com/jooshuua/MTH321-Team-H |
| Commit tested | ef1880737f33764acc016832a8953057e1bc8108 |
| Files tested | Team_H_Code/financial_sde_project.py and Team_H_Code/code/run_all.py |
| Command run | /usr/local/bin/python3.13 code/run_all.py |
| Environment | macOS 14.7.4 (arm64); Python 3.13.7; NumPy 2.3.2; Matplotlib 3.10.9 |
| Run mode and random seed | Full run, without quick mode; main experiment seed: 20260918 |
| Outcome | Exit code 0; all 10 automated checks passed; OVERALL: PASS |

This report covers **numerical testing and reproducibility**: convergence orders, comparison with the exact GBM solution, Brownian-increment statistics, non-affine-model terminal values, and numerical-reference refinement. Figure creation and visual inspection are outside the scope of this report.

## 2. Test Method

I ran the full experiment in an isolated local directory using the main script and runner from the fixed team commit above. Main script source:

https://raw.githubusercontent.com/jooshuua/MTH321-Team-H/ef1880737f33764acc016832a8953057e1bc8108/Team_H_Code/financial_sde_project.py

Runner source:

https://raw.githubusercontent.com/jooshuua/MTH321-Team-H/ef1880737f33764acc016832a8953057e1bc8108/Team_H_Code/code/run_all.py

The fixed random seed makes the numerical results reproducible. The main GBM experiment uses 300,000 paths. The non-affine model uses 20,000 paths and a 2,048-step reference grid. The program writes its complete numerical results and validation status to generated/results.json, and its console summary to generated/run_output.txt. It returns exit code 0 when validation passes and a nonzero exit code when it fails.

GBM has an exact path solution and exact terminal moments, so it provides a benchmark for the numerical algorithms. The non-affine model has no analytic path solution. Its test couples coarse-grid and fine-grid paths using the same Brownian increments and treats the fine-grid simulation as a numerical reference. Because this reference still has discretization error, I also checked sensitivity to reference-grid refinement.

## 3. Ten Automated Checks and Observed Results

The acceptance criteria below come from the validate() function at the tested commit. Observed values come from this run's results.json. The ± values reported with fitted slopes are the program's fitted standard errors.

| No. | Check | Acceptance criterion | Observed value | Result |
| --- | --- | --- | --- | --- |
| 1 | GBM Euler–Maruyama strong convergence order | 0.40 ≤ slope ≤ 0.65 | 0.489865 ± 0.002592 | PASS |
| 2 | GBM Milstein strong convergence order | 0.85 ≤ slope ≤ 1.15 | 0.909854 ± 0.016691 | PASS |
| 3 | GBM analytic weak-bias order | 0.90 ≤ slope ≤ 1.10 | 0.998224 ± 0.000432 | PASS |
| 4 | GBM exact terminal mean | Difference between sample and formula means ≤ 4 × Monte Carlo standard error | Formula: 105.127110; sample: 105.088894; difference: 0.038216; threshold: 0.319799 | PASS |
| 5 | Variance of the first Brownian increment | Deviation from theoretical ratio 1 < 0.03 | Var(ΔW₁)/h = 1.005260 | PASS |
| 6 | Variance of the second Brownian increment | Deviation from theoretical ratio 1 < 0.03 | Var(ΔW₂)/h = 1.003463 | PASS |
| 7 | Correlation of Brownian increments | Difference from target −0.7 < 0.02 | Sample correlation: −0.701848; difference: 0.001848 | PASS |
| 8 | Finite non-affine reference terminal values | finite_fraction = 1.0 | 1.0 | PASS |
| 9 | Positive non-affine reference terminal prices | positive_s_fraction = 1.0 | 1.0; minimum terminal price: 23.146331 | PASS |
| 10 | Non-affine empirical strong convergence order | 0.35 ≤ slope ≤ 0.75 | 0.511133 ± 0.004670 | PASS |

The fractions in checks 8 and 9 are calculated from **terminal values in the reference simulation**. On their own, they do not establish that every intermediate state of every path is finite and positive. The result for check 2 falls within the code's prescribed range, but 0.909854 is not equal to the theoretical limiting order of 1; it should not be described as having “exactly achieved first order.”

## 4. Additional Numerical Diagnostics

### 4.1 GBM Exact Moments and Cost at a Matched Error Target

The formula gives an exact terminal variance of 1917.591686, compared with a simulated sample variance of 1915.728882, a relative difference of approximately 0.097%. This variance comparison is an additional diagnostic, not a separate one of the 10 automated PASS checks.

At a target terminal mean absolute error (MAE) of 0.85, EM first meets the target with 128 steps and an MAE of 0.838329; Milstein meets it with 2 steps and an MAE of 0.754327. The reported 64:1 ratio compares only the **number of time steps per path**. It does not mean that Milstein ran 64 times faster in wall-clock time.

### 4.2 Non-Affine Model Reference Terminal Values

In the 2,048-step reference simulation, the mean terminal price is 105.018150 with a Monte Carlo standard error of 0.214333. The mean call-option payoff is 14.483711 with a standard error of 0.150903. The observed Brownian-increment correlation is −0.701848, close to the model's target of −0.7.

### 4.3 Numerical Reference Refinement

The program uses 4,000 new coupled paths and random seed 20269918 to compare reference grids with 2,048, 4,096, and 8,192 steps:

| Grid pair | Mean absolute terminal difference | Program-reported 95% interval |
| --- | ---: | --- |
| 2,048 vs. 4,096 steps | 0.057485 | [0.055953, 0.059016] |
| 4,096 vs. 8,192 steps | 0.040731 | [0.039653, 0.041809] |

The second adjacent-reference difference is 0.708551 times the first, a decrease of approximately 29.1%. When the strong-error slope is estimated using different reference grids, its maximum change relative to the base estimate is 0.011662. These results support stability under reference refinement. However, the reference remains a numerical solution, so this result does not prove an exact weak convergence order for the non-affine model.

## 5. Reproducibility Check and Evidence

The full run exited normally. In results.json, validation.all_pass is true and all 10 entries in checks are true. The final line of run_output.txt is OVERALL: PASS. On a repeat run, the console summary matched the previous local run character for character. Timing fields in results.json can change between runs, so byte-for-byte equality of the two JSON files is not required.

The main evidence available for review is:

- financial_sde_test_report.md: this testing report.
- run_output.txt: numerical console summary and individual PASS/FAIL outcomes.
- results.json: experiment parameters, complete numerical results, observed values associated with the validation criteria, and validation status.

## 6. Limitations and Conditions for Retesting

1. This run used NumPy 2.3.2 and Matplotlib 3.10.9. The repository README lists NumPy 2.0.2 and Matplotlib 3.9.4. If the course requires reproduction with exactly the README versions, those versions must be tested in a separate environment. This report must not be presented as a test using the README's specified library versions.
2. I ran the fixed commit in an isolated local directory, not in GitHub Actions.
3. OVERALL: PASS means that the program's 10 built-in threshold checks passed. It does not replace an independent review of every mathematical derivation, statistical method, or modeling assumption.
4. If the team changes the code, dependencies, or experiment parameters, record the new commit and rerun the tests for that version.

## 7. Conclusion

For the fixed commit, random seeds, and local software environment stated above, the GBM convergence-order checks and exact-mean comparison, Brownian-increment statistics, non-affine reference-terminal-value checks, and empirical strong convergence-order check all passed the program's 10 acceptance criteria. The adjacent reference-terminal differences decreased after grid refinement. **Final test result: OVERALL: PASS.**
