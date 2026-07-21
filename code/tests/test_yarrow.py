"""Tests for :mod:`fuxi.yarrow`.

The idealized (textbook) model of the da yan shi fa gives exact rationals, so
every assertion about it is an exact :class:`~fractions.Fraction` comparison.
Only the Monte-Carlo test uses a tolerance, and that tolerance is stated.

The load-bearing result here is that the mutation mask is NOT independent of
the current line: a yang line changes with probability 3/8 while a yin line
changes with probability 1/8, even though the marginal change rate is 1/4.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from fuxi import yarrow
from fuxi.automaton import OLD_YANG, OLD_YIN, YOUNG_YANG, YOUNG_YIN


@pytest.fixture(scope="module")
def ideal():
    return yarrow.line_state_distribution("idealized")


@pytest.fixture(scope="module")
def ideal_q(ideal):
    return yarrow.derived_quantities(ideal)


# --------------------------------------------------------------------------
# The idealized line-state distribution
# --------------------------------------------------------------------------

def test_idealized_distribution_is_exactly_1_5_7_3_sixteenths(ideal):
    assert ideal == {
        OLD_YIN: Fraction(1, 16),      # 6
        YOUNG_YANG: Fraction(5, 16),   # 7
        YOUNG_YIN: Fraction(7, 16),    # 8
        OLD_YANG: Fraction(3, 16),     # 9
    }
    # Exact rationals, not floats.
    assert all(isinstance(p, Fraction) for p in ideal.values())


def test_idealized_distribution_matches_the_modules_stated_constant(ideal):
    assert ideal == yarrow.IDEALIZED_LINE_PROBABILITIES


def test_idealized_probabilities_sum_to_exactly_one(ideal):
    assert sum(ideal.values()) == Fraction(1)
    assert sum(ideal.values()) == 1


def test_only_the_four_legal_line_states_occur(ideal):
    assert set(ideal) == {6, 7, 8, 9}


# --------------------------------------------------------------------------
# Derived quantities under the idealized model
# --------------------------------------------------------------------------

def test_marginal_change_probability_is_exactly_one_quarter(ideal_q):
    assert ideal_q["p_change"] == Fraction(1, 4)


def test_expected_number_of_changing_lines_is_exactly_three_halves(ideal_q):
    assert ideal_q["expected_changing_lines"] == Fraction(3, 2)
    assert ideal_q["expected_changing_lines"] == 6 * ideal_q["p_change"]


def test_cast_line_is_yang_with_probability_exactly_one_half(ideal_q):
    """This is what makes the cast hexagram uniform over the 64 states."""
    assert ideal_q["p_primary_yang"] == Fraction(1, 2)
    assert ideal_q["p_primary_yin"] == Fraction(1, 2)


def test_change_probability_is_state_dependent(ideal_q):
    """The central correction: P(change|yang) = 3/8 but P(change|yin) = 1/8."""
    assert ideal_q["p_change_given_yang"] == Fraction(3, 8)
    assert ideal_q["p_change_given_yin"] == Fraction(1, 8)
    assert ideal_q["mask_independent_of_state"] is False
    # A yang line changes exactly three times as often as a yin line.
    assert ideal_q["p_change_given_yang"] == 3 * ideal_q["p_change_given_yin"]


def test_marginal_rate_is_the_average_of_the_two_conditionals(ideal_q):
    """1/4 = 1/2 * 3/8 + 1/2 * 1/8 -- which is why the dependence is easy to miss."""
    mixed = (
        ideal_q["p_primary_yang"] * ideal_q["p_change_given_yang"]
        + ideal_q["p_primary_yin"] * ideal_q["p_change_given_yin"]
    )
    assert mixed == Fraction(1, 4) == ideal_q["p_change"]


def test_derived_hexagram_is_yin_biased_not_uniform(ideal_q):
    assert ideal_q["p_derived_yang"] == Fraction(3, 8)
    assert ideal_q["p_derived_yang"] != Fraction(1, 2)


def test_joint_law_is_exactly_the_four_line_state_probabilities(ideal, ideal_q):
    joint = ideal_q["joint"]
    assert joint[("yin", "yin")] == ideal[YOUNG_YIN]    # 8: stays yin
    assert joint[("yin", "yang")] == ideal[OLD_YIN]     # 6: yin -> yang
    assert joint[("yang", "yin")] == ideal[OLD_YANG]    # 9: yang -> yin
    assert joint[("yang", "yang")] == ideal[YOUNG_YANG] # 7: stays yang
    assert sum(joint.values()) == Fraction(1)


# --------------------------------------------------------------------------
# The exact (uniform-split) model
# --------------------------------------------------------------------------

@pytest.mark.parametrize("min_heap", [1, 2])
def test_exact_model_is_a_valid_distribution(min_heap):
    dist = yarrow.line_state_distribution("exact", min_heap=min_heap)
    assert set(dist) == {6, 7, 8, 9}
    assert sum(dist.values()) == Fraction(1)
    assert all(isinstance(p, Fraction) and p > 0 for p in dist.values())


@pytest.mark.parametrize("min_heap", [1, 2])
def test_state_dependence_survives_the_exact_split_model(min_heap):
    """P(change|yang) stays far above P(change|yin) when the idealization is dropped.

    Under the uniform-split model the textbook rationals no longer hold, but the
    asymmetry the correction rests on is not an artefact of the idealization.
    """
    dist = yarrow.line_state_distribution("exact", min_heap=min_heap)
    q = yarrow.derived_quantities(dist)
    cy = q["p_change_given_yang"]
    ci = q["p_change_given_yin"]
    assert isinstance(cy, Fraction) and isinstance(ci, Fraction)
    assert cy > ci
    assert q["mask_independent_of_state"] is False
    # "Substantially greater": at least three times as large, and an absolute
    # gap of at least 0.25 in probability. Both are exact rational comparisons.
    assert cy > 3 * ci
    assert cy - ci > Fraction(1, 4)


def test_exact_model_departs_only_slightly_from_the_idealized_one(ideal):
    """The idealization is quantitatively close but not exact."""
    exact = yarrow.line_state_distribution("exact")
    assert exact != ideal
    drift = max(abs(exact[k] - ideal[k]) for k in ideal)
    assert drift < Fraction(1, 20), f"drift {float(drift)} unexpectedly large"


def test_line_state_distribution_rejects_unknown_model():
    with pytest.raises(ValueError, match="idealized"):
        yarrow.line_state_distribution("wishful")


# --------------------------------------------------------------------------
# Stage mechanics
# --------------------------------------------------------------------------

def test_remainder_mod_four_keeps_four_rather_than_zero():
    assert yarrow._remainder_mod_four(0) == 0
    assert yarrow._remainder_mod_four(4) == 4
    assert yarrow._remainder_mod_four(8) == 4
    assert yarrow._remainder_mod_four(9) == 1
    assert yarrow._remainder_mod_four(23) == 3


def test_set_aside_on_the_first_change_is_always_five_or_nine():
    """With 49 stalks the first change sets aside 5 or 9, never anything else."""
    for left in range(2, 48):
        assert yarrow.set_aside(49, left) in (5, 9)


def test_first_change_sets_aside_nine_exactly_when_left_is_divisible_by_four():
    for left in range(4, 48):
        expected = 9 if left % 4 == 0 else 5
        assert yarrow.set_aside(49, left) == expected


def test_idealized_stage_outcomes_are_the_textbook_values():
    assert yarrow.stage_outcomes_idealized(49, 0) == {
        5: Fraction(3, 4), 9: Fraction(1, 4)
    }
    for change_index in (1, 2):
        assert yarrow.stage_outcomes_idealized(44, change_index) == {
            4: Fraction(1, 2), 8: Fraction(1, 2)
        }


def test_exact_stage_outcomes_are_a_distribution_over_the_same_support():
    outcomes = yarrow.stage_outcomes_exact(49)
    assert set(outcomes) == {5, 9}
    assert sum(outcomes.values()) == Fraction(1)
    # Not exactly 3/4 : 1/4 -- 46 admissible split points is not divisible by 4.
    assert outcomes[9] != Fraction(1, 4)


# --------------------------------------------------------------------------
# Monte Carlo
# --------------------------------------------------------------------------

def test_monte_carlo_converges_to_the_idealized_values(ideal):
    """50 000 trials, seed 20260722, residue-uniform split.

    Tolerance: 0.01 absolute on each of the four probabilities. With 50 000
    draws the standard error of each estimate is below 0.0023, so 0.01 is
    roughly a four-sigma band -- tight enough to catch a real regression and
    loose enough not to be flaky. The seed is fixed, so the run is deterministic.
    """
    trials = 50_000
    mc = yarrow.monte_carlo_line_states(
        trials=trials, seed=20260722, mode="residue_uniform"
    )
    assert set(mc) == {6, 7, 8, 9}
    assert sum(mc.values()) == pytest.approx(1.0, abs=1e-12)
    for state, p in ideal.items():
        assert mc[state] == pytest.approx(float(p), abs=0.01), (
            f"state {state}: simulated {mc[state]} vs idealized {float(p)}"
        )


def test_monte_carlo_is_deterministic_for_a_fixed_seed():
    a = yarrow.monte_carlo_line_states(trials=2000, seed=7, mode="residue_uniform")
    b = yarrow.monte_carlo_line_states(trials=2000, seed=7, mode="residue_uniform")
    assert a == b


def test_uniform_split_monte_carlo_tracks_the_exact_model_not_the_idealized_one():
    """The physical split simulation converges to the exact model's values.

    Tolerance: 0.01 absolute, same reasoning as above (50 000 trials, fixed seed).
    """
    trials = 50_000
    mc = yarrow.monte_carlo_line_states(
        trials=trials, seed=20260722, mode="uniform_split"
    )
    exact = yarrow.line_state_distribution("exact")
    for state, p in exact.items():
        assert mc[state] == pytest.approx(float(p), abs=0.01)


def test_simulate_line_only_ever_returns_a_legal_line_state():
    import random

    rng = random.Random(1234)
    for _ in range(500):
        assert yarrow.simulate_line(rng) in (6, 7, 8, 9)
        assert yarrow.simulate_line_residue_uniform(rng) in (6, 7, 8, 9)
