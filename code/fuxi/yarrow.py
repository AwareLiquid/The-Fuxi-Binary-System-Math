"""The yarrow-stalk divination procedure (da yan shi fa) as a probability model.

The classical procedure produces one line through three "changes" (bian):

    Start with 50 stalks, set one aside permanently -> 49 in play.
    Each change:
        1. Split the working pile into a left and a right heap at random.
        2. Take one stalk from the right heap and hold it.
        3. Count the left heap off in fours; keep the remainder (4 if divisible).
        4. Count the right heap off in fours; keep the remainder (4 if divisible).
        5. Set aside 1 + r_left + r_right.
    After three changes the remainder divided by four is 6, 7, 8, or 9.

Two probability models are implemented:

``idealized``
    The textbook model: the first change sets aside 5 with probability 3/4 and
    9 with probability 1/4; the second and third set aside 4 or 8 with
    probability 1/2 each. This assumes the left-heap size is exactly uniform
    modulo 4.

``exact``
    Enumerates every admissible split point under a uniform random split. This
    is exactly uniform mod 4 only when the working pile minus one is divisible
    by four, which holds for the first change (48) but NOT for the second or
    third. The exact model therefore departs slightly from the textbook values.

All probabilities are computed with :class:`fractions.Fraction`, so the results
are exact rationals rather than floating-point approximations.
"""

from __future__ import annotations

import random
from fractions import Fraction

from .automaton import OLD_YIN, OLD_YANG, YOUNG_YIN, YOUNG_YANG

INITIAL_STALKS = 49
N_CHANGES = 3

#: Textbook line-state probabilities, as asserted in the literature.
IDEALIZED_LINE_PROBABILITIES = {
    OLD_YIN: Fraction(1, 16),      # 6
    YOUNG_YANG: Fraction(5, 16),   # 7
    YOUNG_YIN: Fraction(7, 16),    # 8
    OLD_YANG: Fraction(3, 16),     # 9
}


# --------------------------------------------------------------------------
# One change
# --------------------------------------------------------------------------

def _remainder_mod_four(count: int) -> int:
    """Count off in fours, keeping 4 rather than 0 as the remainder."""
    if count == 0:
        return 0
    r = count % 4
    return 4 if r == 0 else r


def set_aside(n: int, left: int) -> int:
    """Stalks set aside in one change, given pile ``n`` split with ``left`` on the left."""
    right = n - left
    right_after_pull = right - 1
    r_left = _remainder_mod_four(left)
    r_right = _remainder_mod_four(right_after_pull)
    return 1 + r_left + r_right


def stage_outcomes_exact(n: int, min_heap: int = 2) -> dict:
    """Exact distribution of the set-aside amount under a uniform random split.

    The split point ``left`` is taken uniform on the admissible range. With
    ``min_heap = 2`` both heaps keep at least two stalks, so the right heap is
    still non-empty after one stalk is pulled from it. ``min_heap = 1`` admits
    the degenerate split that empties the right heap.

    Exact uniformity of ``left`` modulo four -- the assumption behind the
    textbook probabilities -- holds only when the number of admissible split
    points is divisible by four. That is generally false, which is why this
    model departs slightly from :func:`stage_outcomes_idealized`.
    """
    counts = {}
    lo, hi = min_heap, n - min_heap
    for left in range(lo, hi + 1):
        s = set_aside(n, left)
        counts[s] = counts.get(s, 0) + 1
    total = hi - lo + 1
    return {k: Fraction(v, total) for k, v in sorted(counts.items())}


def stage_outcomes_idealized(n: int, change_index: int) -> dict:
    """Textbook stage distribution."""
    if change_index == 0:
        return {5: Fraction(3, 4), 9: Fraction(1, 4)}
    return {4: Fraction(1, 2), 8: Fraction(1, 2)}


# --------------------------------------------------------------------------
# Three changes -> one line
# --------------------------------------------------------------------------

def line_state_distribution(model: str = "idealized", min_heap: int = 2) -> dict:
    """Exact distribution over the four traditional line states {6, 7, 8, 9}."""
    if model not in ("idealized", "exact"):
        raise ValueError("model must be 'idealized' or 'exact'")

    dist: dict = {}

    def recurse(n: int, change_index: int, prob: Fraction) -> None:
        if change_index == N_CHANGES:
            if n % 4 != 0:
                raise AssertionError(f"final pile {n} not divisible by four")
            state = n // 4
            if state not in (OLD_YIN, YOUNG_YANG, YOUNG_YIN, OLD_YANG):
                raise AssertionError(f"illegal line state {state}")
            dist[state] = dist.get(state, Fraction(0)) + prob
            return
        if model == "exact":
            outcomes = stage_outcomes_exact(n, min_heap=min_heap)
        else:
            outcomes = stage_outcomes_idealized(n, change_index)
        for amount, p in outcomes.items():
            recurse(n - amount, change_index + 1, prob * p)

    recurse(INITIAL_STALKS, 0, Fraction(1))
    return dict(sorted(dist.items()))


# --------------------------------------------------------------------------
# Monte Carlo over the physical procedure
# --------------------------------------------------------------------------

def simulate_line(rng: random.Random, min_heap: int = 2) -> int:
    """Simulate one line by actually splitting the pile at random."""
    n = INITIAL_STALKS
    for _ in range(N_CHANGES):
        left = rng.randint(min_heap, n - min_heap)
        n -= set_aside(n, left)
    return n // 4


def simulate_line_residue_uniform(rng: random.Random) -> int:
    """Simulate under the textbook assumption that the split is uniform mod 4.

    Rather than choosing a split point, this draws the left-heap residue class
    uniformly, which is the symmetry assumption the classical derivation makes.
    """
    n = INITIAL_STALKS
    for _ in range(N_CHANGES):
        residue = rng.randrange(4)
        left = next(
            L for L in range(4, n - 4) if L % 4 == residue
        )
        n -= set_aside(n, left)
    return n // 4


def monte_carlo_line_states(
    trials: int = 1_000_000, seed: int = 20260722, mode: str = "uniform_split"
) -> dict:
    """Empirical line-state frequencies from a direct simulation of the procedure."""
    rng = random.Random(seed)
    draw = simulate_line if mode == "uniform_split" else simulate_line_residue_uniform
    counts = {OLD_YIN: 0, YOUNG_YANG: 0, YOUNG_YIN: 0, OLD_YANG: 0}
    for _ in range(trials):
        counts[draw(rng)] += 1
    return {k: v / trials for k, v in sorted(counts.items())}


# --------------------------------------------------------------------------
# Derived quantities
# --------------------------------------------------------------------------

def derived_quantities(dist: dict) -> dict:
    """Marginals and conditionals implied by a line-state distribution.

    This is where the paper's Markov model is put under stress. The joint
    distribution of (primary bit, derived bit) is exactly the four line-state
    probabilities:

        (yin,  yin ) = P(8)   young yin    -- stays yin
        (yin,  yang) = P(6)   old yin      -- changes to yang
        (yang, yin ) = P(9)   old yang     -- changes to yin
        (yang, yang) = P(7)   young yang   -- stays yang

    From that joint one reads off, in particular, P(change | yang) and
    P(change | yin), which the paper implicitly assumes are equal.
    """
    p6, p7, p8, p9 = dist[OLD_YIN], dist[YOUNG_YANG], dist[YOUNG_YIN], dist[OLD_YANG]

    p_yang_primary = p7 + p9
    p_yin_primary = p6 + p8
    p_yang_derived = p6 + p7
    p_change = p6 + p9

    return {
        "p_primary_yang": p_yang_primary,
        "p_primary_yin": p_yin_primary,
        "p_derived_yang": p_yang_derived,
        "p_change": p_change,
        "expected_changing_lines": 6 * p_change,
        "p_change_given_yang": p9 / p_yang_primary if p_yang_primary else None,
        "p_change_given_yin": p6 / p_yin_primary if p_yin_primary else None,
        "mask_independent_of_state": (
            p_yang_primary != 0
            and p_yin_primary != 0
            and p9 / p_yang_primary == p6 / p_yin_primary
        ),
        "joint": {
            ("yin", "yin"): p8,
            ("yin", "yang"): p6,
            ("yang", "yin"): p9,
            ("yang", "yang"): p7,
        },
    }
