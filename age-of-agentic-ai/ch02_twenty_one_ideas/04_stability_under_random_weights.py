# Strategic HR in the Age of Agentic AI, Chapter 2: Twenty-One Ideas
# Listing: Stability Under Random Weights (Under the Hood)
# Dirichlet draws give every weighting an equal chance. A case that keeps its place in most draws is robust to the argument about weights.

import numpy as np

DOUBLED = [7, 10]       # time to first proof; OKR impact and money

def book_score(S: np.ndarray) -> np.ndarray:
    """S: cases x 11 parameters, each scored 0 to 4. Maximum 52."""
    return S.sum(axis=1) + S[:, DOUBLED].sum(axis=1)

def stays_in_top(S, top=18, draws=5000, seed=2026):
    rng = np.random.default_rng(seed)
    hits = np.zeros(len(S))
    for _ in range(draws):
        w = rng.dirichlet(np.ones(S.shape[1]))    # one random weighting
        rank = (-(S @ w)).argsort().argsort()      # 0 is best
        hits += rank < top
    return hits / draws        # share of weightings that keep each case
