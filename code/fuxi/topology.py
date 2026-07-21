"""Topology of the state-transition graph.

Vertices are the 64 hexagrams. Two hexagrams are adjacent when they differ in
exactly one line, i.e. at Hamming distance 1. This is the 6-dimensional
hypercube graph Q_6.

Every metric here is computed from the graph itself rather than quoted from a
formula, so that the reported values are independent checks.
"""

from __future__ import annotations

from collections import deque
from math import comb

from .encoding import N_HEXAGRAMS, N_LINES, yang_count

try:
    import numpy as _np
except ImportError:  # pragma: no cover
    _np = None


def neighbours(v: int) -> list:
    """Hexagrams reachable by flipping exactly one line."""
    return [v ^ (1 << k) for k in range(N_LINES)]


def adjacency() -> dict:
    return {v: set(neighbours(v)) for v in range(N_HEXAGRAMS)}


def edge_set() -> set:
    return {
        frozenset((v, u))
        for v in range(N_HEXAGRAMS)
        for u in neighbours(v)
    }


def basic_counts() -> dict:
    adj = adjacency()
    degrees = {v: len(adj[v]) for v in adj}
    return {
        "n_vertices": N_HEXAGRAMS,
        "n_edges": len(edge_set()),
        "degrees": sorted(set(degrees.values())),
        "regular": len(set(degrees.values())) == 1,
        "degree": next(iter(set(degrees.values()))),
    }


# --------------------------------------------------------------------------
# Distances
# --------------------------------------------------------------------------

def bfs_distances(source: int) -> list:
    dist = [-1] * N_HEXAGRAMS
    dist[source] = 0
    queue = deque([source])
    while queue:
        v = queue.popleft()
        for u in neighbours(v):
            if dist[u] < 0:
                dist[u] = dist[v] + 1
                queue.append(u)
    return dist


def distance_statistics() -> dict:
    """Diameter and mean shortest-path length, measured by BFS.

    The mean is reported two ways, because the two conventions differ and the
    distinction matters when comparing against a quoted value:

    ``mean_over_distinct_pairs``
        averages over ordered pairs with i != j. This is the standard
        definition of average shortest-path length.
    ``mean_over_all_pairs``
        includes the 64 zero-distance self-pairs, which pulls the value down.
    """
    total = 0
    total_distinct = 0
    diameter = 0
    matches_hamming = True
    for v in range(N_HEXAGRAMS):
        dist = bfs_distances(v)
        for u, d in enumerate(dist):
            if d != yang_count(v ^ u):
                matches_hamming = False
            total += d
            if u != v:
                total_distinct += d
        diameter = max(diameter, max(dist))
    n = N_HEXAGRAMS
    return {
        "diameter": diameter,
        "mean_over_distinct_pairs": total_distinct / (n * (n - 1)),
        "mean_over_all_pairs": total / (n * n),
        "graph_distance_equals_hamming_distance": matches_hamming,
        "connected": all(d >= 0 for v in range(n) for d in bfs_distances(v)),
    }


def hamming_distance_distribution() -> dict:
    """Distribution of Hamming distance between two independent uniform hexagrams."""
    counts = [0] * (N_LINES + 1)
    for a in range(N_HEXAGRAMS):
        for b in range(N_HEXAGRAMS):
            counts[yang_count(a ^ b)] += 1
    total = N_HEXAGRAMS * N_HEXAGRAMS
    probs = [c / total for c in counts]
    mean = sum(k * p for k, p in enumerate(probs))
    var = sum((k - mean) ** 2 * p for k, p in enumerate(probs))
    return {
        "counts_per_source": [comb(N_LINES, k) for k in range(N_LINES + 1)],
        "probabilities": probs,
        "mean": mean,
        "variance": var,
    }


# --------------------------------------------------------------------------
# Clustering
# --------------------------------------------------------------------------

def triangle_count() -> int:
    adj = adjacency()
    triangles = 0
    for v in range(N_HEXAGRAMS):
        nb = sorted(adj[v])
        for idx, a in enumerate(nb):
            for b in nb[idx + 1:]:
                if b in adj[a]:
                    triangles += 1
    return triangles // 3


def clustering() -> dict:
    """Local and global clustering coefficients, computed from the graph.

    Q_6 is bipartite, so it contains no odd cycles and therefore no triangles.
    Both coefficients must come out at zero.
    """
    adj = adjacency()
    locals_ = []
    for v in range(N_HEXAGRAMS):
        nb = sorted(adj[v])
        k = len(nb)
        links = sum(
            1
            for idx, a in enumerate(nb)
            for b in nb[idx + 1:]
            if b in adj[a]
        )
        locals_.append(0.0 if k < 2 else 2 * links / (k * (k - 1)))
    triangles = triangle_count()
    open_triplets = sum(len(adj[v]) * (len(adj[v]) - 1) // 2 for v in adj)
    return {
        "average_local_clustering": sum(locals_) / len(locals_),
        "global_transitivity": 0.0 if open_triplets == 0 else 3 * triangles / open_triplets,
        "triangles": triangles,
        "connected_triples": open_triplets,
    }


def is_bipartite() -> dict:
    """Two-colour the graph; parity of Hamming weight is the natural colouring."""
    colour = {0: 0}
    queue = deque([0])
    ok = True
    while queue:
        v = queue.popleft()
        for u in neighbours(v):
            if u not in colour:
                colour[u] = 1 - colour[v]
                queue.append(u)
            elif colour[u] == colour[v]:
                ok = False
    parity_matches = all(colour[v] == (yang_count(v) % 2) for v in colour)
    part_sizes = [sum(1 for c in colour.values() if c == 0),
                  sum(1 for c in colour.values() if c == 1)]
    return {
        "bipartite": ok,
        "parts": part_sizes,
        "colouring_is_yang_parity": parity_matches,
    }


# --------------------------------------------------------------------------
# Spectrum
# --------------------------------------------------------------------------

def analytic_adjacency_spectrum() -> dict:
    """Q_n has eigenvalues n - 2k with multiplicity C(n, k)."""
    return {N_LINES - 2 * k: comb(N_LINES, k) for k in range(N_LINES + 1)}


def numeric_adjacency_spectrum(tol: float = 1e-9) -> dict:
    if _np is None:  # pragma: no cover
        raise RuntimeError("numpy required for numeric_adjacency_spectrum")
    matrix = _np.zeros((N_HEXAGRAMS, N_HEXAGRAMS))
    for v in range(N_HEXAGRAMS):
        for u in neighbours(v):
            matrix[v, u] = 1.0
    values = _np.linalg.eigvalsh(matrix)
    counts: dict = {}
    for lam in values:
        key = round(float(lam))
        if abs(float(lam) - key) > 1e-6:
            key = float(lam)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), reverse=True))
