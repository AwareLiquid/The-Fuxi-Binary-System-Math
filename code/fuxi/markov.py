"""Transition kernels on the 64 hexagram states.

Two kernels are built and compared.

``independent_mask``
    The kernel assumed in the original analysis: at each step a mutation mask
    is drawn with every line flipping independently with probability p = 1/4,
    regardless of that line's current value. Formally

        P(i -> j) = p^w(i XOR j) * (1-p)^(6 - w(i XOR j)).

``yarrow``
    The kernel actually induced by the divination procedure. There the four
    line states carry the joint distribution of (cast value, transformed
    value), so the flip probability is conditional on the current line:

        P(change | yang) = P(9) / P(yang)
        P(change | yin ) = P(6) / P(yin)

    These are not equal, so the kernel is not a function of i XOR j alone.

The two kernels agree on the marginal flip rate but differ in symmetry and in
stationary distribution.
"""

from __future__ import annotations

from fractions import Fraction

from .encoding import N_HEXAGRAMS, N_LINES, yang_count

try:  # numpy is optional; analytic results do not need it
    import numpy as _np
except ImportError:  # pragma: no cover
    _np = None


# --------------------------------------------------------------------------
# Kernel construction
# --------------------------------------------------------------------------

def independent_mask_kernel(p_change=Fraction(1, 4)) -> list:
    """64x64 kernel with per-line flip probability p, independent of the state."""
    p = Fraction(p_change)
    q = 1 - p
    kernel = []
    for i in range(N_HEXAGRAMS):
        row = []
        for j in range(N_HEXAGRAMS):
            w = yang_count(i ^ j)
            row.append(p ** w * q ** (N_LINES - w))
        kernel.append(row)
    return kernel


def yarrow_kernel(p_change_given_yin, p_change_given_yang) -> list:
    """64x64 kernel with state-dependent per-line flip probabilities."""
    q = {0: Fraction(p_change_given_yin), 1: Fraction(p_change_given_yang)}
    kernel = []
    for i in range(N_HEXAGRAMS):
        row = []
        for j in range(N_HEXAGRAMS):
            prob = Fraction(1)
            for k in range(N_LINES):
                b = (i >> k) & 1
                c = (j >> k) & 1
                prob *= q[b] if b != c else 1 - q[b]
            row.append(prob)
        kernel.append(row)
    return kernel


# --------------------------------------------------------------------------
# Structural properties
# --------------------------------------------------------------------------

def is_stochastic(kernel) -> bool:
    return all(sum(row) == 1 for row in kernel)


def is_symmetric(kernel) -> bool:
    n = len(kernel)
    return all(kernel[i][j] == kernel[j][i] for i in range(n) for j in range(n))


def is_irreducible(kernel) -> bool:
    """Every entry strictly positive implies irreducibility in one step."""
    return all(x > 0 for row in kernel for x in row)


def is_aperiodic(kernel) -> bool:
    """A positive diagonal entry gives period 1."""
    return all(kernel[i][i] > 0 for i in range(len(kernel)))


def stationary_by_power_iteration(kernel, iterations: int = 400) -> list:
    """Numerically iterate a uniform start to the stationary distribution."""
    n = len(kernel)
    dist = [1.0 / n] * n
    kf = [[float(x) for x in row] for row in kernel]
    for _ in range(iterations):
        nxt = [0.0] * n
        for i, pi in enumerate(dist):
            if pi == 0.0:
                continue
            row = kf[i]
            for j in range(n):
                nxt[j] += pi * row[j]
        dist = nxt
    return dist


def stationary_product_form(p_change_given_yin, p_change_given_yang) -> list:
    """Exact stationary distribution of the state-dependent kernel.

    The six lines evolve independently, so the stationary distribution is a
    product of per-line stationary distributions. For a two-state chain with
    flip probabilities q_yin (0 -> 1) and q_yang (1 -> 0), detailed balance
    gives pi(yin) = q_yang / (q_yin + q_yang).
    """
    q0 = Fraction(p_change_given_yin)
    q1 = Fraction(p_change_given_yang)
    pi_yin = q1 / (q0 + q1)
    pi_yang = q0 / (q0 + q1)
    return [
        pi_yang ** yang_count(v) * pi_yin ** (N_LINES - yang_count(v))
        for v in range(N_HEXAGRAMS)
    ]


def check_stationary(kernel, dist) -> bool:
    """Verify dist * kernel == dist exactly."""
    n = len(kernel)
    for j in range(n):
        total = sum(dist[i] * kernel[i][j] for i in range(n))
        if total != dist[j]:
            return False
    return True


# --------------------------------------------------------------------------
# Spectrum
# --------------------------------------------------------------------------

def analytic_eigenvalues(second_eigenvalue) -> dict:
    """Eigenvalues of a six-fold tensor power of a two-state kernel.

    Each per-line kernel has eigenvalues {1, lambda2}. The full kernel is their
    tensor product, so its eigenvalues are lambda2^k with multiplicity C(6, k).
    """
    from math import comb

    lam = Fraction(second_eigenvalue)
    return {lam ** k: comb(N_LINES, k) for k in range(N_LINES + 1)}


def numeric_eigenvalues(kernel) -> list:
    """Eigenvalues via numpy, sorted by decreasing modulus."""
    if _np is None:  # pragma: no cover
        raise RuntimeError("numpy required for numeric_eigenvalues")
    matrix = _np.array([[float(x) for x in row] for row in kernel])
    values = _np.linalg.eigvals(matrix)
    return sorted(values.real.tolist(), key=lambda x: -abs(x))


def spectral_gap(kernel) -> float:
    values = numeric_eigenvalues(kernel)
    moduli = sorted((abs(v) for v in values), reverse=True)
    return moduli[0] - moduli[1]


# --------------------------------------------------------------------------
# Mixing
# --------------------------------------------------------------------------

def total_variation(a, b) -> float:
    return 0.5 * sum(abs(float(x) - float(y)) for x, y in zip(a, b))


def mixing_time(kernel, stationary, epsilon: float = 0.01, max_steps: int = 200) -> int:
    """Worst-case steps until total-variation distance drops below epsilon."""
    n = len(kernel)
    kf = [[float(x) for x in row] for row in kernel]
    pi = [float(x) for x in stationary]
    worst = 0
    for start in range(n):
        dist = [0.0] * n
        dist[start] = 1.0
        for t in range(1, max_steps + 1):
            nxt = [0.0] * n
            for i, p in enumerate(dist):
                if p == 0.0:
                    continue
                row = kf[i]
                for j in range(n):
                    nxt[j] += p * row[j]
            dist = nxt
            if total_variation(dist, pi) < epsilon:
                worst = max(worst, t)
                break
        else:  # pragma: no cover
            return -1
    return worst
