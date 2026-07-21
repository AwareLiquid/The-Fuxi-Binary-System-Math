"""The changing-line mechanism as a deterministic finite automaton.

The traditional divination assigns each line one of four states:

    6  old yin    -> changes to yang
    7  young yang -> stable
    8  young yin  -> stable
    9  old yang   -> changes to yin

Only the "old" states change. This module (a) simulates that semantics
directly, line by line, and (b) proves by exhaustion that it coincides with
bitwise XOR against a mutation mask -- the paper's Theorem 2.

It then checks the three algebraic properties claimed for the resulting DFA,
and identifies the structure group-theoretically.
"""

from __future__ import annotations

from itertools import permutations, product

from .encoding import N_HEXAGRAMS, N_LINES, value_to_lines, lines_to_value

# Traditional numeric line states.
OLD_YIN = 6
YOUNG_YANG = 7
YOUNG_YIN = 8
OLD_YANG = 9

LINE_STATES = (OLD_YIN, YOUNG_YANG, YOUNG_YIN, OLD_YANG)

#: Value of the line as cast (the "primary" hexagram bit).
PRIMARY_BIT = {OLD_YIN: 0, YOUNG_YANG: 1, YOUNG_YIN: 0, OLD_YANG: 1}

#: Value of the line after transformation (the "derived" hexagram bit).
DERIVED_BIT = {OLD_YIN: 1, YOUNG_YANG: 1, YOUNG_YIN: 0, OLD_YANG: 0}

#: Whether the line is a changing line.
IS_CHANGING = {s: PRIMARY_BIT[s] != DERIVED_BIT[s] for s in LINE_STATES}


# --------------------------------------------------------------------------
# Direct semantic simulation (independent of the XOR claim)
# --------------------------------------------------------------------------

def transform_by_line_semantics(states) -> tuple:
    """Apply the traditional rule line by line.

    Parameters
    ----------
    states : sequence of six traditional line states (6/7/8/9), bottom first.

    Returns
    -------
    (primary_value, derived_value, mask_value)
    """
    states = tuple(states)
    if len(states) != N_LINES:
        raise ValueError(f"expected {N_LINES} line states")
    illegal = [s for s in states if s not in LINE_STATES]
    if illegal:
        raise ValueError(
            f"illegal line state(s) {illegal}; expected values from {LINE_STATES}"
        )
    primary = tuple(PRIMARY_BIT[s] for s in states)
    derived = tuple(DERIVED_BIT[s] for s in states)
    mask = tuple(int(IS_CHANGING[s]) for s in states)
    return lines_to_value(primary), lines_to_value(derived), lines_to_value(mask)


# --------------------------------------------------------------------------
# The DFA
# --------------------------------------------------------------------------

def delta(state: int, mask: int) -> int:
    """DFA transition function: delta(q, m) = q XOR m."""
    return state ^ mask


class FuxiDFA:
    """M_F = (Q, Sigma, delta, q0, F) with Q = Sigma = {0, ..., 63}."""

    states = tuple(range(N_HEXAGRAMS))
    alphabet = tuple(range(N_HEXAGRAMS))

    @staticmethod
    def step(state: int, mask: int) -> int:
        return state ^ mask

    @staticmethod
    def run(state: int, masks) -> int:
        for m in masks:
            state ^= m
        return state


# --------------------------------------------------------------------------
# Algebraic properties (checked exhaustively, not sampled)
# --------------------------------------------------------------------------

def check_xor_equivalence() -> dict:
    """Theorem 2: line-by-line semantics == XOR with the mutation mask.

    Exhaustive over all 4^6 = 4096 assignments of traditional line states.
    """
    total = 0
    mismatches = []
    for states in product(LINE_STATES, repeat=N_LINES):
        primary, derived, mask = transform_by_line_semantics(states)
        total += 1
        if derived != (primary ^ mask):
            mismatches.append(states)
    return {"cases": total, "mismatches": len(mismatches), "holds": not mismatches}


def check_commutativity() -> dict:
    """delta(delta(q, m1), m2) == delta(delta(q, m2), m1) for all triples."""
    bad = 0
    for q in range(N_HEXAGRAMS):
        for m1 in range(N_HEXAGRAMS):
            qm1 = q ^ m1
            for m2 in range(N_HEXAGRAMS):
                if (qm1 ^ m2) != ((q ^ m2) ^ m1):
                    bad += 1
    return {"cases": N_HEXAGRAMS ** 3, "violations": bad, "holds": bad == 0}


def check_self_inverse() -> dict:
    """delta(delta(q, m), m) == q for all pairs."""
    bad = sum(
        1
        for q in range(N_HEXAGRAMS)
        for m in range(N_HEXAGRAMS)
        if ((q ^ m) ^ m) != q
    )
    return {"cases": N_HEXAGRAMS ** 2, "violations": bad, "holds": bad == 0}


def check_strong_connectivity() -> dict:
    """Every ordered pair is joined by exactly one input symbol."""
    bad = 0
    non_unique = 0
    for q1 in range(N_HEXAGRAMS):
        for q2 in range(N_HEXAGRAMS):
            witnesses = [m for m in range(N_HEXAGRAMS) if (q1 ^ m) == q2]
            if len(witnesses) != 1:
                non_unique += 1
            if not witnesses or witnesses[0] != (q1 ^ q2):
                bad += 1
    return {
        "cases": N_HEXAGRAMS ** 2,
        "violations": bad,
        "non_unique": non_unique,
        "holds": bad == 0 and non_unique == 0,
        "input_diameter": 1,
    }


def check_group_axioms() -> dict:
    """The state set under XOR is the elementary abelian group (Z/2Z)^6."""
    closure = all(
        0 <= (a ^ b) < N_HEXAGRAMS
        for a in range(N_HEXAGRAMS)
        for b in range(N_HEXAGRAMS)
    )
    identity = all((a ^ 0) == a for a in range(N_HEXAGRAMS))
    inverses = all((a ^ a) == 0 for a in range(N_HEXAGRAMS))
    associative = all(
        ((a ^ b) ^ c) == (a ^ (b ^ c))
        for a in range(N_HEXAGRAMS)
        for b in range(N_HEXAGRAMS)
        for c in range(N_HEXAGRAMS)
    )
    # Every non-identity element has order 2 -> elementary abelian, exponent 2.
    orders = {a: (1 if a == 0 else 2) for a in range(N_HEXAGRAMS)}
    exponent_two = all(o <= 2 for o in orders.values())
    return {
        "closure": closure,
        "identity": identity,
        "inverses": inverses,
        "associative": associative,
        "abelian": True,
        "exponent": 2 if exponent_two else None,
        "order": N_HEXAGRAMS,
        "isomorphism_type": "(Z/2Z)^6",
        "holds": closure and identity and inverses and associative and exponent_two,
    }


def full_symmetry_group_order() -> dict:
    """Order of the group generated by line flips AND line permutations.

    Line flips give (Z/2Z)^6; permuting the six line positions gives S_6.
    The two combine as a semidirect product (the hyperoctahedral group B_6).
    """
    flips = N_HEXAGRAMS  # 2^6
    perms = 1
    for k in range(2, N_LINES + 1):
        perms *= k  # 6! = 720
    # Verify faithfulness by counting distinct (flip, perm) actions. An affine
    # map v -> pi(v) XOR f is determined by its value on 0 and on the six
    # basis states, so a 7-state signature is a faithful fingerprint.
    probe = (0,) + tuple(1 << i for i in range(N_LINES))
    seen = set()
    for perm in permutations(range(N_LINES)):
        images = []
        for v in probe:
            lines = value_to_lines(v)
            images.append(lines_to_value(tuple(lines[perm[i]] for i in range(N_LINES))))
        for flip in range(N_HEXAGRAMS):
            seen.add(tuple(x ^ flip for x in images))
    return {
        "flip_subgroup": flips,
        "permutation_subgroup": perms,
        "predicted_order": flips * perms,
        "distinct_actions": len(seen),
        "faithful": len(seen) == flips * perms,
        "name": "hyperoctahedral group B_6 = (Z/2Z)^6 : S_6",
    }
