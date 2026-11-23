# Strategic HR in the Age of Agentic AI, Chapter 9: The Pay Gap
# Listing: Two Controls, One Function (Under the Hood)
# Log pay makes the coefficient a percentage. Use robust or clustered errors when cells differ in size; the plain version is shown for clarity.

import numpy as np

def gap_estimate(log_pay, female, controls):
    """OLS on log pay. Returns the female coefficient as a percentage gap
    and a 95% interval. controls: one-hot matrix (grade or job-value band)."""
    X = np.column_stack([np.ones(len(log_pay)), female, controls])
    beta, *_ = np.linalg.lstsq(X, log_pay, rcond=None)
    resid = log_pay - X @ beta
    dof = len(log_pay) - np.linalg.matrix_rank(X)
    cov = (resid @ resid / dof) * np.linalg.pinv(X.T @ X)
    se = np.sqrt(cov[1, 1])
    pct = lambda b: 100 * (np.exp(b) - 1)
    return pct(beta[1]), (pct(beta[1] - 1.96 * se), pct(beta[1] + 1.96 * se))

# run twice, report both
by_grade = gap_estimate(log_pay, female, grade_dummies)
by_value = gap_estimate(log_pay, female, job_value_dummies)
