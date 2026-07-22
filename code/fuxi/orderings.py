"""Comparative analysis of hexagram orderings.

The formalization so far concerns the *set* of sixty-four hexagrams and the
group acting on it. Neither depends on how the hexagrams are arranged in a
sequence. This module addresses the arrangement itself, which is where the
Earlier Heaven (Fuxi) and King Wen orderings differ.

Two questions are asked.

1. **Does the King Wen ordering have the pairing structure tradition ascribes
   to it?** The traditional claim is that the sequence consists of thirty-two
   couplets, in which the second hexagram is the vertical reversal of the first,
   except where a hexagram is its own reversal, in which case the couplet is
   completed by the complement instead. This is fully decidable.

2. **How do the orderings compare as codes?** Consecutive hexagrams in a
   sequence differ by some number of lines. The profile of those differences is
   a property of the ordering, and it can be compared against a Gray code, which
   is optimal, and against random orderings, which supply a null.

Nothing here interprets the orderings. The questions are about structure.
"""

from __future__ import annotations

import random as _random
from math import comb

from .encoding import N_HEXAGRAMS, N_LINES, complement, value_to_lines, yang_count


# --------------------------------------------------------------------------
# Traditional operations on a single hexagram
# --------------------------------------------------------------------------

def reverse(value: int) -> int:
    """The hexagram turned upside down (zong gua).

    The bottom line becomes the top line. Under the bottom-first encoding this
    reverses the bit order.
    """
    lines = value_to_lines(value)
    return sum(b << i for i, b in enumerate(reversed(lines)))


def is_palindromic(value: int) -> bool:
    """True when the hexagram is unchanged by vertical reversal."""
    return reverse(value) == value


def palindromic_hexagrams() -> list:
    """The hexagrams that are their own reversal.

    A six-bit string equal to its reverse is determined by its lower three
    bits, so there are exactly 2^3 = 8 of them.
    """
    return [v for v in range(N_HEXAGRAMS) if is_palindromic(v)]


def nuclear(value: int) -> int:
    """The nuclear hexagram (hu gua): lines 2-4 below, lines 3-5 above."""
    b = value_to_lines(value)
    inner = (b[1], b[2], b[3], b[2], b[3], b[4])
    return sum(x << i for i, x in enumerate(inner))


# --------------------------------------------------------------------------
# Reference orderings
# --------------------------------------------------------------------------

def counting_ordering() -> list:
    """Binary counting under the bottom-as-least-significant-bit convention."""
    return list(range(N_HEXAGRAMS))


def fuxi_traditional_ordering() -> list:
    """The classical Earlier Heaven sequence attributed to Shao Yong.

    The traditional trigram order is Qian, Dui, Li, Zhen, Xun, Kan, Gen, Kun,
    which is 7 down to 0 when the *bottom* line is read as the most significant
    bit. The sixty-four hexagram sequence extends this, running from Qian down
    to Kun.

    This is binary counting, but under the opposite bit-weight convention from
    the one this package adopts for the algebra. The two readings are related by
    bit reversal, which is exactly what :func:`reverse` computes on integers.
    Hence position ``p`` holds ``reverse(63 - p)``.
    """
    return [reverse(N_HEXAGRAMS - 1 - p) for p in range(N_HEXAGRAMS)]


def bit_reversal_relation() -> dict:
    """Relate the two readings of the Earlier Heaven arrangement.

    Reading the bottom line as the most significant bit and reading it as the
    least significant bit give two different sequences over the same set. They
    are conjugate by the bit-reversal permutation, and because a bit permutation
    is an isometry of the hypercube, the two sequences have identical
    consecutive-distance profiles.
    """
    counting = counting_ordering()
    traditional = fuxi_traditional_ordering()

    is_isometry = all(
        yang_count(a ^ b) == yang_count(reverse(a) ^ reverse(b))
        for a in range(N_HEXAGRAMS)
        for b in range(N_HEXAGRAMS)
    )
    same_set = sorted(traditional) == sorted(counting)
    same_sequence = traditional == counting
    same_profile = (
        consecutive_distances(traditional)[::-1] == consecutive_distances(counting)
    )

    return {
        "reverse_is_hypercube_isometry": is_isometry,
        "same_underlying_set": same_set,
        "same_sequence": same_sequence,
        "profiles_agree_up_to_direction": same_profile,
        "positions_that_differ": sum(
            1 for a, b in zip(traditional, counting) if a != b
        ),
    }


def gray_ordering() -> list:
    """The reflected binary (Gray) code, in which consecutive values differ by
    exactly one line. This is the optimum for the consecutive-distance profile.
    """
    return [i ^ (i >> 1) for i in range(N_HEXAGRAMS)]


def random_ordering(rng: _random.Random) -> list:
    order = list(range(N_HEXAGRAMS))
    rng.shuffle(order)
    return order


# --------------------------------------------------------------------------
# The pairing claim
# --------------------------------------------------------------------------

def pairing_structure(order) -> dict:
    """Test the couplet claim on an ordering.

    Positions are taken two at a time. For each couplet the relation between the
    two members is classified as reversal, complement, both, or neither.
    """
    if len(order) != N_HEXAGRAMS:
        raise ValueError("ordering must list all 64 hexagrams")
    if sorted(order) != list(range(N_HEXAGRAMS)):
        raise ValueError("ordering must be a permutation of 0..63")

    by_reversal = []
    by_complement = []
    by_neither = []
    palindromic_pairs = []

    for k in range(0, N_HEXAGRAMS, 2):
        a, b = order[k], order[k + 1]
        rev = reverse(a) == b
        comp = complement(a) == b
        if is_palindromic(a):
            palindromic_pairs.append((k // 2 + 1, a, b))
        if rev:
            by_reversal.append((k // 2 + 1, a, b))
        elif comp:
            by_complement.append((k // 2 + 1, a, b))
        else:
            by_neither.append((k // 2 + 1, a, b))

    return {
        "couplets": N_HEXAGRAMS // 2,
        "reversal_pairs": len(by_reversal),
        "complement_pairs": len(by_complement),
        "unexplained_pairs": len(by_neither),
        "claim_holds": len(by_neither) == 0,
        "palindromic_members": len(palindromic_pairs),
        "unexplained_detail": by_neither,
        "complement_detail": by_complement,
    }


def canonical_matching() -> dict:
    """The matching the traditional claim describes.

    Every non-palindromic hexagram is matched to its reversal; every palindromic
    hexagram is matched to its complement. This is checked to be a perfect
    matching rather than assumed: the complement of a palindrome is a
    palindrome, so the eight palindromes close among themselves.
    """
    partner = {}
    for v in range(N_HEXAGRAMS):
        partner[v] = complement(v) if is_palindromic(v) else reverse(v)

    involution = all(partner[partner[v]] == v for v in range(N_HEXAGRAMS))
    fixed_points = [v for v in range(N_HEXAGRAMS) if partner[v] == v]
    pairs = {frozenset((v, partner[v])) for v in range(N_HEXAGRAMS)}

    return {
        "partner": partner,
        "is_involution": involution,
        "fixed_points": fixed_points,
        "n_pairs": len(pairs),
        "is_perfect_matching": involution and not fixed_points and len(pairs) == 32,
        "reversal_pairs": len([p for p in pairs if not is_palindromic(min(p))]),
        "complement_pairs": len([p for p in pairs if is_palindromic(min(p))]),
    }


def pairing_null_probability() -> dict:
    """Exact probability that a uniformly random ordering satisfies the claim.

    If the claim holds, the ordering lists the thirty-two matched pairs
    consecutively. The favourable permutations are counted by choosing an order
    for the thirty-two pairs and an orientation within each, giving
    ``32! * 2^32`` out of ``64!``. Simulation is useless at this magnitude, so
    the value is computed exactly.
    """
    from math import factorial

    favourable = factorial(32) * (2 ** 32)
    total = factorial(N_HEXAGRAMS)
    return {
        "favourable_permutations": favourable,
        "total_permutations": total,
        "probability": favourable / total,
        "log10_probability": _log10_ratio(favourable, total),
    }


def _log10_ratio(a: int, b: int) -> float:
    from math import log10
    return log10(a) - log10(b) if a else float("-inf")


def expected_explained_couplets_random() -> dict:
    """Expected number of couplets a random ordering explains.

    The classifier accepts a couplet when the second member is the reversal or
    the complement of the first, so the number of hexagrams that would complete
    a given first member is the size of ``{reverse(a), complement(a)}`` after
    removing ``a`` itself.
    """
    partners_per_hexagram = []
    for a in range(N_HEXAGRAMS):
        candidates = {reverse(a), complement(a)} - {a}
        partners_per_hexagram.append(len(candidates))
    mean_partners = sum(partners_per_hexagram) / N_HEXAGRAMS
    return {
        "mean_valid_partners": mean_partners,
        "expected_couplets": 32 * mean_partners / (N_HEXAGRAMS - 1),
        "hexagrams_with_two_partners": partners_per_hexagram.count(2),
        "hexagrams_with_one_partner": partners_per_hexagram.count(1),
    }


def pairing_simulation(trials: int, seed: int = 20260722) -> dict:
    """How many couplets random orderings actually explain, for reference."""
    rng = _random.Random(seed)
    best = 0
    total = 0
    for _ in range(trials):
        result = pairing_structure(random_ordering(rng))
        explained = result["reversal_pairs"] + result["complement_pairs"]
        total += explained
        best = max(best, explained)
    return {
        "trials": trials,
        "mean_couplets_explained": total / trials,
        "max_couplets_explained": best,
    }


# --------------------------------------------------------------------------
# Coding profile
# --------------------------------------------------------------------------

def consecutive_distances(order) -> list:
    """Hamming distance between each consecutive pair in the ordering."""
    return [yang_count(order[i] ^ order[i + 1]) for i in range(len(order) - 1)]


def distance_profile(order) -> dict:
    d = consecutive_distances(order)
    n = len(d)
    counts = [0] * (N_LINES + 1)
    for x in d:
        counts[x] += 1
    mean = sum(d) / n
    var = sum((x - mean) ** 2 for x in d) / n
    return {
        "steps": n,
        "total_line_changes": sum(d),
        "mean": mean,
        "variance": var,
        "counts": counts,
        "min": min(d),
        "max": max(d),
        "adjacent_at_distance_one": counts[1],
    }


def random_profile_distribution(trials: int, seed: int = 20260722) -> dict:
    """Null distribution of the mean consecutive distance under random ordering."""
    rng = _random.Random(seed)
    means = []
    for _ in range(trials):
        means.append(distance_profile(random_ordering(rng))["mean"])
    means.sort()
    n = len(means)
    mean_of_means = sum(means) / n
    var = sum((m - mean_of_means) ** 2 for m in means) / n
    return {
        "trials": trials,
        "mean": mean_of_means,
        "stdev": var ** 0.5,
        "p05": means[int(0.05 * n)],
        "p95": means[int(0.95 * n)],
        "min": means[0],
        "max": means[-1],
    }


def expected_random_consecutive_distance() -> float:
    """Mean Hamming distance between two distinct uniform hexagrams.

    A random ordering places an arbitrary distinct hexagram next to each one, so
    this is the expected consecutive distance under the null.
    """
    total = sum(
        comb(N_LINES, k) * k for k in range(N_LINES + 1)
    )  # sum over all partners of a fixed hexagram
    return total / (N_HEXAGRAMS - 1)


def fuxi_total_changes_closed_form() -> int:
    """Total line changes across the binary-counting ordering, in closed form.

    Bit i flips once every 2^(i+1) steps, so the total is the sum of
    floor((2^6 - 1) / 2^i) over i = 0..5.
    """
    return sum((N_HEXAGRAMS - 1) // (1 << i) for i in range(N_LINES))
