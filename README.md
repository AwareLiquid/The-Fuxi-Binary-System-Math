# The Fuxi Binary System

A machine-checked formalization of the Fuxi Earlier Heaven arrangement of the
sixty-four hexagrams, together with a verification suite that executes every
quantitative claim the formalization makes.

The short version: the system is a six-bit finite state machine whose transition
structure is the elementary abelian group $\mathbb{Z}_2^6$. That much is already
known. What has not been done is running it. When you do, three claims in the
received account turn out to be wrong, and one of them propagates.

## What this repository contains

| Path | Contents |
|---|---|
| `paper/main.tex` | The manuscript |
| `paper/figures/` | Generated figures (PDF and PNG) |
| `code/fuxi/` | The formalization, seven modules, standard library only |
| `code/verify_all.py` | The verification driver: 40 checks, one command |
| `code/tests/` | pytest suite |
| `code/figures/make_figures.py` | Regenerates every figure from the model |
| `paper/refs.bib` | Bibliography, metadata audited (see below) |
| `results/` | Generated verification report |
| `docs/conventions.md` | Encoding, terminology, notation |
| `docs/reference-audit.md` | Citation audit: 9 verified, 12 corrected, 1 non-existent |

## Running it

Python 3.10 or later. The formalization itself needs nothing beyond the standard
library. NumPy is used only for the numerical eigendecompositions that
cross-check the analytic spectra, and matplotlib only for figures.

```bash
cd code
python verify_all.py                                  # console report
python verify_all.py --markdown ../results/verification_report.md
python -m pytest tests -q                             # test suite
python figures/make_figures.py                        # regenerate figures
```

Rational quantities are computed with `fractions.Fraction` and compared for
exact equality, not within a tolerance. Wherever a property is finite enough to
enumerate, the suite enumerates it rather than sampling: the exclusive-or
equivalence is checked on all 4096 line-state assignments, commutativity on all
262,144 triples, and the graph invariants on the whole graph.

## Results

Forty checks: **24 confirmed, 5 refined, 7 corrected, 4 new**.

Each check carries one of four verdicts. *Confirmed* means the computed value
matches the received one. *Refined* means the received value holds under an
idealization that the check then makes explicit. *Corrected* means the computed
value contradicts the received one. *New* means the quantity was not previously
reported.

### The three corrections that matter

**1. The clustering coefficient is zero, not 5/12.**

The state-transition graph is the six-dimensional hypercube, which is bipartite:
the two parts are the hexagrams with an even and an odd number of yang lines, 32
each. A bipartite graph has no odd cycles and therefore no triangles. Direct
enumeration over 960 connected triples finds zero closed ones. Two neighbours of
a hexagram each differ from it in one line, so they differ from each other in
two lines and are never adjacent. No value in $(0,1]$ can be correct.

**2. The yarrow-stalk mutation mask is not independent of the state.**

This is the one that propagates. Reading the four traditional line states as the
*joint* distribution of (cast bit, transformed bit) rather than as a marginal
makes the conditionals visible:

| | transformed yin | transformed yang |
|---|---|---|
| **cast yin** | 7/16 (young yin, 8) | 1/16 (old yin, 6) |
| **cast yang** | 3/16 (old yang, 9) | 5/16 (young yang, 7) |

So `P(change | yang) = 3/8` but `P(change | yin) = 1/8`. A yang line changes
three times as often as a yin line. The marginal change rate is still exactly
1/4, which is why the dependence is easy to miss and why the received analysis
could assume independence without an obvious inconsistency.

The consequences:

- The induced transition kernel is **not symmetric**.
- Its stationary distribution is **not uniform**. It is the product form
  $\pi(h) \propto (3/4)^{\text{yin}} (1/4)^{\text{yang}}$, which places
  $729/4096$ of the mass on all-yin Kun and $1/4096$ on all-yang Qian, a ratio
  of **729 to 1**. The chain drifts toward yin.
- The mutual information between cast and transformed hexagram is **1.233 bits**,
  not 1.132.
- The transformed hexagram carries **5.727 bits**, not 6, because it is
  yin-biased.

The spectral gap survives at 1/2 for both kernels, so the mixing rate is
unaffected.

**3. The genetic-code dichotomies are dependent over GF(2).**

Purine/pyrimidine, amino/keto and strong/weak are usually presented as three
independent binary dimensions per nucleotide, which across three codon positions
would give nine degrees of freedom and $2^9 = 512$ codons. Gaussian elimination
over GF(2) returns rank 2. The dependency is exact and checkable by hand: the
strong/weak bit is the XOR of the other two, for all four nucleotides.

| | purine | amino | strong | XOR of first two |
|---|---|---|---|---|
| A | 1 | 1 | 0 | 0 ✓ |
| C | 0 | 1 | 1 | 1 ✓ |
| G | 1 | 0 | 1 | 1 ✓ |
| U | 0 | 0 | 0 | 0 ✓ |

Two free bits per nucleotide, six per codon, $2^6 = 64$. Same answer, consistent
route.

### Confirmed

The doubling generation gives $2^n$ symbols and the full set of six-bit strings,
under *both* conventions for where the new line is placed. Changing lines are
bitwise XOR, on all 4096 assignments. The transition structure satisfies
commutativity, self-inversion, and one-step reachability. The graph has 64
vertices, 192 edges, degree 6, diameter 6, and adjacency spectrum $6-2k$ with
multiplicity $\binom{6}{k}$. The yarrow procedure gives line-state probabilities
of exactly 1/16, 5/16, 7/16, 3/16, a marginal change rate of exactly 1/4, and an
expected 3/2 changing lines. The cast hexagram is exactly uniform over the 64
states. Hexagram entropy is 6 bits.

### Refined

The received "average shortest-path length of 3" is the mean Hamming distance
between two independent uniform hexagrams. The standard average shortest-path
length excludes self-pairs and is $192/63 \approx 3.048$. Both are reported.

The line-state probabilities assume the left-heap size is uniform modulo four.
That holds exactly at the first of the three operations and fails at the second
and third. Under a uniform-split model the probabilities move by at most 0.013,
and the state dependence in correction 2 survives either way.

### New

The full symmetry group, allowing line positions to permute as well as flip, has
order $2^6 \cdot 6! = 46{,}080$: the hyperoctahedral group. The changing-line
mechanism lives entirely in the normal $\mathbb{Z}_2^6$ subgroup.

## The citations were checked too

The same discipline was applied to the bibliography. Twenty-two references were
each resolved to a publisher page, DOI record, or authoritative index — not to a
matching entry in a citation aggregator, since that is how a copying error
spreads.

**9 verified, 12 corrected, 1 does not exist.**

The non-existent one was attributed to *Studies of Zhouyi* 2006(3): 62–67. That
issue's full table of contents has fourteen articles, none on divination
probability, none by an author surnamed Ke, nothing at those pages. The supplied
English title turns out to be a close translation of a real article in a
different journal by a different author, which is cited in its place.

Worth knowing if you cite Maitre: the paper is *Science in Context* **36(1),
2023, 38–59**. It appeared online first in August 2025 and its DOI string
contains `725`, so "2025" is an easy and wrong inference.

Details in [`docs/reference-audit.md`](docs/reference-audit.md).

## Scope

The formalized system has 64 states. Nothing here supports the claim that the
arrangement anticipated binary computation, the genetic code, or any model of
discrete physics. Powers of two recur across unrelated systems because iterated
binary splitting produces them, not because the systems are related. The
bijection between hexagrams and codons is a statement about two sets of size 64;
a bijection between two finite sets of equal size always exists.

Nothing here bears on the divinatory or interpretive tradition. The probability
model describes how line states are produced, not what they are taken to mean.

The formalization covers the Earlier Heaven arrangement and the three-operation
yarrow procedure on 49 stalks. It does not cover the King Wen sequence, the coin
method, or the commentarial apparatus.

## License

MIT for the code. See `LICENSE`.
