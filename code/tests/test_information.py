"""Tests for :mod:`fuxi.information`.

Entropies are transcendental in general, so the assertions here are float
comparisons. Each one states its tolerance explicitly; the headline values are
pinned to four decimal places (abs=5e-5), which is tighter than the three-decimal
figures quoted in the prior analysis.

The two results that matter:

* the mutual information computed from the true yarrow joint (1.2326 bits) is
  strictly greater than the independent-mask value (1.1323 bits);
* the transformed hexagram carries 5.7266 bits, strictly less than six, because
  it is yin-biased.
"""

from __future__ import annotations

from fractions import Fraction
from math import log2

import pytest

from fuxi import information, yarrow

# Four-decimal pinning tolerance.
FOUR_DP = 5e-5


@pytest.fixture(scope="module")
def line_joint():
    ideal = yarrow.line_state_distribution("idealized")
    return yarrow.derived_quantities(ideal)


# --------------------------------------------------------------------------
# Entropy primitives
# --------------------------------------------------------------------------

def test_entropy_of_a_point_mass_is_zero():
    assert information.entropy([1]) == 0.0
    assert information.entropy([Fraction(1), Fraction(0)]) == 0.0


def test_entropy_ignores_zero_probability_outcomes():
    assert information.entropy([0.5, 0.5, 0.0]) == pytest.approx(1.0, abs=1e-12)


def test_entropy_of_a_fair_coin_is_one_bit():
    assert information.entropy([Fraction(1, 2)] * 2) == pytest.approx(1.0, abs=1e-12)


def test_binary_entropy_is_symmetric_and_peaks_at_one_half():
    assert information.binary_entropy(Fraction(1, 2)) == pytest.approx(1.0, abs=1e-12)
    for p in (Fraction(1, 8), Fraction(1, 4), Fraction(3, 8)):
        assert information.binary_entropy(p) == pytest.approx(
            information.binary_entropy(1 - p), abs=1e-12
        )
        assert information.binary_entropy(p) < 1.0


def test_uniform_entropy_is_log2_of_n():
    for n in (2, 4, 8, 64):
        assert information.uniform_entropy(n) == pytest.approx(log2(n), abs=1e-12)


def test_entropy_rejects_negative_probability():
    with pytest.raises(ValueError, match="negative probability"):
        information.entropy([0.5, 0.7, -0.2])


# --------------------------------------------------------------------------
# System-level quantities
# --------------------------------------------------------------------------

def test_hexagram_entropy_is_exactly_six_bits():
    """log2(64) = 6 is exactly representable in binary floating point."""
    assert information.hexagram_entropy() == 6.0


def test_mask_entropy_at_one_quarter_is_4_8677_bits():
    """6 * H_b(1/4) = 6 * (1/2 + (3/4) log2(4/3)). Tolerance: 5e-5 (4 dp)."""
    value = information.mask_entropy(Fraction(1, 4))
    assert value == pytest.approx(4.8677, abs=FOUR_DP)
    # Re-derived independently from the closed form.
    expected = 6 * (0.25 * log2(4.0) + 0.75 * log2(4.0 / 3.0))
    assert value == pytest.approx(expected, abs=1e-12)


def test_independent_mask_mutual_information_is_1_1323_bits():
    """I = 6 - H(M). Tolerance: 5e-5 (4 dp)."""
    value = information.mutual_information_independent_mask(Fraction(1, 4))
    assert value == pytest.approx(1.1323, abs=FOUR_DP)
    assert value == pytest.approx(
        6.0 - information.mask_entropy(Fraction(1, 4)), abs=1e-12
    )


def test_yarrow_true_mutual_information_is_1_2326_bits(line_joint):
    """Computed from the 2x2 per-line joint, times six. Tolerance: 5e-5 (4 dp)."""
    value = information.mutual_information_from_line_joint(line_joint["joint"])
    assert value == pytest.approx(1.2326, abs=FOUR_DP)


def test_yarrow_mutual_information_strictly_exceeds_the_independent_mask_value(
    line_joint,
):
    """The state dependence makes the transformation MORE informative, not less."""
    true_mi = information.mutual_information_from_line_joint(line_joint["joint"])
    naive_mi = information.mutual_information_independent_mask(Fraction(1, 4))
    assert true_mi > naive_mi
    # The gap is about 0.10 bits, far outside any plausible rounding error.
    assert true_mi - naive_mi == pytest.approx(0.1003, abs=FOUR_DP)


def test_transformed_hexagram_entropy_is_5_7266_bits(line_joint):
    """6 * H_b(3/8), strictly below six because the derived line is yin-biased.

    Tolerance: 5e-5 (4 dp).
    """
    p_derived_yang = line_joint["p_derived_yang"]
    assert p_derived_yang == Fraction(3, 8)  # exact
    value = 6 * information.binary_entropy(p_derived_yang)
    assert value == pytest.approx(5.7266, abs=FOUR_DP)
    assert value < 6.0
    assert 6.0 - value == pytest.approx(0.2734, abs=FOUR_DP)


# --------------------------------------------------------------------------
# Mutual information mechanics
# --------------------------------------------------------------------------

def test_mutual_information_of_independent_variables_is_zero():
    joint = {
        ("a", "x"): Fraction(1, 4),
        ("a", "y"): Fraction(1, 4),
        ("b", "x"): Fraction(1, 4),
        ("b", "y"): Fraction(1, 4),
    }
    assert information.mutual_information(joint) == pytest.approx(0.0, abs=1e-12)


def test_mutual_information_of_a_deterministic_copy_is_the_full_entropy():
    joint = {("a", "a"): Fraction(1, 2), ("b", "b"): Fraction(1, 2)}
    assert information.mutual_information(joint) == pytest.approx(1.0, abs=1e-12)


def test_joint_entropy_accepts_a_mapping_or_an_iterable(line_joint):
    joint = line_joint["joint"]
    assert information.joint_entropy(joint) == pytest.approx(
        information.joint_entropy(list(joint.values())), abs=1e-12
    )


def test_per_line_mutual_information_is_one_sixth_of_the_hexagram_value(line_joint):
    """The six lines are cast independently, so I scales linearly."""
    per_line = information.mutual_information(line_joint["joint"])
    whole = information.mutual_information_from_line_joint(line_joint["joint"])
    assert whole == pytest.approx(6 * per_line, abs=1e-12)
    assert per_line == pytest.approx(0.2054, abs=FOUR_DP)


def test_mutual_information_never_exceeds_either_marginal_entropy(line_joint):
    joint = line_joint["joint"]
    mi = information.mutual_information(joint)
    px = {}
    py = {}
    for (x, y), p in joint.items():
        px[x] = px.get(x, 0) + p
        py[y] = py.get(y, 0) + p
    assert mi <= information.entropy(px.values()) + 1e-12
    assert mi <= information.entropy(py.values()) + 1e-12
    assert mi >= -1e-12
