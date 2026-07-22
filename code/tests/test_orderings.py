"""Tests for the ordering analysis.

The checks in this file are deliberately split in two.

The first group is data-independent: it tests reversal, palindromicity, the
canonical matching, and the reference orderings. None of it depends on the
King Wen sequence data.

The second group validates the King Wen data itself against anchors derived by
hand from the eight trigrams, independently of whatever source the data came
from. A trigram is read bottom to top, and a hexagram value is
``lower + 8 * upper``:

    Qian 111 = 7   Dui  110 = 3   Li   101 = 5   Zhen 100 = 1
    Xun  011 = 6   Kan  010 = 2   Gen  001 = 4   Kun  000 = 0

These anchors exist so that an error in the sourced data fails loudly rather
than propagating into a published claim.
"""

from __future__ import annotations

import pytest

from fuxi import king_wen, orderings
from fuxi.encoding import complement

# --------------------------------------------------------------------------
# Hand-derived anchors: (King Wen number, hexagram value, name)
# --------------------------------------------------------------------------

TRIGRAM = {
    "qian": 0b111, "dui": 0b011, "li": 0b101, "zhen": 0b001,
    "xun": 0b110, "kan": 0b010, "gen": 0b100, "kun": 0b000,
}


def hexagram(lower: str, upper: str) -> int:
    """Compose a hexagram value from its lower and upper trigram names."""
    return TRIGRAM[lower] + 8 * TRIGRAM[upper]


#: King Wen number -> value, derived by hand from the trigram composition.
ANCHORS = {
    1: hexagram("qian", "qian"),   # 63, all yang
    2: hexagram("kun", "kun"),     # 0, all yin
    3: hexagram("zhen", "kan"),    # 17, water over thunder
    4: hexagram("kan", "gen"),     # 34, mountain over water
    27: hexagram("zhen", "gen"),   # 33, mountain over thunder
    28: hexagram("xun", "dui"),    # 30, lake over wind
    29: hexagram("kan", "kan"),    # 18
    30: hexagram("li", "li"),      # 45
    61: hexagram("dui", "xun"),    # 51, wind over lake
    62: hexagram("gen", "zhen"),   # 12, thunder over mountain
    63: hexagram("li", "kan"),     # 21, water over fire
    64: hexagram("kan", "li"),     # 42, fire over water
}


def test_trigram_table_is_a_bijection():
    assert sorted(TRIGRAM.values()) == list(range(8))


def test_anchor_values_are_distinct_and_in_range():
    assert len(set(ANCHORS.values())) == len(ANCHORS)
    assert all(0 <= v < 64 for v in ANCHORS.values())


def test_anchors_match_expected_integers():
    # Spelled out so a change in the trigram table cannot silently pass.
    assert ANCHORS[1] == 63
    assert ANCHORS[2] == 0
    assert ANCHORS[3] == 17
    assert ANCHORS[4] == 34
    assert ANCHORS[29] == 18
    assert ANCHORS[30] == 45
    assert ANCHORS[63] == 21
    assert ANCHORS[64] == 42


# --------------------------------------------------------------------------
# Data-independent structure
# --------------------------------------------------------------------------

def test_reverse_is_an_involution():
    assert all(orderings.reverse(orderings.reverse(v)) == v for v in range(64))


def test_reverse_known_values():
    assert orderings.reverse(1) == 32
    assert orderings.reverse(17) == 34      # anchors 3 and 4 are a reversal pair
    assert orderings.reverse(21) == 42      # anchors 63 and 64 are a reversal pair


def test_exactly_eight_palindromic_hexagrams():
    pal = orderings.palindromic_hexagrams()
    assert len(pal) == 8
    assert pal == [0, 12, 18, 30, 33, 45, 51, 63]


def test_palindromes_are_closed_under_complement():
    pal = set(orderings.palindromic_hexagrams())
    assert {complement(v) for v in pal} == pal


def test_canonical_matching_is_perfect():
    m = orderings.canonical_matching()
    assert m["is_involution"]
    assert m["fixed_points"] == []
    assert m["n_pairs"] == 32
    assert m["is_perfect_matching"]
    assert m["reversal_pairs"] == 28
    assert m["complement_pairs"] == 4


def test_anchor_couplets_agree_with_canonical_matching():
    partner = orderings.canonical_matching()["partner"]
    for a, b in ((1, 2), (3, 4), (27, 28), (29, 30), (61, 62), (63, 64)):
        assert partner[ANCHORS[a]] == ANCHORS[b], f"couplet {a}-{b}"


def test_the_four_complement_couplets_are_the_palindromic_ones():
    for a, b in ((1, 2), (27, 28), (29, 30), (61, 62)):
        assert orderings.is_palindromic(ANCHORS[a])
        assert complement(ANCHORS[a]) == ANCHORS[b]


# --------------------------------------------------------------------------
# Reference orderings
# --------------------------------------------------------------------------

def test_gray_ordering_is_optimal():
    g = orderings.gray_ordering()
    assert sorted(g) == list(range(64))
    profile = orderings.distance_profile(g)
    assert profile["max"] == 1
    assert profile["mean"] == 1.0
    assert profile["total_line_changes"] == 63


def test_counting_ordering_matches_closed_form():
    f = orderings.counting_ordering()
    profile = orderings.distance_profile(f)
    assert profile["total_line_changes"] == orderings.fuxi_total_changes_closed_form()
    assert profile["total_line_changes"] == 120
    assert profile["mean"] == pytest.approx(120 / 63, abs=1e-12)


def test_counting_ordering_is_not_an_optimal_code():
    # Binary counting is not a Gray code; this guards against the claim that the
    # Earlier Heaven arrangement minimizes consecutive change.
    counting = orderings.distance_profile(orderings.counting_ordering())["mean"]
    gray = orderings.distance_profile(orderings.gray_ordering())["mean"]
    assert counting > gray


def test_expected_random_consecutive_distance():
    assert orderings.expected_random_consecutive_distance() == pytest.approx(
        192 / 63, abs=1e-12
    )


def test_pairing_structure_rejects_non_permutations():
    with pytest.raises(ValueError):
        orderings.pairing_structure(list(range(63)))
    with pytest.raises(ValueError):
        orderings.pairing_structure([0] * 64)


def test_gray_and_counting_do_not_satisfy_the_couplet_claim():
    # The couplet structure is specific; it is not a property of any ordering.
    for order in (orderings.counting_ordering(), orderings.gray_ordering()):
        assert not orderings.pairing_structure(order)["claim_holds"]


# --------------------------------------------------------------------------
# The null
# --------------------------------------------------------------------------

def test_null_probability_is_astronomically_small():
    n = orderings.pairing_null_probability()
    assert n["probability"] < 1e-40
    assert n["log10_probability"] < -40


def test_expected_explained_couplets_under_random():
    e = orderings.expected_explained_couplets_random()
    assert e["hexagrams_with_two_partners"] + e["hexagrams_with_one_partner"] == 64
    assert e["expected_couplets"] < 1.0


def test_simulation_agrees_with_expectation():
    e = orderings.expected_explained_couplets_random()["expected_couplets"]
    sim = orderings.pairing_simulation(3000, seed=20260722)["mean_couplets_explained"]
    # Poisson-ish count with mean below 1; 3000 trials gives a tight interval.
    assert sim == pytest.approx(e, abs=0.1)
    assert orderings.pairing_simulation(3000)["max_couplets_explained"] < 32


# --------------------------------------------------------------------------
# The King Wen data
# --------------------------------------------------------------------------

def test_king_wen_table_is_a_permutation():
    assert sorted(king_wen.king_wen_ordering()) == list(range(64))


def test_king_wen_matches_every_hand_derived_anchor():
    order = king_wen.king_wen_ordering()
    for number, value in ANCHORS.items():
        assert order[number - 1] == value, f"King Wen #{number}"


def test_king_wen_endpoints():
    order = king_wen.king_wen_ordering()
    assert order[0] == 63       # Qian, all yang
    assert order[1] == 0        # Kun, all yin
    assert order[62] == 21      # Ji Ji, alternating
    assert order[63] == 42      # Wei Ji, the other alternating


def test_sovereign_hexagrams_have_the_expected_arithmetic_signature():
    """The twelve sovereign hexagrams encode yang waxing from the bottom.

    With the bottom line as the least significant bit, "yang fills upward from
    the bottom" is exactly 2^k - 1, and "yin fills upward from the bottom" is
    its complement. This is a strong orientation check: it fails if the line
    order is reversed or if trigram-internal bits are swapped.
    """
    order = king_wen.king_wen_ordering()
    values = [order[n - 1] for n in king_wen.SOVEREIGN_HEXAGRAMS]
    waxing_yang = [2 ** k - 1 for k in range(1, 7)]
    waxing_yin = [63 - (2 ** k - 1) for k in range(1, 7)]
    assert values[:6] == waxing_yang == [1, 3, 7, 15, 31, 63]
    assert values[6:] == waxing_yin == [62, 60, 56, 48, 32, 0]


def test_doubled_trigram_hexagrams_have_equal_halves():
    order = king_wen.king_wen_ordering()
    for n in king_wen.DOUBLED_TRIGRAM_HEXAGRAMS:
        v = order[n - 1]
        assert v % 8 == v // 8, f"King Wen #{n} is not a doubled trigram"


def test_king_wen_satisfies_the_couplet_claim():
    """The headline structural result."""
    result = orderings.pairing_structure(king_wen.king_wen_ordering())
    assert result["claim_holds"]
    assert result["reversal_pairs"] == 28
    assert result["complement_pairs"] == 4
    assert result["unexplained_pairs"] == 0


def test_the_four_complement_couplets_are_at_the_expected_positions():
    result = orderings.pairing_structure(king_wen.king_wen_ordering())
    couplet_numbers = sorted(i for i, _, _ in result["complement_detail"])
    # Couplet k covers King Wen numbers 2k-1 and 2k.
    assert couplet_numbers == [1, 14, 15, 31]
    assert [(2 * k - 1, 2 * k) for k in couplet_numbers] == [
        (1, 2), (27, 28), (29, 30), (61, 62)
    ]


def test_king_wen_number_lookup_round_trips():
    for n in range(1, 65):
        value = king_wen.king_wen_ordering()[n - 1]
        assert king_wen.number_of(value) == n


def test_unicode_block_is_contiguous_and_in_king_wen_order():
    glyphs = [king_wen.unicode_glyph(n) for n in range(1, 65)]
    assert len(set(glyphs)) == 64
    assert ord(glyphs[0]) == 0x4DC0
    assert ord(glyphs[-1]) == 0x4DFF


def test_king_wen_names_are_present_and_distinct():
    zh = [king_wen.name(n)[0] for n in range(1, 65)]
    assert len(set(zh)) == 64
    assert king_wen.name(1)[0] == "乾"
    assert king_wen.name(2)[0] == "坤"


# --------------------------------------------------------------------------
# The two readings of the Earlier Heaven arrangement
# --------------------------------------------------------------------------

def test_traditional_fuxi_ordering_starts_at_qian():
    t = orderings.fuxi_traditional_ordering()
    assert sorted(t) == list(range(64))
    assert t[0] == 63                 # Qian
    assert t[1] == 31                 # Guai: Qian below, Dui above
    assert t[-1] == 0                 # Kun


def test_classical_trigram_order_descends_only_under_bottom_as_msb():
    """Pins the claim in docs/conventions.md.

    The classical order is Qian, Dui, Li, Zhen, Xun, Kan, Gen, Kun. Read with
    the bottom line as the most significant bit it descends 7 to 0. Read with
    the bottom line as the least significant bit it has no such pattern.
    """
    order = ["qian", "dui", "li", "zhen", "xun", "kan", "gen", "kun"]
    as_lsb = [TRIGRAM[n] for n in order]
    # TRIGRAM already encodes bottom-as-LSB; reverse the three bits for MSB.
    as_msb = [
        sum(((v >> i) & 1) << (2 - i) for i in range(3)) for v in as_lsb
    ]
    assert as_msb == [7, 6, 5, 4, 3, 2, 1, 0]
    assert as_lsb == [7, 3, 5, 1, 6, 2, 4, 0]
    assert as_msb == sorted(as_msb, reverse=True)
    assert as_lsb != sorted(as_lsb, reverse=True)


def test_traditional_fuxi_trigram_order_is_the_classical_one():
    """Qian Dui Li Zhen Xun Kan Gen Kun, read with the bottom line as MSB."""
    expected = [
        hexagram("qian", "qian"), hexagram("qian", "dui"),
        hexagram("qian", "li"), hexagram("qian", "zhen"),
    ]
    assert orderings.fuxi_traditional_ordering()[:4] == expected


def test_the_two_readings_differ_as_sequences_but_not_as_sets():
    r = orderings.bit_reversal_relation()
    assert r["same_underlying_set"]
    assert not r["same_sequence"]
    assert r["positions_that_differ"] == 56


def test_bit_reversal_is_a_hypercube_isometry():
    r = orderings.bit_reversal_relation()
    assert r["reverse_is_hypercube_isometry"]
    assert r["profiles_agree_up_to_direction"]


def test_both_readings_have_the_same_coding_profile():
    a = orderings.distance_profile(orderings.counting_ordering())
    b = orderings.distance_profile(orderings.fuxi_traditional_ordering())
    assert a["total_line_changes"] == b["total_line_changes"] == 120
    assert a["mean"] == pytest.approx(b["mean"], abs=1e-12)
    assert a["counts"] == b["counts"][::-1] or a["counts"] == b["counts"]
