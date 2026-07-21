"""Entropy and mutual information for the hexagram system.

All functions accept exact :class:`fractions.Fraction` probabilities as well as
floats. Entropies are returned in bits.
"""

from __future__ import annotations

from fractions import Fraction
from math import log2

from .encoding import N_HEXAGRAMS, N_LINES


def entropy(probabilities) -> float:
    """Shannon entropy in bits of an iterable of probabilities."""
    total = 0.0
    for p in probabilities:
        pf = float(p)
        if pf < 0:
            raise ValueError("negative probability")
        if pf > 0:
            total -= pf * log2(pf)
    return total


def binary_entropy(p) -> float:
    """H_b(p) in bits."""
    return entropy([p, 1 - Fraction(p) if isinstance(p, Fraction) else 1 - float(p)])


def uniform_entropy(n: int) -> float:
    """Entropy of the uniform distribution on n outcomes."""
    return log2(n)


def joint_entropy(joint) -> float:
    """Entropy of a joint distribution given as a mapping or iterable of probabilities."""
    values = joint.values() if hasattr(joint, "values") else joint
    return entropy(values)


def mutual_information(joint) -> float:
    """I(X;Y) in bits from a joint distribution keyed by (x, y) pairs."""
    px: dict = {}
    py: dict = {}
    for (x, y), p in joint.items():
        px[x] = px.get(x, 0) + p
        py[y] = py.get(y, 0) + p
    return entropy(px.values()) + entropy(py.values()) - entropy(joint.values())


# --------------------------------------------------------------------------
# System-level quantities
# --------------------------------------------------------------------------

def hexagram_entropy() -> float:
    """H of a uniformly distributed hexagram: log2(64) = 6 bits."""
    return uniform_entropy(N_HEXAGRAMS)


def mask_entropy(p_change) -> float:
    """H(M) for an independent per-line mutation mask with flip probability p."""
    return N_LINES * binary_entropy(p_change)


def mutual_information_independent_mask(p_change) -> float:
    """I(B; B') under the paper's model: B uniform, M independent of B.

    B' = B XOR M is then uniform, so I = H(B') - H(B'|B) = 6 - H(M).
    """
    return hexagram_entropy() - mask_entropy(p_change)


def mutual_information_from_line_joint(line_joint) -> float:
    """I(B; B') for six independent lines, each with the given joint.

    ``line_joint`` maps (primary_bit, derived_bit) to a probability. Because the
    six lines are cast independently, the whole-hexagram mutual information is
    six times the per-line value.
    """
    return N_LINES * mutual_information(line_joint)
