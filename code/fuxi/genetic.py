"""Binary structure of the 64-codon genetic code.

The literature commonly describes each nucleotide through three binary
dichotomies:

    purine / pyrimidine       A, G   vs   C, U
    amino   / keto            A, C   vs   G, U
    strong  / weak            G, C   vs   A, U   (3 vs 2 hydrogen bonds)

Three dichotomies applied at three codon positions look like nine binary
degrees of freedom, which would give 2^9 = 512 codons rather than 64. This
module resolves the discrepancy by computing the rank of the dichotomy matrix
over GF(2).
"""

from __future__ import annotations

from itertools import product

NUCLEOTIDES = ("A", "C", "G", "U")

#: (purine, amino, strong) indicator bits for each nucleotide.
DICHOTOMIES = {
    "A": (1, 1, 0),   # purine, amino, weak
    "C": (0, 1, 1),   # pyrimidine, amino, strong
    "G": (1, 0, 1),   # purine, keto, strong
    "U": (0, 0, 0),   # pyrimidine, keto, weak
}

DICHOTOMY_NAMES = ("purine/pyrimidine", "amino/keto", "strong/weak")


def gf2_rank(rows) -> int:
    """Rank over GF(2) of a list of bit-tuples, by Gaussian elimination."""
    vectors = [int("".join(str(b) for b in row), 2) for row in rows]
    rank = 0
    pivot_rows: list = []
    for v in vectors:
        cur = v
        for p in pivot_rows:
            cur = min(cur, cur ^ p)
        if cur:
            pivot_rows.append(cur)
            pivot_rows.sort(reverse=True)
            rank += 1
    return rank


def dichotomy_rank() -> dict:
    """Rank of the 4x3 nucleotide dichotomy matrix over GF(2).

    A rank below 3 means the three dichotomies are not independent, so each
    nucleotide carries fewer than three free bits.
    """
    columns = [
        tuple(DICHOTOMIES[n][j] for n in NUCLEOTIDES) for j in range(3)
    ]
    rank = gf2_rank(columns)
    # Explicit dependency check: is strong/weak the XOR of the other two?
    xor_identity = all(
        DICHOTOMIES[n][2] == (DICHOTOMIES[n][0] ^ DICHOTOMIES[n][1])
        for n in NUCLEOTIDES
    )
    return {
        "n_dichotomies": 3,
        "gf2_rank": rank,
        "independent_bits_per_nucleotide": rank,
        "strong_weak_is_xor_of_others": xor_identity,
        "naive_degrees_of_freedom": 3 * 3,
        "naive_codon_count": 2 ** 9,
        "actual_bits_per_codon": rank * 3,
        "actual_codon_count": 2 ** (rank * 3),
    }


def codon_encoding_bijection() -> dict:
    """Two free bits per nucleotide give a bijection between codons and 0..63."""
    # Use (purine, amino) as the independent pair; strong/weak is their XOR.
    two_bit = {n: (DICHOTOMIES[n][0], DICHOTOMIES[n][1]) for n in NUCLEOTIDES}
    injective = len(set(two_bit.values())) == len(NUCLEOTIDES)

    codons = ["".join(c) for c in product(NUCLEOTIDES, repeat=3)]
    values = {}
    for codon in codons:
        bits = []
        for base in codon:
            bits.extend(two_bit[base])
        values[codon] = sum(b << i for i, b in enumerate(reversed(bits)))

    return {
        "two_bit_encoding_injective": injective,
        "n_codons": len(codons),
        "n_distinct_values": len(set(values.values())),
        "bijective_onto_0_63": sorted(values.values()) == list(range(64)),
        "example": {c: values[c] for c in ("AAA", "AAC", "UUU", "GGG")},
    }
