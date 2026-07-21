"""Bit-level encoding of the Fuxi (Earlier Heaven / Xiantian) hexagram system.

Convention
----------
A hexagram is six stacked lines. Traditional line names run bottom to top:
initial (chu yao), second, third, fourth, fifth, top (shang yao).

We adopt the *bottom-up* bit-weight convention: the bottom line carries weight
2^0 and the top line carries weight 2^5. Lines are stored bottom-first in a
tuple, so ``lines[0]`` is the bottom line.

Under this convention Kun (all yin) is 0 and Qian (all yang) is 63.

Everything in this module is stdlib-only.
"""

from __future__ import annotations

from itertools import product

N_LINES = 6
N_HEXAGRAMS = 1 << N_LINES  # 64

YIN = 0
YANG = 1


# --------------------------------------------------------------------------
# Core bijection
# --------------------------------------------------------------------------

def lines_to_value(lines) -> int:
    """Map a bottom-first tuple of six bits to its integer value.

    V(h) = sum_{i=1..6} b_i * 2^(i-1), with b_1 the bottom line.
    """
    lines = tuple(lines)
    if len(lines) != N_LINES:
        raise ValueError(f"expected {N_LINES} lines, got {len(lines)}")
    if any(b not in (0, 1) for b in lines):
        raise ValueError("lines must be 0 (yin) or 1 (yang)")
    return sum(b << i for i, b in enumerate(lines))


def value_to_lines(value: int) -> tuple:
    """Inverse of :func:`lines_to_value`. Returns a bottom-first tuple."""
    if not 0 <= value < N_HEXAGRAMS:
        raise ValueError(f"value out of range: {value}")
    return tuple((value >> i) & 1 for i in range(N_LINES))


def yang_count(value: int) -> int:
    """Number of yang lines = Hamming weight = rank in the Boolean lattice."""
    return bin(value).count("1")


def complement(value: int) -> int:
    """The 'inverted' hexagram (pang tong gua): every line flipped."""
    return value ^ (N_HEXAGRAMS - 1)


KUN = 0                    # all yin
QIAN = N_HEXAGRAMS - 1     # all yang, 63


# --------------------------------------------------------------------------
# Shao Yong's doubling method (jia yi bei fa)
# --------------------------------------------------------------------------
#
# The generation is recursive: G(0) = {empty}, and each step splits every
# existing symbol in two by adding one new line. Two placement conventions are
# in circulation; we implement both, because a central claim of the paper is
# that the *set* generated is convention-independent (cf. Maitre 2025) while the
# *enumeration order* is not.

def doubling_top(n: int) -> list:
    """Doubling method placing each new line ABOVE the existing ones.

    The new line becomes the new most-significant bit. The yin branch of the
    whole level is emitted before the yang branch.
    """
    grams = [()]
    for _ in range(n):
        grams = [g + (YIN,) for g in grams] + [g + (YANG,) for g in grams]
    return grams


def doubling_bottom(n: int) -> list:
    """Doubling method placing each new line BELOW the existing ones.

    Existing lines shift up one position; the new line becomes the new
    least-significant bit. Each parent symbol emits its yin child then its
    yang child (depth-first), which is the ordering drawn in the traditional
    bifurcation diagram.
    """
    grams = [()]
    for _ in range(n):
        nxt = []
        for g in grams:
            nxt.append((YIN,) + g)
            nxt.append((YANG,) + g)
        grams = nxt
    return grams


def doubling_values(n: int, placement: str = "top") -> list:
    """Integer values produced by the doubling method, in generation order.

    For n < 6 the partial symbols are valued as n-bit numbers.
    """
    if placement == "top":
        grams = doubling_top(n)
    elif placement == "bottom":
        grams = doubling_bottom(n)
    else:
        raise ValueError("placement must be 'top' or 'bottom'")
    return [sum(b << i for i, b in enumerate(g)) for g in grams]


def all_hexagrams() -> list:
    """All 64 hexagrams as bottom-first line tuples, in value order 0..63."""
    return [value_to_lines(v) for v in range(N_HEXAGRAMS)]


def brute_force_enumeration(n: int) -> set:
    """Independent ground truth: every n-tuple over {yin, yang}."""
    return set(product((YIN, YANG), repeat=n))


# --------------------------------------------------------------------------
# Boolean lattice structure
# --------------------------------------------------------------------------

def meet(a: int, b: int) -> int:
    """Lattice meet = bitwise AND."""
    return a & b


def join(a: int, b: int) -> int:
    """Lattice join = bitwise OR."""
    return a | b


def leq(a: int, b: int) -> bool:
    """Partial order: a <= b iff every yang line of a is yang in b."""
    return (a & b) == a


def rank_distribution() -> list:
    """Number of hexagrams at each Boolean-lattice rank (0..6)."""
    counts = [0] * (N_LINES + 1)
    for v in range(N_HEXAGRAMS):
        counts[yang_count(v)] += 1
    return counts
