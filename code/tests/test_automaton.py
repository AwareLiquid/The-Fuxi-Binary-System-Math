"""Tests for :mod:`fuxi.automaton`.

The traditional line states are

    6  old yin    -> primary yin,  derived yang  (changing)
    7  young yang -> primary yang, derived yang  (stable)
    8  young yin  -> primary yin,  derived yin   (stable)
    9  old yang   -> primary yang, derived yin   (changing)

The module's central claim (Theorem 2) is that applying this rule line by line
is the same as XOR-ing the primary hexagram with the mask of changing lines.

Everything here is integer arithmetic, so all assertions are exact.
"""

from __future__ import annotations

from itertools import product

import pytest

from fuxi import automaton
from fuxi.encoding import N_HEXAGRAMS, N_LINES


# --------------------------------------------------------------------------
# The four line states
# --------------------------------------------------------------------------

def test_line_state_tables_agree_with_the_traditional_semantics():
    assert automaton.LINE_STATES == (6, 7, 8, 9)
    assert automaton.PRIMARY_BIT == {6: 0, 7: 1, 8: 0, 9: 1}
    assert automaton.DERIVED_BIT == {6: 1, 7: 1, 8: 0, 9: 0}
    # Only the "old" states 6 and 9 change.
    assert automaton.IS_CHANGING == {6: True, 7: False, 8: False, 9: True}


# --------------------------------------------------------------------------
# Independent re-derivation of transform_by_line_semantics
# --------------------------------------------------------------------------
#
# Each case below is worked out by hand from the four-state table above,
# bottom line first. For states s = (s1..s6):
#
#   primary bit b_i  = 0 for s in {6, 8}, 1 for s in {7, 9}
#   derived bit b'_i = 1 for s in {6, 7}, 0 for s in {8, 9}
#   mask bit m_i     = 1 for s in {6, 9}, 0 for s in {7, 8}
#
# and the integer value is sum_i bit_i * 2^(i-1) with i = 1 the bottom line.

HAND_WORKED_CASES = [
    # states                (primary, derived, mask)  -- derivation in comment
    # all young yang: every line yang and stable
    ((7, 7, 7, 7, 7, 7), (63, 63, 0)),
    # all young yin: every line yin and stable
    ((8, 8, 8, 8, 8, 8), (0, 0, 0)),
    # all old yin: Kun cast, every line changes, becomes Qian
    ((6, 6, 6, 6, 6, 6), (0, 63, 63)),
    # all old yang: Qian cast, every line changes, becomes Kun
    ((9, 9, 9, 9, 9, 9), (63, 0, 63)),
    # (6,7,8,9,7,8)
    #   primary bits (0,1,0,1,1,0) -> 2 + 8 + 16          = 26
    #   derived bits (1,1,0,0,1,0) -> 1 + 2 + 16          = 19
    #   mask bits    (1,0,0,1,0,0) -> 1 + 8               = 9
    #   check 26 XOR 9 = 011010 XOR 001001 = 010011 = 19
    ((6, 7, 8, 9, 7, 8), (26, 19, 9)),
    # (9,9,6,6,8,7)
    #   primary bits (1,1,0,0,0,1) -> 1 + 2 + 32          = 35
    #   derived bits (0,0,1,1,0,1) -> 4 + 8 + 32          = 44
    #   mask bits    (1,1,1,1,0,0) -> 1 + 2 + 4 + 8       = 15
    #   check 35 XOR 15 = 100011 XOR 001111 = 101100 = 44
    ((9, 9, 6, 6, 8, 7), (35, 44, 15)),
    # (8,9,7,6,9,8)
    #   primary bits (0,1,1,0,1,0) -> 2 + 4 + 16          = 22
    #   derived bits (0,0,1,1,0,0) -> 4 + 8               = 12
    #   mask bits    (0,1,0,1,1,0) -> 2 + 8 + 16          = 26
    #   check 22 XOR 26 = 010110 XOR 011010 = 001100 = 12
    ((8, 9, 7, 6, 9, 8), (22, 12, 26)),
    # (6,8,8,8,8,8): only the bottom line is old yin
    #   primary bits (0,0,0,0,0,0) -> 0
    #   derived bits (1,0,0,0,0,0) -> 1
    #   mask bits    (1,0,0,0,0,0) -> 1
    ((6, 8, 8, 8, 8, 8), (0, 1, 1)),
    # (7,7,7,7,7,9): only the top line is old yang
    #   primary bits (1,1,1,1,1,1) -> 63
    #   derived bits (1,1,1,1,1,0) -> 31
    #   mask bits    (0,0,0,0,0,1) -> 32
    ((7, 7, 7, 7, 7, 9), (63, 31, 32)),
]


@pytest.mark.parametrize("states,expected", HAND_WORKED_CASES)
def test_transform_by_line_semantics_matches_hand_worked_table(states, expected):
    assert automaton.transform_by_line_semantics(states) == expected


@pytest.mark.parametrize("states,expected", HAND_WORKED_CASES)
def test_hand_worked_cases_also_satisfy_the_xor_identity(states, expected):
    primary, derived, mask = expected
    assert derived == primary ^ mask


def test_transform_rejects_wrong_number_of_line_states():
    with pytest.raises(ValueError, match="line states"):
        automaton.transform_by_line_semantics((7, 7, 7))
    with pytest.raises(ValueError, match="line states"):
        automaton.transform_by_line_semantics((7,) * 7)


def test_transform_rejects_unknown_line_state():
    # Validation is uniform with the length check above: both raise ValueError.
    with pytest.raises(ValueError, match="illegal line state"):
        automaton.transform_by_line_semantics((7, 7, 7, 7, 7, 5))


# --------------------------------------------------------------------------
# Exhaustive checks
# --------------------------------------------------------------------------

def test_xor_equivalence_holds_over_all_4096_line_state_assignments():
    result = automaton.check_xor_equivalence()
    assert result["holds"] is True
    assert result["cases"] == 4 ** N_LINES == 4096
    assert result["mismatches"] == 0


def test_xor_equivalence_re_derived_independently():
    """Re-run the 4^6 exhaustion here rather than trusting the module's loop."""
    for states in product(automaton.LINE_STATES, repeat=N_LINES):
        primary, derived, mask = automaton.transform_by_line_semantics(states)
        assert derived == primary ^ mask
        assert 0 <= primary < N_HEXAGRAMS
        assert 0 <= derived < N_HEXAGRAMS
        assert 0 <= mask < N_HEXAGRAMS


def test_commutativity_holds():
    result = automaton.check_commutativity()
    assert result["holds"] is True
    assert result["violations"] == 0
    assert result["cases"] == N_HEXAGRAMS ** 3


def test_self_inverse_holds():
    result = automaton.check_self_inverse()
    assert result["holds"] is True
    assert result["violations"] == 0
    assert result["cases"] == N_HEXAGRAMS ** 2


def test_strong_connectivity_holds_with_a_unique_witness():
    result = automaton.check_strong_connectivity()
    assert result["holds"] is True
    assert result["violations"] == 0
    assert result["non_unique"] == 0
    assert result["input_diameter"] == 1
    assert result["cases"] == N_HEXAGRAMS ** 2


# --------------------------------------------------------------------------
# The DFA itself
# --------------------------------------------------------------------------

def test_delta_is_xor_and_agrees_with_the_dfa_class():
    for q in range(N_HEXAGRAMS):
        for m in range(N_HEXAGRAMS):
            assert automaton.delta(q, m) == q ^ m
            assert automaton.FuxiDFA.step(q, m) == q ^ m


def test_dfa_run_composes_masks_by_xor():
    masks = [1, 2, 4, 63, 21]
    combined = 0
    for m in masks:
        combined ^= m
    for q in range(N_HEXAGRAMS):
        assert automaton.FuxiDFA.run(q, masks) == q ^ combined
    assert automaton.FuxiDFA.run(0, []) == 0


def test_dfa_state_and_alphabet_are_the_64_hexagrams():
    assert automaton.FuxiDFA.states == tuple(range(64))
    assert automaton.FuxiDFA.alphabet == tuple(range(64))


# --------------------------------------------------------------------------
# Group structure
# --------------------------------------------------------------------------

def test_transition_group_is_elementary_abelian_of_order_64_and_exponent_2():
    result = automaton.check_group_axioms()
    assert result["holds"] is True
    assert result["closure"] is True
    assert result["identity"] is True
    assert result["inverses"] is True
    assert result["associative"] is True
    assert result["abelian"] is True
    assert result["order"] == 64
    assert result["exponent"] == 2
    assert result["isomorphism_type"] == "(Z/2Z)^6"


def test_every_non_identity_element_has_order_exactly_two():
    """Exponent 2 re-derived: a XOR a = 0 for all a, and a != 0 for a != 0."""
    for a in range(N_HEXAGRAMS):
        assert (a ^ a) == 0
        if a != 0:
            assert a != 0  # order is not 1
    # No element of order 4 can exist, since squaring is already the identity.
    assert len({a ^ a for a in range(N_HEXAGRAMS)}) == 1


def test_full_symmetry_group_has_order_46080_and_acts_faithfully():
    result = automaton.full_symmetry_group_order()
    assert result["flip_subgroup"] == 64          # (Z/2Z)^6
    assert result["permutation_subgroup"] == 720  # S_6
    assert result["predicted_order"] == 46080     # 2^6 * 6!
    assert result["distinct_actions"] == 46080
    assert result["faithful"] is True
    assert "hyperoctahedral" in result["name"]


def test_symmetry_group_order_equals_two_to_six_times_six_factorial():
    from math import factorial

    assert 2 ** 6 * factorial(6) == 46080
