"""Tests for :mod:`fuxi.encoding`.

Convention under test: lines are stored bottom-first, the bottom line carries
weight 2^0 and the top line 2^5. Yang = 1, yin = 0, so Kun (all yin) = 0 and
Qian (all yang) = 63.

Every quantity in this module is an exact integer or a set, so every assertion
here is exact -- no floating point appears anywhere in this file.
"""

from __future__ import annotations

from itertools import product
from math import comb

import pytest

from fuxi import encoding


# --------------------------------------------------------------------------
# Shao Yong's doubling method
# --------------------------------------------------------------------------

@pytest.mark.parametrize("n", range(7))
def test_doubling_top_cardinality_is_two_to_the_n(n):
    """|G(n)| = 2^n for n = 0..6 under top placement."""
    assert len(encoding.doubling_top(n)) == 2 ** n


@pytest.mark.parametrize("n", range(7))
def test_doubling_bottom_cardinality_is_two_to_the_n(n):
    """|G(n)| = 2^n for n = 0..6 under bottom placement."""
    assert len(encoding.doubling_bottom(n)) == 2 ** n


@pytest.mark.parametrize("n", range(7))
def test_doubling_top_reproduces_all_n_bit_strings(n):
    """The generated set equals the brute-force product {0,1}^n."""
    grams = encoding.doubling_top(n)
    assert set(grams) == encoding.brute_force_enumeration(n)
    assert len(set(grams)) == len(grams), "generation must not repeat a symbol"


@pytest.mark.parametrize("n", range(7))
def test_doubling_bottom_reproduces_all_n_bit_strings(n):
    """Same set under the other placement convention: the set is convention-free."""
    grams = encoding.doubling_bottom(n)
    assert set(grams) == encoding.brute_force_enumeration(n)
    assert len(set(grams)) == len(grams), "generation must not repeat a symbol"


@pytest.mark.parametrize("n", range(7))
def test_both_placements_generate_the_same_set(n):
    assert set(encoding.doubling_top(n)) == set(encoding.doubling_bottom(n))


def test_doubling_at_level_six_gives_the_64_hexagrams():
    assert set(encoding.doubling_top(6)) == set(encoding.all_hexagrams())
    assert set(encoding.doubling_bottom(6)) == set(encoding.all_hexagrams())
    assert len(encoding.all_hexagrams()) == encoding.N_HEXAGRAMS == 64


@pytest.mark.parametrize("placement", ["top", "bottom"])
@pytest.mark.parametrize("n", range(7))
def test_doubling_values_are_exactly_0_to_2n_minus_1_in_order(n, placement):
    """Enumeration order is the natural integer order under both conventions."""
    values = encoding.doubling_values(n, placement)
    assert values == list(range(2 ** n))


def test_doubling_values_rejects_unknown_placement():
    with pytest.raises(ValueError):
        encoding.doubling_values(6, "sideways")


# --------------------------------------------------------------------------
# The core bijection
# --------------------------------------------------------------------------

def test_lines_to_value_round_trips_over_all_64():
    for v in range(encoding.N_HEXAGRAMS):
        lines = encoding.value_to_lines(v)
        assert len(lines) == encoding.N_LINES
        assert encoding.lines_to_value(lines) == v


def test_value_to_lines_round_trips_over_all_64_line_tuples():
    for lines in product((encoding.YIN, encoding.YANG), repeat=encoding.N_LINES):
        assert encoding.value_to_lines(encoding.lines_to_value(lines)) == lines


def test_encoding_is_a_bijection_onto_0_63():
    values = sorted(
        encoding.lines_to_value(lines) for lines in encoding.all_hexagrams()
    )
    assert values == list(range(64))


def test_bottom_line_is_the_least_significant_bit():
    """lines[0] is the bottom line and carries weight 2^0."""
    assert encoding.lines_to_value((1, 0, 0, 0, 0, 0)) == 1
    assert encoding.lines_to_value((0, 0, 0, 0, 0, 1)) == 32
    assert encoding.value_to_lines(1) == (1, 0, 0, 0, 0, 0)
    assert encoding.value_to_lines(32) == (0, 0, 0, 0, 0, 1)


def test_kun_is_zero_and_qian_is_sixty_three():
    assert encoding.KUN == 0
    assert encoding.QIAN == 63
    assert encoding.value_to_lines(encoding.KUN) == (0,) * 6
    assert encoding.value_to_lines(encoding.QIAN) == (1,) * 6
    assert encoding.lines_to_value((encoding.YIN,) * 6) == encoding.KUN
    assert encoding.lines_to_value((encoding.YANG,) * 6) == encoding.QIAN


# --------------------------------------------------------------------------
# Boolean lattice structure
# --------------------------------------------------------------------------

def test_yang_count_is_the_hamming_weight():
    for v in range(encoding.N_HEXAGRAMS):
        assert encoding.yang_count(v) == sum(encoding.value_to_lines(v))


def test_rank_distribution_is_the_sixth_binomial_row():
    assert encoding.rank_distribution() == [1, 6, 15, 20, 15, 6, 1]
    assert encoding.rank_distribution() == [comb(6, k) for k in range(7)]
    assert sum(encoding.rank_distribution()) == 64


def test_complement_is_an_involution():
    for v in range(encoding.N_HEXAGRAMS):
        assert encoding.complement(encoding.complement(v)) == v


def test_complement_flips_every_line_and_reverses_rank():
    for v in range(encoding.N_HEXAGRAMS):
        c = encoding.complement(v)
        assert encoding.yang_count(c) == 6 - encoding.yang_count(v)
        assert all(
            a != b
            for a, b in zip(encoding.value_to_lines(v), encoding.value_to_lines(c))
        )
    assert encoding.complement(encoding.KUN) == encoding.QIAN
    assert encoding.complement(encoding.QIAN) == encoding.KUN


def test_meet_join_leq_are_mutually_consistent():
    """a <= b iff meet(a,b) == a iff join(a,b) == b, for every ordered pair."""
    for a in range(encoding.N_HEXAGRAMS):
        for b in range(encoding.N_HEXAGRAMS):
            le = encoding.leq(a, b)
            assert le == (encoding.meet(a, b) == a)
            assert le == (encoding.join(a, b) == b)


def test_meet_and_join_are_commutative_idempotent_and_bounded():
    for a in range(encoding.N_HEXAGRAMS):
        assert encoding.meet(a, a) == a
        assert encoding.join(a, a) == a
        # Kun is the bottom element, Qian the top.
        assert encoding.meet(a, encoding.QIAN) == a
        assert encoding.join(a, encoding.KUN) == a
        assert encoding.meet(a, encoding.KUN) == encoding.KUN
        assert encoding.join(a, encoding.QIAN) == encoding.QIAN
        assert encoding.leq(encoding.KUN, a)
        assert encoding.leq(a, encoding.QIAN)
        for b in range(encoding.N_HEXAGRAMS):
            assert encoding.meet(a, b) == encoding.meet(b, a)
            assert encoding.join(a, b) == encoding.join(b, a)
            assert encoding.leq(encoding.meet(a, b), a)
            assert encoding.leq(a, encoding.join(a, b))
            # Absorption laws.
            assert encoding.meet(a, encoding.join(a, b)) == a
            assert encoding.join(a, encoding.meet(a, b)) == a


def test_partial_order_is_antisymmetric_and_transitive():
    for a in range(encoding.N_HEXAGRAMS):
        assert encoding.leq(a, a)
        for b in range(encoding.N_HEXAGRAMS):
            if encoding.leq(a, b) and encoding.leq(b, a):
                assert a == b
            if encoding.leq(a, b):
                for c in range(encoding.N_HEXAGRAMS):
                    if encoding.leq(b, c):
                        assert encoding.leq(a, c)


def test_complement_satisfies_de_morgan_and_the_lattice_complement_laws():
    for a in range(encoding.N_HEXAGRAMS):
        assert encoding.meet(a, encoding.complement(a)) == encoding.KUN
        assert encoding.join(a, encoding.complement(a)) == encoding.QIAN
        for b in range(encoding.N_HEXAGRAMS):
            assert encoding.complement(encoding.meet(a, b)) == encoding.join(
                encoding.complement(a), encoding.complement(b)
            )
            assert encoding.complement(encoding.join(a, b)) == encoding.meet(
                encoding.complement(a), encoding.complement(b)
            )
            # Order reverses under complementation.
            assert encoding.leq(a, b) == encoding.leq(
                encoding.complement(b), encoding.complement(a)
            )


# --------------------------------------------------------------------------
# Input validation
# --------------------------------------------------------------------------

@pytest.mark.parametrize("bad", [(), (1,), (0, 1, 0, 1, 0), (0,) * 7, (1,) * 12])
def test_lines_to_value_rejects_wrong_length(bad):
    with pytest.raises(ValueError, match="lines"):
        encoding.lines_to_value(bad)


@pytest.mark.parametrize("bad_bit", [2, -1, 9, 0.5])
def test_lines_to_value_rejects_non_binary_lines(bad_bit):
    with pytest.raises(ValueError, match="yin"):
        encoding.lines_to_value((0, 1, 0, 1, 0, bad_bit))


@pytest.mark.parametrize("bad", [-1, 64, 65, 1000])
def test_value_to_lines_rejects_out_of_range(bad):
    with pytest.raises(ValueError, match="out of range"):
        encoding.value_to_lines(bad)
