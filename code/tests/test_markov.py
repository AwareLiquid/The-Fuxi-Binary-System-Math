"""Tests for :mod:`fuxi.markov`.

Two 64x64 kernels are compared:

``A`` independent-mask kernel, every line flips with probability 1/4
      regardless of its current value;
``B`` yarrow kernel, a yang line flips with probability 3/8 and a yin line
      with probability 1/8.

Both kernels are built from exact Fractions, so stochasticity, symmetry and
stationarity are all tested by exact rational equality. Only the eigenvalues
come from numpy and therefore carry a tolerance.
"""

from __future__ import annotations

from collections import Counter
from fractions import Fraction
from math import comb

import pytest

from fuxi import markov
from fuxi.encoding import KUN, N_HEXAGRAMS, QIAN

# Conditional flip probabilities implied by the idealized yarrow model.
P_CHANGE_GIVEN_YIN = Fraction(1, 8)
P_CHANGE_GIVEN_YANG = Fraction(3, 8)

UNIFORM = [Fraction(1, N_HEXAGRAMS)] * N_HEXAGRAMS

# numpy eigenvalue tolerance for a 64x64 matrix with entries of order 1e-2.
EIG_TOL = 1e-9


@pytest.fixture(scope="module")
def kernel_independent():
    return markov.independent_mask_kernel(Fraction(1, 4))


@pytest.fixture(scope="module")
def kernel_yarrow():
    return markov.yarrow_kernel(P_CHANGE_GIVEN_YIN, P_CHANGE_GIVEN_YANG)


@pytest.fixture(scope="module")
def product_stationary():
    return markov.stationary_product_form(P_CHANGE_GIVEN_YIN, P_CHANGE_GIVEN_YANG)


# --------------------------------------------------------------------------
# Shape and stochasticity
# --------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["kernel_independent", "kernel_yarrow"])
def test_kernel_is_64_by_64(name, request):
    kernel = request.getfixturevalue(name)
    assert len(kernel) == 64
    assert all(len(row) == 64 for row in kernel)


@pytest.mark.parametrize("name", ["kernel_independent", "kernel_yarrow"])
def test_kernel_rows_sum_to_exactly_one_as_fractions(name, request):
    kernel = request.getfixturevalue(name)
    assert markov.is_stochastic(kernel) is True
    for i, row in enumerate(kernel):
        assert all(isinstance(x, Fraction) for x in row)
        assert sum(row) == Fraction(1), f"row {i} does not sum to 1 exactly"


@pytest.mark.parametrize("name", ["kernel_independent", "kernel_yarrow"])
def test_kernel_is_irreducible_and_aperiodic(name, request):
    kernel = request.getfixturevalue(name)
    assert markov.is_irreducible(kernel) is True
    assert markov.is_aperiodic(kernel) is True


# --------------------------------------------------------------------------
# The independent-mask kernel: symmetric, uniform-stationary
# --------------------------------------------------------------------------

def test_independent_mask_kernel_is_symmetric(kernel_independent):
    assert markov.is_symmetric(kernel_independent) is True


def test_independent_mask_kernel_depends_only_on_the_xor(kernel_independent):
    """P(i -> j) is a function of i XOR j alone."""
    for i in range(N_HEXAGRAMS):
        for j in range(N_HEXAGRAMS):
            assert kernel_independent[i][j] == kernel_independent[0][i ^ j]


def test_uniform_is_exactly_stationary_for_the_independent_mask_kernel(
    kernel_independent,
):
    assert markov.check_stationary(kernel_independent, UNIFORM) is True


def test_independent_mask_entries_are_the_expected_exact_rationals(kernel_independent):
    """P(i -> j) = (1/4)^w (3/4)^(6-w) with w the Hamming distance."""
    from fuxi.encoding import yang_count

    for i in (0, 21, 63):
        for j in range(N_HEXAGRAMS):
            w = yang_count(i ^ j)
            expected = Fraction(1, 4) ** w * Fraction(3, 4) ** (6 - w)
            assert kernel_independent[i][j] == expected
    # Staying put is the most likely single outcome.
    assert kernel_independent[0][0] == Fraction(3, 4) ** 6


# --------------------------------------------------------------------------
# The yarrow kernel: not symmetric, uniform is not stationary
# --------------------------------------------------------------------------

def test_yarrow_kernel_is_not_symmetric(kernel_yarrow):
    assert markov.is_symmetric(kernel_yarrow) is False


def test_yarrow_kernel_asymmetry_is_visible_on_a_single_pair(kernel_yarrow):
    """Kun -> Qian and Qian -> Kun have different probabilities."""
    up = kernel_yarrow[KUN][QIAN]      # six yin lines all flip: (1/8)^6
    down = kernel_yarrow[QIAN][KUN]    # six yang lines all flip: (3/8)^6
    assert up == Fraction(1, 8) ** 6
    assert down == Fraction(3, 8) ** 6
    assert up != down
    assert down == 729 * up


def test_uniform_is_not_stationary_for_the_yarrow_kernel(kernel_yarrow):
    assert markov.check_stationary(kernel_yarrow, UNIFORM) is False


def test_product_form_is_exactly_stationary_for_the_yarrow_kernel(
    kernel_yarrow, product_stationary
):
    assert markov.check_stationary(kernel_yarrow, product_stationary) is True


def test_product_form_is_a_probability_distribution(product_stationary):
    assert all(isinstance(p, Fraction) and p > 0 for p in product_stationary)
    assert sum(product_stationary) == Fraction(1)
    assert len(product_stationary) == 64


def test_stationary_mass_at_kun_over_qian_is_exactly_729(product_stationary):
    """pi(h) = (1/4)^yang (3/4)^yin, so pi(Kun)/pi(Qian) = 3^6 = 729."""
    assert product_stationary[KUN] == Fraction(729, 4096)
    assert product_stationary[QIAN] == Fraction(1, 4096)
    assert product_stationary[KUN] / product_stationary[QIAN] == 729


def test_product_form_reduces_to_uniform_when_the_flip_rates_are_equal():
    """Sanity check on the formula: equal conditionals give the uniform law."""
    pi = markov.stationary_product_form(Fraction(1, 4), Fraction(1, 4))
    assert pi == UNIFORM


def test_power_iteration_approaches_the_exact_stationary_laws(
    kernel_independent, kernel_yarrow, product_stationary
):
    """Numeric cross-check of the exact results. Tolerance: 1e-9 absolute."""
    num_a = markov.stationary_by_power_iteration(kernel_independent, iterations=200)
    for value in num_a:
        assert value == pytest.approx(1 / 64, abs=1e-9)

    num_b = markov.stationary_by_power_iteration(kernel_yarrow, iterations=200)
    for value, exact in zip(num_b, product_stationary):
        assert value == pytest.approx(float(exact), abs=1e-9)


# --------------------------------------------------------------------------
# Spectrum
# --------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["kernel_independent", "kernel_yarrow"])
def test_spectral_gap_is_one_half(name, request):
    """Both kernels are tensor sixth powers of a two-state chain with lambda2 = 1/2.

    Independent mask: lambda2 = 1 - 2p = 1/2.
    Yarrow:           lambda2 = 1 - q_yin - q_yang = 1 - 1/8 - 3/8 = 1/2.

    Tolerance: 1e-9 absolute, on a numpy eigenvalue computation.
    """
    kernel = request.getfixturevalue(name)
    assert markov.spectral_gap(kernel) == pytest.approx(0.5, abs=EIG_TOL)


def test_analytic_eigenvalue_multiset_is_the_binomial_row():
    analytic = markov.analytic_eigenvalues(Fraction(1, 2))
    assert analytic == {Fraction(1, 2) ** k: comb(6, k) for k in range(7)}
    assert sum(analytic.values()) == 64
    assert analytic[Fraction(1)] == 1


@pytest.mark.parametrize("name", ["kernel_independent", "kernel_yarrow"])
def test_numeric_eigenvalues_match_the_analytic_multiset(name, request):
    """Compare multisets. Numeric values are rounded at 1e-9 before counting."""
    kernel = request.getfixturevalue(name)
    numeric = markov.numeric_eigenvalues(kernel)
    assert len(numeric) == 64

    analytic = markov.analytic_eigenvalues(Fraction(1, 2))
    observed = Counter(round(v, 9) for v in numeric)
    expected = Counter()
    for lam, mult in analytic.items():
        expected[round(float(lam), 9)] += mult
    assert observed == expected


@pytest.mark.parametrize("name", ["kernel_independent", "kernel_yarrow"])
def test_leading_eigenvalue_is_one(name, request):
    kernel = request.getfixturevalue(name)
    values = markov.numeric_eigenvalues(kernel)
    assert values[0] == pytest.approx(1.0, abs=EIG_TOL)


# --------------------------------------------------------------------------
# Mixing
# --------------------------------------------------------------------------

def test_total_variation_of_a_distribution_with_itself_is_zero():
    assert markov.total_variation(UNIFORM, UNIFORM) == 0.0


def test_total_variation_of_two_disjoint_point_masses_is_one():
    a = [Fraction(1)] + [Fraction(0)] * 63
    b = [Fraction(0)] * 63 + [Fraction(1)]
    assert markov.total_variation(a, b) == pytest.approx(1.0, abs=1e-12)


def test_mixing_times_are_finite_and_small(kernel_independent, kernel_yarrow,
                                           product_stationary):
    t_a = markov.mixing_time(kernel_independent, UNIFORM)
    t_b = markov.mixing_time(kernel_yarrow, product_stationary)
    for t in (t_a, t_b):
        assert t > 0, "mixing_time returned -1, meaning it never converged"
        assert t < 50, "mixing should take order log(64) steps, not dozens"
