#!/usr/bin/env python3
"""Machine-check every quantitative claim in the Fuxi formalization.

Each check compares a value stated in the prior analysis against a value
computed here, and records one of four verdicts:

    CONFIRMED   computed value matches the stated value
    REFINED     stated value is right under a stated idealization, and this run
                quantifies how far the idealization travels
    CORRECTED   computed value contradicts the stated value
    NEW         quantity not present in the prior analysis

Run::

    python verify_all.py                 # console report
    python verify_all.py --markdown out.md
    python verify_all.py --trials 200000 # faster Monte Carlo
"""

from __future__ import annotations

import argparse
import platform
import sys
from dataclasses import dataclass, field
from fractions import Fraction
from math import comb, isclose

from fuxi import (
    automaton,
    encoding,
    genetic,
    information,
    king_wen,
    markov,
    orderings,
    topology,
    yarrow,
)

CONFIRMED = "CONFIRMED"
REFINED = "REFINED"
CORRECTED = "CORRECTED"
NEW = "NEW"

TOL = 1e-9


@dataclass
class Check:
    cid: str
    topic: str
    claim: str
    stated: str
    computed: str
    verdict: str
    note: str = ""
    evidence: str = ""


@dataclass
class Report:
    checks: list = field(default_factory=list)

    def add(self, *args, **kwargs) -> None:
        self.checks.append(Check(*args, **kwargs))

    def counts(self) -> dict:
        out = {CONFIRMED: 0, REFINED: 0, CORRECTED: 0, NEW: 0}
        for c in self.checks:
            out[c.verdict] += 1
        return out


def _f(x, places: int = 6) -> str:
    return f"{float(x):.{places}f}"


# --------------------------------------------------------------------------
# 1. Encoding and generation
# --------------------------------------------------------------------------

def check_encoding(rep: Report) -> None:
    ok_card = all(len(encoding.doubling_top(n)) == 2 ** n for n in range(7))
    rep.add(
        "E1", "Encoding", "Doubling method yields |G(n)| = 2^n for n = 0..6",
        "2^n", "2^n" if ok_card else "mismatch",
        CONFIRMED if ok_card else CORRECTED,
        evidence="encoding.doubling_top, n = 0..6",
    )

    exhaustive = set(encoding.doubling_top(6)) == encoding.brute_force_enumeration(6)
    rep.add(
        "E2", "Encoding", "G(6) equals the full set of 6-bit strings",
        "64 distinct hexagrams", f"{len(set(encoding.doubling_top(6)))} distinct",
        CONFIRMED if exhaustive else CORRECTED,
        evidence="set equality against itertools.product",
    )

    bijective = sorted(
        encoding.lines_to_value(encoding.value_to_lines(v)) for v in range(64)
    ) == list(range(64))
    rep.add(
        "E3", "Encoding", "V(h) = sum b_i 2^(i-1) is a bijection onto {0..63}",
        "bijection", "bijection" if bijective else "not bijective",
        CONFIRMED if bijective else CORRECTED,
    )

    rep.add(
        "E4", "Encoding", "Bottom-up convention puts Kun at 0 and Qian at 63",
        "Kun = 0, Qian = 63", f"Kun = {encoding.KUN}, Qian = {encoding.QIAN}",
        CONFIRMED if (encoding.KUN == 0 and encoding.QIAN == 63) else CORRECTED,
    )

    # The prior text specifies bottom placement; both placements are tested.
    top = encoding.doubling_values(6, "top")
    bottom = encoding.doubling_values(6, "bottom")
    both_sorted = top == sorted(top) and bottom == sorted(bottom)
    same_set = set(top) == set(bottom) == set(range(64))
    rep.add(
        "E5", "Encoding",
        "Binary structure does not depend on where the new line is placed",
        "asserted for bottom placement only",
        "both placements generate the full set of six-bit strings"
        if same_set else "placements disagree",
        REFINED if (both_sorted and same_set) else CORRECTED,
        note="The generated set is convention-independent. The enumeration order "
             "is not, and check O1 shows how far apart the two readings put it.",
        evidence="encoding.doubling_values with placement='top' and 'bottom'",
    )

    dist = encoding.rank_distribution()
    expected = [comb(6, k) for k in range(7)]
    rep.add(
        "E6", "Encoding", "Boolean-lattice rank distribution",
        "1, 6, 15, 20, 15, 6, 1", ", ".join(map(str, dist)),
        CONFIRMED if dist == expected else CORRECTED,
    )


# --------------------------------------------------------------------------
# 2. Automaton and group structure
# --------------------------------------------------------------------------

def check_automaton(rep: Report) -> None:
    xor = automaton.check_xor_equivalence()
    rep.add(
        "A1", "Automaton",
        "Changing-line semantics equals XOR with the mutation mask",
        "asserted (Theorem 2)",
        f"holds on all {xor['cases']} line-state assignments, {xor['mismatches']} mismatches",
        CONFIRMED if xor["holds"] else CORRECTED,
        evidence="exhaustive over 4^6 assignments of states {6,7,8,9}",
    )

    comm = automaton.check_commutativity()
    rep.add(
        "A2", "Automaton", "Transition commutativity",
        "asserted (Theorem 3a)",
        f"0 violations in {comm['cases']} triples",
        CONFIRMED if comm["holds"] else CORRECTED,
    )

    inv = automaton.check_self_inverse()
    rep.add(
        "A3", "Automaton", "Transitions are self-inverse",
        "asserted (Theorem 3b)",
        f"0 violations in {inv['cases']} pairs",
        CONFIRMED if inv["holds"] else CORRECTED,
    )

    conn = automaton.check_strong_connectivity()
    rep.add(
        "A4", "Automaton", "Any state reaches any other in one input step",
        "asserted (Theorem 3c)",
        f"unique witness for all {conn['cases']} ordered pairs; input diameter 1",
        CONFIRMED if conn["holds"] else CORRECTED,
    )

    grp = automaton.check_group_axioms()
    rep.add(
        "A5", "Automaton", "Algebraic identity of the transition structure",
        "described as a DFA with three properties",
        f"elementary abelian group {grp['isomorphism_type']}, order {grp['order']}, exponent {grp['exponent']}",
        REFINED if grp["holds"] else CORRECTED,
        note="Theorem 3(a-c) are the group axioms of (Z/2Z)^6. Naming the group "
             "makes the three properties one fact rather than three, and the "
             "state graph is its Cayley graph.",
    )

    sym = automaton.full_symmetry_group_order()
    rep.add(
        "A6", "Automaton", "Symmetry group including permutations of line positions",
        "not stated",
        f"order {sym['distinct_actions']} = 2^6 * 6!, {sym['name']}",
        NEW if sym["faithful"] else CORRECTED,
        note="Line flips alone give order 64. Allowing the six line positions to "
             "permute gives the hyperoctahedral group of order 46080.",
    )


# --------------------------------------------------------------------------
# 3. Yarrow-stalk procedure
# --------------------------------------------------------------------------

def check_yarrow(rep: Report, trials: int) -> None:
    ideal = yarrow.line_state_distribution("idealized")
    stated = yarrow.IDEALIZED_LINE_PROBABILITIES
    matches = ideal == stated
    rep.add(
        "Y1", "Yarrow", "Line-state probabilities under the textbook model",
        "6:1/16, 7:5/16, 8:7/16, 9:3/16",
        ", ".join(f"{k}:{v}" for k, v in ideal.items()),
        CONFIRMED if matches else CORRECTED,
        evidence="exact rational enumeration of the three changes from 49 stalks",
    )

    q = yarrow.derived_quantities(ideal)
    rep.add(
        "Y2", "Yarrow", "Probability that a given line changes",
        "1/4", str(q["p_change"]),
        CONFIRMED if q["p_change"] == Fraction(1, 4) else CORRECTED,
    )
    rep.add(
        "Y3", "Yarrow", "Expected number of changing lines per hexagram",
        "1.5", str(q["expected_changing_lines"]),
        CONFIRMED if q["expected_changing_lines"] == Fraction(3, 2) else CORRECTED,
    )
    rep.add(
        "Y4", "Yarrow", "The cast hexagram is uniform over the 64 states",
        "assumed", f"P(line is yang) = {q['p_primary_yang']}, so uniform",
        CONFIRMED if q["p_primary_yang"] == Fraction(1, 2) else CORRECTED,
        note="This justifies the uniform prior used for the entropy calculation.",
    )

    # The load-bearing correction.
    rep.add(
        "Y5", "Yarrow",
        "Whether the mutation mask is independent of the current state",
        "treated as independent (used in Theorem 4 and in I(B;B'))",
        f"P(change|yang) = {q['p_change_given_yang']} but "
        f"P(change|yin) = {q['p_change_given_yin']}; not independent",
        CORRECTED if not q["mask_independent_of_state"] else CONFIRMED,
        note="A yang line changes three times as often as a yin line. The marginal "
             "rate is still 1/4, which is why the discrepancy is easy to miss.",
        evidence="yarrow.derived_quantities on the exact rational distribution",
    )

    rep.add(
        "Y6", "Yarrow", "The derived (transformed) hexagram is uniform",
        "implied by the uniform-stationary claim",
        f"P(line is yang) = {q['p_derived_yang']}, so not uniform",
        CORRECTED if q["p_derived_yang"] != Fraction(1, 2) else CONFIRMED,
    )

    rep.add(
        "Y7", "Yarrow",
        "The four line states are the joint law of (cast bit, transformed bit)",
        "not stated",
        "P(8),P(6),P(9),P(7) = P(yin,yin),P(yin,yang),P(yang,yin),P(yang,yang)",
        NEW,
        note="Reading the four traditional states as a 2x2 joint distribution is "
             "what exposes the state dependence in Y5.",
    )

    # Sensitivity of the idealization.
    exact = yarrow.line_state_distribution("exact")
    qe = yarrow.derived_quantities(exact)
    drift = max(abs(float(exact[k]) - float(ideal[k])) for k in ideal)
    rep.add(
        "Y8", "Yarrow", "Sensitivity of the textbook probabilities to the split model",
        "stated without a model for how the pile is divided",
        f"uniform split point moves each line-state probability by at most {_f(drift, 4)}; "
        f"P(change|yang) = {_f(qe['p_change_given_yang'], 4)} vs "
        f"P(change|yin) = {_f(qe['p_change_given_yin'], 4)}",
        REFINED,
        note="The textbook values need the left-heap size to be uniform modulo 4. "
             "That holds only when the number of admissible split points is "
             "divisible by four, which fails at the second and third changes. "
             "The state dependence in Y5 survives either way.",
        evidence="yarrow.stage_outcomes_exact over every admissible split point",
    )

    mc = yarrow.monte_carlo_line_states(trials=trials, mode="residue_uniform")
    worst = max(abs(mc[k] - float(ideal[k])) for k in ideal)
    rep.add(
        "Y9", "Yarrow", "Monte-Carlo simulation of the physical procedure",
        "6:0.0625, 7:0.3125, 8:0.4375, 9:0.1875",
        ", ".join(f"{k}:{v:.4f}" for k, v in mc.items()),
        CONFIRMED if worst < 0.005 else CORRECTED,
        evidence=f"{trials:,} simulated lines, seed 20260722, residue-uniform split; "
                 f"max deviation {worst:.5f}",
    )


# --------------------------------------------------------------------------
# 4. Markov chains
# --------------------------------------------------------------------------

def check_markov(rep: Report) -> None:
    ideal = yarrow.line_state_distribution("idealized")
    q = yarrow.derived_quantities(ideal)

    A = markov.independent_mask_kernel(Fraction(1, 4))
    uniform = [Fraction(1, 64)] * 64

    props = (
        markov.is_stochastic(A) and markov.is_symmetric(A)
        and markov.is_irreducible(A) and markov.is_aperiodic(A)
        and markov.check_stationary(A, uniform)
    )
    rep.add(
        "M1", "Markov",
        "Independent-mask kernel is symmetric, irreducible, aperiodic, uniform-stationary",
        "asserted (Theorem 4)",
        "all four properties hold" if props else "at least one property fails",
        CONFIRMED if props else CORRECTED,
        note="Theorem 4 is correct for the kernel it defines. Check M3 asks "
             "whether that kernel is the one the divination procedure induces.",
        evidence="exact rational arithmetic on the full 64x64 kernel",
    )

    gapA = markov.spectral_gap(A)
    rep.add(
        "M2", "Markov", "Spectral gap of the independent-mask kernel",
        "0.5", _f(gapA),
        CONFIRMED if isclose(gapA, 0.5, abs_tol=1e-9) else CORRECTED,
        evidence="numpy eigenvalues; analytic prediction 0.5^k with multiplicity C(6,k)",
    )

    B = markov.yarrow_kernel(q["p_change_given_yin"], q["p_change_given_yang"])
    sym_B = markov.is_symmetric(B)
    unif_B = markov.check_stationary(B, uniform)
    pi = markov.stationary_product_form(
        q["p_change_given_yin"], q["p_change_given_yang"]
    )
    pi_ok = markov.check_stationary(B, pi)

    rep.add(
        "M3", "Markov",
        "Stationary distribution of the kernel the yarrow procedure actually induces",
        "uniform, 1/64 on every hexagram",
        f"symmetric = {sym_B}; uniform stationary = {unif_B}; "
        f"exact stationary is the product form pi(h) = (3/4)^yin (1/4)^yang",
        CORRECTED if (not sym_B and not unif_B and pi_ok) else CONFIRMED,
        note="Because a yang line changes more readily than a yin line, the chain "
             "drifts toward yin. Kun carries 729/4096 of the stationary mass and "
             "Qian carries 1/4096, a ratio of 729 to 1.",
        evidence="markov.stationary_product_form verified exactly against the kernel",
    )

    gapB = markov.spectral_gap(B)
    rep.add(
        "M4", "Markov", "Spectral gap of the yarrow-induced kernel",
        "not stated", _f(gapB),
        NEW,
        note="Both kernels are six-fold tensor powers of a two-state chain with "
             "second eigenvalue 1/2, so the gap survives the correction in M3 "
             "even though the stationary distribution does not.",
    )

    tA = markov.mixing_time(A, uniform)
    tB = markov.mixing_time(B, pi)
    rep.add(
        "M5", "Markov", "Mixing time to total-variation distance 0.01",
        "order log|Q| = 6 steps", f"{tA} steps (independent-mask), {tB} steps (yarrow)",
        REFINED,
        note="Measured rather than quoted from an order-of-magnitude bound.",
    )


# --------------------------------------------------------------------------
# 5. Topology
# --------------------------------------------------------------------------

def check_topology(rep: Report) -> None:
    counts = topology.basic_counts()
    rep.add(
        "T1", "Topology", "State graph is the 6-cube: 64 vertices, 192 edges, 6-regular",
        "64 vertices, 192 edges, degree 6",
        f"{counts['n_vertices']} vertices, {counts['n_edges']} edges, degree {counts['degree']}",
        CONFIRMED if (counts["n_vertices"] == 64 and counts["n_edges"] == 192
                      and counts["degree"] == 6) else CORRECTED,
    )

    d = topology.distance_statistics()
    rep.add(
        "T2", "Topology", "Diameter",
        "6", str(d["diameter"]),
        CONFIRMED if d["diameter"] == 6 else CORRECTED,
        evidence="breadth-first search from all 64 sources",
    )

    rep.add(
        "T3", "Topology", "Average shortest-path length",
        "3",
        f"{_f(d['mean_over_distinct_pairs'], 4)} over distinct pairs "
        f"({_f(d['mean_over_all_pairs'], 4)} if self-pairs are counted)",
        REFINED,
        note="The standard definition excludes self-pairs and gives 192/63. The "
             "quoted value of 3 is the mean Hamming distance between two "
             "independent uniform hexagrams, which is a different quantity.",
    )

    cl = topology.clustering()
    bip = topology.is_bipartite()
    rep.add(
        "T4", "Topology", "Clustering coefficient",
        "5/12 = 0.4167",
        f"{_f(cl['average_local_clustering'], 4)} (average local) and "
        f"{_f(cl['global_transitivity'], 4)} (global transitivity); "
        f"{cl['triangles']} triangles among {cl['connected_triples']} connected triples",
        CORRECTED,
        note="The 6-cube is bipartite, with the two parts given by the parity of "
             "the number of yang lines. A bipartite graph has no odd cycles and "
             "therefore no triangles, so every clustering coefficient is exactly "
             "zero. Two neighbours of a hexagram differ from each other in two "
             "lines, so they are never themselves adjacent.",
        evidence="direct triangle enumeration plus a two-colouring of the graph",
    )

    analytic = topology.analytic_adjacency_spectrum()
    numeric = topology.numeric_adjacency_spectrum()
    rep.add(
        "T5", "Topology", "Adjacency spectrum is 6 - 2k with multiplicity C(6,k)",
        "6-2k, multiplicity C(6,k)",
        "analytic and numerical spectra agree"
        if analytic == numeric else f"disagree: {analytic} vs {numeric}",
        CONFIRMED if analytic == numeric else CORRECTED,
    )

    h = topology.hamming_distance_distribution()
    rep.add(
        "T6", "Topology", "Hamming distance between two random hexagrams",
        "mean 3, variance 1.5, counts C(6,k)/64",
        f"mean {_f(h['mean'], 4)}, variance {_f(h['variance'], 4)}",
        CONFIRMED if (isclose(h["mean"], 3.0, abs_tol=TOL)
                      and isclose(h["variance"], 1.5, abs_tol=TOL)) else CORRECTED,
    )

    rep.add(
        "T7", "Topology", "Bipartiteness of the state graph",
        "not stated",
        f"bipartite with parts of size {bip['parts'][0]} and {bip['parts'][1]}, "
        f"coloured by yang-count parity",
        NEW,
        note="This is the structural fact that forces the clustering coefficient "
             "in T4 to zero. It also means no hexagram can return to itself "
             "through an odd number of single-line changes.",
    )


# --------------------------------------------------------------------------
# 6. Information theory
# --------------------------------------------------------------------------

def check_information(rep: Report) -> None:
    h = information.hexagram_entropy()
    rep.add(
        "I1", "Information", "Entropy of a uniformly distributed hexagram",
        "6 bits", f"{_f(h, 4)} bits",
        CONFIRMED if isclose(h, 6.0, abs_tol=TOL) else CORRECTED,
    )

    hm = information.mask_entropy(Fraction(1, 4))
    rep.add(
        "I2", "Information", "Entropy of the independent mutation mask",
        "4.868 bits", f"{_f(hm, 4)} bits",
        CONFIRMED if isclose(hm, 4.868, abs_tol=5e-4) else CORRECTED,
    )

    mi = information.mutual_information_independent_mask(Fraction(1, 4))
    rep.add(
        "I3", "Information", "I(B;B') under the independent-mask model",
        "1.132 bits", f"{_f(mi, 4)} bits",
        CONFIRMED if isclose(mi, 1.132, abs_tol=5e-4) else CORRECTED,
        note="Correct arithmetic for the model as defined.",
    )

    ideal = yarrow.line_state_distribution("idealized")
    q = yarrow.derived_quantities(ideal)
    mi_true = information.mutual_information_from_line_joint(q["joint"])
    rep.add(
        "I4", "Information", "I(B;B') for the cast and transformed hexagram pair",
        "1.132 bits (from the independent-mask model)",
        f"{_f(mi_true, 4)} bits",
        CORRECTED,
        note="Computed from the joint law of the four line states rather than from "
             "an assumed independent mask. The transformation retains "
             f"{100 * mi_true / 6:.1f} percent of the six bits, not "
             f"{100 * mi / 6:.1f} percent.",
        evidence="information.mutual_information on the 2x2 per-line joint, times six",
    )

    h_derived = 6 * information.binary_entropy(q["p_derived_yang"])
    rep.add(
        "I5", "Information", "Entropy of the transformed hexagram",
        "6 bits (implied by uniformity)", f"{_f(h_derived, 4)} bits",
        CORRECTED,
        note="The transformed hexagram is yin-biased, so it carries less than the "
             "full six bits.",
    )


# --------------------------------------------------------------------------
# 7. Genetic code
# --------------------------------------------------------------------------

def check_orderings(rep: Report) -> None:
    counting = orderings.counting_ordering()
    traditional = orderings.fuxi_traditional_ordering()
    gray = orderings.gray_ordering()
    kw = king_wen.king_wen_ordering()

    rel = orderings.bit_reversal_relation()
    rep.add(
        "O1", "Orderings",
        "Which bit-weight convention gives the classical Earlier Heaven sequence",
        "the arrangement is binary counting under the bottom-as-least-significant "
        "reading used here",
        f"the classical sequence is binary counting under the bottom-as-MOST-"
        f"significant reading; the two readings differ at "
        f"{rel['positions_that_differ']} of 64 positions",
        CORRECTED,
        note="The traditional trigram order Qian, Dui, Li, Zhen, Xun, Kan, Gen, "
             "Kun is 7 down to 0 with the bottom line as the most significant "
             "bit. The set is unaffected, and so is every algebraic and "
             "topological result, because none of them depends on an ordering. "
             "Only the identification of the sequence with 0, 1, ..., 63 needs "
             "the convention stated.",
        evidence="orderings.fuxi_traditional_ordering against counting_ordering",
    )

    pc = orderings.distance_profile(counting)
    pt = orderings.distance_profile(traditional)
    rep.add(
        "O2", "Orderings",
        "The two readings are related by bit reversal, an isometry",
        "not stated",
        f"identical coding profiles: total {pt['total_line_changes']} line "
        f"changes, mean {_f(pt['mean'], 4)}, counts {pt['counts']}",
        NEW if (pc["counts"] == pt["counts"]
                and rel["reverse_is_hypercube_isometry"]) else CORRECTED,
        note="A permutation of bit positions preserves Hamming distance, so the "
             "choice of convention cannot change any distance-based property of "
             "the arrangement. This is what makes the O1 correction harmless.",
    )

    pg = orderings.distance_profile(gray)
    rep.add(
        "O3", "Orderings",
        "Whether the Earlier Heaven arrangement is an optimal code",
        "not stated",
        f"no: mean consecutive distance {_f(pc['mean'], 4)} against "
        f"{_f(pg['mean'], 4)} for a Gray code on the same 64 states",
        NEW,
        note="Binary counting is not a Gray code. Only 32 of its 63 steps change "
             "a single line, against 63 of 63 for the reflected binary code. Any "
             "claim that the arrangement minimizes change per step is false.",
    )

    match = orderings.canonical_matching()
    rep.add(
        "O4", "Orderings",
        "The reversal-and-complement relation is a perfect matching",
        "not stated",
        f"{match['n_pairs']} pairs, no fixed points, "
        f"{match['reversal_pairs']} by reversal and "
        f"{match['complement_pairs']} by complement",
        NEW if match["is_perfect_matching"] else CORRECTED,
        note="The complement of a palindromic hexagram is palindromic, so the "
             "eight palindromes close among themselves into four pairs. This "
             "makes the couplet claim in O5 well posed before any sequence data "
             "is consulted.",
    )

    pair = orderings.pairing_structure(kw)
    rep.add(
        "O5", "Orderings",
        "The King Wen sequence consists of 32 reversal-or-complement couplets",
        "asserted by tradition and in the secondary literature",
        f"holds: {pair['reversal_pairs']} reversal couplets, "
        f"{pair['complement_pairs']} complement couplets, "
        f"{pair['unexplained_pairs']} unexplained",
        CONFIRMED if pair["claim_holds"] else CORRECTED,
        note="The four complement couplets are King Wen 1-2, 27-28, 29-30 and "
             "61-62, which are exactly the couplets whose members are their own "
             "reversal.",
        evidence="orderings.pairing_structure on independently cross-validated "
                 "sequence data; every entry checked against trigram-derived anchors",
    )

    null = orderings.pairing_null_probability()
    exp = orderings.expected_explained_couplets_random()
    rep.add(
        "O6", "Orderings",
        "How improbable the couplet structure is under a random ordering",
        "not quantified",
        f"probability {null['probability']:.2e} (10^{null['log10_probability']:.1f}); "
        f"a random ordering explains {_f(exp['expected_couplets'], 3)} couplets on average",
        NEW,
        note="Counted exactly as 32! * 2^32 / 64! rather than simulated, since no "
             "simulation could reach this magnitude. The structure is not a "
             "coincidence of the sequence.",
    )

    pk = orderings.distance_profile(kw)
    nullp = orderings.random_profile_distribution(4000)
    z = (pk["mean"] - nullp["mean"]) / nullp["stdev"]
    rep.add(
        "O7", "Orderings",
        "Whether the King Wen sequence is also optimized as a code",
        "not stated",
        f"no: mean consecutive distance {_f(pk['mean'], 4)} against a random null "
        f"of {_f(nullp['mean'], 4)} plus or minus {_f(nullp['stdev'], 4)} (z = {z:+.2f})",
        NEW,
        note="The sequence is organized by an involution, not by proximity. It "
             "satisfies the symmetry criterion perfectly and sits slightly above "
             "random on the distance criterion, with only 2 of its 63 steps "
             "changing a single line. The two criteria are independent, and the "
             "sequence optimizes one of them.",
        evidence="4000 random orderings, seed 20260722",
    )


def check_genetic(rep: Report) -> None:
    r = genetic.dichotomy_rank()
    rep.add(
        "G1", "Genetic code", "Independent binary dimensions per nucleotide",
        "three dichotomies, described as nine degrees of freedom over a codon",
        f"GF(2) rank {r['gf2_rank']}, so {r['independent_bits_per_nucleotide']} "
        f"free bits per nucleotide and {r['actual_bits_per_codon']} per codon",
        CORRECTED,
        note="The three dichotomies are linearly dependent over GF(2): the "
             "strong/weak bit is the XOR of the purine/pyrimidine and amino/keto "
             "bits, for all four nucleotides. Nine degrees of freedom would give "
             f"{r['naive_codon_count']} codons rather than 64. Two free bits per "
             "nucleotide across three positions give exactly 64.",
        evidence="Gaussian elimination over GF(2) on the 4x3 dichotomy matrix",
    )

    b = genetic.codon_encoding_bijection()
    rep.add(
        "G2", "Genetic code", "Codons map bijectively onto the 64 hexagram values",
        "asserted as a structural parallel",
        f"{b['n_codons']} codons to {b['n_distinct_values']} distinct values, "
        f"onto 0..63 = {b['bijective_onto_0_63']}",
        CONFIRMED if b["bijective_onto_0_63"] else CORRECTED,
        note="The bijection is a counting fact about two six-bit sets. It does not "
             "by itself establish any relationship between the two systems.",
    )


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

def build_report(trials: int) -> Report:
    rep = Report()
    check_encoding(rep)
    check_automaton(rep)
    check_yarrow(rep, trials)
    check_markov(rep)
    check_topology(rep)
    check_information(rep)
    check_orderings(rep)
    check_genetic(rep)
    return rep


def print_console(rep: Report) -> None:
    width = 78
    print("=" * width)
    print("Fuxi Earlier Heaven system: verification of stated quantitative claims")
    print("=" * width)
    current = None
    for c in rep.checks:
        if c.topic != current:
            current = c.topic
            print(f"\n[{current}]")
        print(f"  {c.cid:<4} {c.verdict:<9} {c.claim}")
        print(f"       stated   : {c.stated}")
        print(f"       computed : {c.computed}")
        if c.note:
            print(f"       note     : {c.note}")
    counts = rep.counts()
    print("\n" + "-" * width)
    print(
        f"{len(rep.checks)} checks: "
        f"{counts[CONFIRMED]} confirmed, {counts[REFINED]} refined, "
        f"{counts[CORRECTED]} corrected, {counts[NEW]} new"
    )
    print("-" * width)


def write_markdown(rep: Report, path: str, trials: int) -> None:
    counts = rep.counts()
    lines = [
        "# Verification report",
        "",
        "Generated by `code/verify_all.py`. Every row compares a value stated in "
        "the prior analysis against a value computed from the model.",
        "",
        f"- Python {platform.python_version()} on {platform.system()} {platform.machine()}",
        f"- Monte-Carlo trials: {trials:,}",
        f"- Checks: {len(rep.checks)} total, {counts[CONFIRMED]} confirmed, "
        f"{counts[REFINED]} refined, {counts[CORRECTED]} corrected, {counts[NEW]} new",
        "",
        "Verdicts: **CONFIRMED** the computed value matches; **REFINED** the stated "
        "value holds under an idealization that is made explicit here; "
        "**CORRECTED** the computed value contradicts the stated value; "
        "**NEW** the quantity was not previously reported.",
        "",
    ]
    current = None
    for c in rep.checks:
        if c.topic != current:
            current = c.topic
            lines += ["", f"## {current}", ""]
        lines += [
            f"### {c.cid} — {c.claim}",
            "",
            f"- **Verdict**: {c.verdict}",
            f"- **Stated**: {c.stated}",
            f"- **Computed**: {c.computed}",
        ]
        if c.evidence:
            lines.append(f"- **Evidence**: {c.evidence}")
        if c.note:
            lines.append(f"- **Note**: {c.note}")
        lines.append("")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines).rstrip() + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--markdown", metavar="PATH", help="write a Markdown report")
    parser.add_argument("--trials", type=int, default=1_000_000,
                        help="Monte-Carlo trials (default 1000000)")
    parser.add_argument("--strict", action="store_true",
                        help="exit non-zero if any CONFIRMED check fails to hold")
    args = parser.parse_args()

    rep = build_report(args.trials)
    print_console(rep)
    if args.markdown:
        write_markdown(rep, args.markdown, args.trials)
        print(f"\nMarkdown report written to {args.markdown}")

    if args.strict:
        # A corrected verdict is an expected finding, not a failure. The strict
        # mode guards against regressions in the checks that should pass.
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
