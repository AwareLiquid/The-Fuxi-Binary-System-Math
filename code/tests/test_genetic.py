"""Tests for :mod:`fuxi.genetic`.

The three nucleotide dichotomies look like three independent bits, which would
give 2^9 = 512 codons. They are not independent: over GF(2) the dichotomy
matrix has rank 2, so each nucleotide carries two free bits and a codon carries
six -- exactly 64.

Everything here is integer / GF(2) arithmetic, so every assertion is exact.
"""

from __future__ import annotations

from itertools import product

import pytest

from fuxi import genetic


# --------------------------------------------------------------------------
# The dichotomy table
# --------------------------------------------------------------------------

def test_dichotomy_table_matches_the_stated_biochemistry():
    assert genetic.NUCLEOTIDES == ("A", "C", "G", "U")
    assert genetic.DICHOTOMY_NAMES == (
        "purine/pyrimidine", "amino/keto", "strong/weak"
    )
    # (purine, amino, strong)
    assert genetic.DICHOTOMIES == {
        "A": (1, 1, 0),   # purine, amino, weak   (2 hydrogen bonds)
        "C": (0, 1, 1),   # pyrimidine, amino, strong
        "G": (1, 0, 1),   # purine, keto, strong
        "U": (0, 0, 0),   # pyrimidine, keto, weak
    }


def test_each_dichotomy_splits_the_four_nucleotides_two_and_two():
    for j in range(3):
        column = [genetic.DICHOTOMIES[n][j] for n in genetic.NUCLEOTIDES]
        assert sum(column) == 2, f"dichotomy {genetic.DICHOTOMY_NAMES[j]} is unbalanced"


# --------------------------------------------------------------------------
# The rank-2 result
# --------------------------------------------------------------------------

def test_gf2_rank_of_the_dichotomy_matrix_is_two_not_three():
    """The headline correction: two free bits per nucleotide, not three."""
    result = genetic.dichotomy_rank()
    assert result["gf2_rank"] == 2
    assert result["gf2_rank"] != 3
    assert result["n_dichotomies"] == 3
    assert result["independent_bits_per_nucleotide"] == 2


def test_rank_two_gives_six_bits_and_64_codons_not_nine_bits_and_512():
    result = genetic.dichotomy_rank()
    assert result["naive_degrees_of_freedom"] == 9
    assert result["naive_codon_count"] == 512
    assert result["actual_bits_per_codon"] == 6
    assert result["actual_codon_count"] == 64


def test_strong_weak_bit_is_the_xor_of_the_other_two_for_all_four_nucleotides():
    result = genetic.dichotomy_rank()
    assert result["strong_weak_is_xor_of_others"] is True
    for n in genetic.NUCLEOTIDES:
        purine, amino, strong = genetic.DICHOTOMIES[n]
        assert strong == (purine ^ amino), f"XOR identity fails for {n}"


def test_xor_identity_written_out_by_hand_per_nucleotide():
    """Independent check, spelled out rather than looped over the table.

    A = purine(1), amino(1) -> 1 XOR 1 = 0 = weak    (A pairs with U, 2 bonds)
    C = pyrimidine(0), amino(1) -> 0 XOR 1 = 1 = strong  (C pairs with G, 3 bonds)
    G = purine(1), keto(0) -> 1 XOR 0 = 1 = strong
    U = pyrimidine(0), keto(0) -> 0 XOR 0 = 0 = weak
    """
    assert genetic.DICHOTOMIES["A"] == (1, 1, 0) and (1 ^ 1) == 0
    assert genetic.DICHOTOMIES["C"] == (0, 1, 1) and (0 ^ 1) == 1
    assert genetic.DICHOTOMIES["G"] == (1, 0, 1) and (1 ^ 0) == 1
    assert genetic.DICHOTOMIES["U"] == (0, 0, 0) and (0 ^ 0) == 0


def test_the_three_columns_are_linearly_dependent_over_gf2():
    """Column_strong = column_purine XOR column_amino, as 4-bit vectors."""
    purine = tuple(genetic.DICHOTOMIES[n][0] for n in genetic.NUCLEOTIDES)
    amino = tuple(genetic.DICHOTOMIES[n][1] for n in genetic.NUCLEOTIDES)
    strong = tuple(genetic.DICHOTOMIES[n][2] for n in genetic.NUCLEOTIDES)
    assert purine == (1, 0, 1, 0)
    assert amino == (1, 1, 0, 0)
    assert strong == (0, 1, 1, 0)
    assert tuple(a ^ b for a, b in zip(purine, amino)) == strong
    # Any two of the three are independent, so the rank is exactly 2.
    assert genetic.gf2_rank([purine, amino]) == 2
    assert genetic.gf2_rank([purine, strong]) == 2
    assert genetic.gf2_rank([amino, strong]) == 2
    assert genetic.gf2_rank([purine, amino, strong]) == 2


# --------------------------------------------------------------------------
# gf2_rank itself
# --------------------------------------------------------------------------

def test_gf2_rank_on_known_small_cases():
    assert genetic.gf2_rank([]) == 0
    assert genetic.gf2_rank([(0, 0, 0)]) == 0
    assert genetic.gf2_rank([(1, 0, 0)]) == 1
    assert genetic.gf2_rank([(1, 0, 0), (1, 0, 0)]) == 1
    assert genetic.gf2_rank([(1, 0, 0), (0, 1, 0), (0, 0, 1)]) == 3
    # a, b, a XOR b -> rank 2
    assert genetic.gf2_rank([(1, 1, 0), (0, 1, 1), (1, 0, 1)]) == 2


# --------------------------------------------------------------------------
# The codon bijection
# --------------------------------------------------------------------------

def test_codon_encoding_is_a_bijection_onto_0_to_63():
    result = genetic.codon_encoding_bijection()
    assert result["two_bit_encoding_injective"] is True
    assert result["n_codons"] == 64
    assert result["n_distinct_values"] == 64
    assert result["bijective_onto_0_63"] is True


def test_there_are_exactly_64_codons_over_four_nucleotides():
    assert len(list(product(genetic.NUCLEOTIDES, repeat=3))) == 4 ** 3 == 64


def test_codon_examples_are_the_hand_computed_values():
    """Bits are (purine, amino) per base, most significant base first.

    AAA -> A=(1,1) three times -> 111111 -> 63
    UUU -> U=(0,0) three times -> 000000 -> 0
    GGG -> G=(1,0) three times -> 101010 -> 42
    AAC -> (1,1)(1,1)(0,1)      -> 111101 -> 61
    """
    example = genetic.codon_encoding_bijection()["example"]
    assert example["AAA"] == 63
    assert example["UUU"] == 0
    assert example["GGG"] == 42
    assert example["AAC"] == 61


def test_two_bit_encoding_distinguishes_all_four_nucleotides():
    pairs = {n: genetic.DICHOTOMIES[n][:2] for n in genetic.NUCLEOTIDES}
    assert len(set(pairs.values())) == 4
    assert set(pairs.values()) == {(0, 0), (0, 1), (1, 0), (1, 1)}
