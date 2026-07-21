"""Tests for :mod:`fuxi.topology`.

The state-transition graph is the 6-dimensional hypercube Q6: 64 vertices, one
edge per single-line change. Counts, distances and triangle counts are all
integers, so those assertions are exact; only the numpy spectrum carries a
tolerance.
"""

from __future__ import annotations

from math import comb

import pytest

from fuxi import topology
from fuxi.encoding import N_HEXAGRAMS, N_LINES, yang_count


# --------------------------------------------------------------------------
# Basic counts
# --------------------------------------------------------------------------

def test_graph_has_64_vertices_192_edges_and_is_6_regular():
    counts = topology.basic_counts()
    assert counts["n_vertices"] == 64
    assert counts["n_edges"] == 192          # 64 * 6 / 2
    assert counts["degree"] == 6
    assert counts["degrees"] == [6]
    assert counts["regular"] is True


def test_edge_count_is_the_handshake_count():
    assert 64 * 6 // 2 == 192
    assert len(topology.edge_set()) == 192


def test_neighbours_differ_in_exactly_one_line():
    for v in range(N_HEXAGRAMS):
        nbrs = topology.neighbours(v)
        assert len(nbrs) == 6
        assert len(set(nbrs)) == 6
        for u in nbrs:
            assert yang_count(v ^ u) == 1
        assert v not in nbrs, "no self-loops"


def test_adjacency_is_symmetric():
    adj = topology.adjacency()
    assert set(adj) == set(range(64))
    for v, nbrs in adj.items():
        for u in nbrs:
            assert v in adj[u]


# --------------------------------------------------------------------------
# Distances
# --------------------------------------------------------------------------

def test_diameter_is_exactly_six():
    stats = topology.distance_statistics()
    assert stats["diameter"] == 6
    assert stats["connected"] is True


def test_graph_distance_equals_hamming_distance_for_every_pair():
    stats = topology.distance_statistics()
    assert stats["graph_distance_equals_hamming_distance"] is True


def test_graph_distance_equals_hamming_distance_re_derived_by_bfs():
    """Independent re-derivation: run BFS here rather than trusting the flag."""
    for source in range(N_HEXAGRAMS):
        dist = topology.bfs_distances(source)
        assert len(dist) == 64
        for target, d in enumerate(dist):
            assert d == yang_count(source ^ target)
        # Every vertex is at distance 6 from its own complement, so the
        # eccentricity of every vertex is 6 and the diameter is 6.
        assert max(dist) == 6


def test_only_the_complement_is_at_distance_six():
    dist = topology.bfs_distances(0)
    assert [v for v, d in enumerate(dist) if d == 6] == [63]


def test_mean_shortest_path_over_distinct_pairs_is_192_over_63():
    """Sum of Hamming distances over ordered distinct pairs / (64 * 63)."""
    stats = topology.distance_statistics()
    assert stats["mean_over_distinct_pairs"] == pytest.approx(192 / 63, abs=1e-12)
    # Including the 64 self-pairs pulls the average down to exactly 3.
    assert stats["mean_over_all_pairs"] == pytest.approx(3.0, abs=1e-12)


# --------------------------------------------------------------------------
# Clustering -- the key structural result
# --------------------------------------------------------------------------

def test_graph_has_zero_triangles():
    """Q6 is bipartite, so it has no odd cycles and hence no triangles.

    Concretely: two neighbours of a hexagram differ from each other in exactly
    two lines, so they are never adjacent to one another. This is why every
    clustering coefficient below is exactly zero rather than the 5/12 that had
    been claimed.
    """
    assert topology.triangle_count() == 0


def test_clustering_coefficients_are_exactly_zero():
    """Both local and global clustering vanish -- a consequence of bipartiteness.

    These are exact zeros, not small floats, so they are compared with ==.
    """
    cl = topology.clustering()
    assert cl["triangles"] == 0
    assert cl["average_local_clustering"] == 0.0
    assert cl["global_transitivity"] == 0.0
    # The denominator is non-degenerate: there are plenty of connected triples,
    # so the zero comes from the numerator, not from an empty ratio.
    assert cl["connected_triples"] == 64 * comb(6, 2) == 960


def test_no_two_neighbours_of_a_vertex_are_adjacent():
    """Direct re-derivation of the zero-triangle result."""
    adj = topology.adjacency()
    for v in range(N_HEXAGRAMS):
        nbrs = sorted(adj[v])
        for i, a in enumerate(nbrs):
            for b in nbrs[i + 1:]:
                assert yang_count(a ^ b) == 2
                assert b not in adj[a]


# --------------------------------------------------------------------------
# Bipartiteness
# --------------------------------------------------------------------------

def test_graph_is_bipartite_with_parts_of_size_32_and_32():
    bip = topology.is_bipartite()
    assert bip["bipartite"] is True
    assert sorted(bip["parts"]) == [32, 32]
    assert sum(bip["parts"]) == 64


def test_bipartition_is_the_parity_of_the_yang_count():
    bip = topology.is_bipartite()
    assert bip["colouring_is_yang_parity"] is True
    # Re-derived: the number of hexagrams with an even yang count is 32.
    even = sum(1 for v in range(N_HEXAGRAMS) if yang_count(v) % 2 == 0)
    assert even == 32
    assert 64 - even == 32


def test_every_edge_joins_opposite_parities():
    for v in range(N_HEXAGRAMS):
        for u in topology.neighbours(v):
            assert yang_count(v) % 2 != yang_count(u) % 2


# --------------------------------------------------------------------------
# Spectrum
# --------------------------------------------------------------------------

def test_analytic_adjacency_spectrum_is_6_minus_2k_with_multiplicity_c_6_k():
    analytic = topology.analytic_adjacency_spectrum()
    assert analytic == {6 - 2 * k: comb(6, k) for k in range(7)}
    assert analytic == {6: 1, 4: 6, 2: 15, 0: 20, -2: 15, -4: 6, -6: 1}
    assert sum(analytic.values()) == 64


def test_numeric_adjacency_spectrum_agrees_with_the_analytic_one():
    """numeric_adjacency_spectrum rounds eigenvalues within 1e-6 to integers."""
    assert topology.numeric_adjacency_spectrum() == (
        topology.analytic_adjacency_spectrum()
    )


def test_spectrum_is_symmetric_about_zero_as_bipartiteness_requires():
    spectrum = topology.analytic_adjacency_spectrum()
    for lam, mult in spectrum.items():
        assert spectrum[-lam] == mult
    # Sum of eigenvalues is the trace, which is zero (no self-loops).
    assert sum(lam * mult for lam, mult in spectrum.items()) == 0


# --------------------------------------------------------------------------
# Hamming distance distribution
# --------------------------------------------------------------------------

def test_hamming_distance_has_mean_exactly_3_and_variance_exactly_1_5():
    """Distance is Binomial(6, 1/2): mean 6 * 1/2 = 3, variance 6 * 1/4 = 1.5.

    The underlying counts are integers over a power of two, so these floats are
    exactly representable; the tolerance is only guarding the summation order.
    """
    h = topology.hamming_distance_distribution()
    assert h["mean"] == pytest.approx(3.0, abs=1e-12)
    assert h["variance"] == pytest.approx(1.5, abs=1e-12)


def test_hamming_counts_per_source_are_the_binomial_coefficients():
    h = topology.hamming_distance_distribution()
    assert h["counts_per_source"] == [1, 6, 15, 20, 15, 6, 1]
    assert sum(h["counts_per_source"]) == 64


def test_hamming_probabilities_are_binomial_and_sum_to_one():
    h = topology.hamming_distance_distribution()
    assert len(h["probabilities"]) == 7
    assert sum(h["probabilities"]) == pytest.approx(1.0, abs=1e-12)
    for k, p in enumerate(h["probabilities"]):
        assert p == pytest.approx(comb(N_LINES, k) / 64, abs=1e-12)
