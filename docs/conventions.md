# Conventions and terminology

One name for one thing. This file is the single source of truth for the
manuscript and the code. If a term changes here, it changes everywhere.

## Encoding

| Decision | Value | Where it is enforced |
|---|---|---|
| Bit order | Bottom line is the **least significant** bit | `encoding.lines_to_value` |
| Line values | yang = **1**, yin = **0** | `encoding.YANG`, `encoding.YIN` |
| Storage order | Tuples are **bottom-first**: `lines[0]` is the bottom line | all of `fuxi` |
| Anchor points | Kun (all yin) = **0**, Qian (all yang) = **63** | `encoding.KUN`, `encoding.QIAN` |

$$V(h) = \sum_{i=1}^{6} b_i \, 2^{\,i-1}, \qquad b_1 = \text{bottom line}$$

This convention is a choice, and the opposite one appears in the literature.
Leibniz assigned the highest weight to the bottom line. Nothing in the algebraic,
topological, or probabilistic results depends on the choice, because those are
properties of the set and its structure rather than of the labelling. The one
place the choice is visible is the enumeration order, which is why
`encoding.doubling_values` supports both placements and the manuscript reports
both.

## Terminology

| Canonical term | Definition | Rejected variants |
|---|---|---|
| **hexagram** | a six-line figure; one of 64 | gua, kua, figure |
| **trigram** | a three-line figure; one of 8 | bagua element |
| **line** | one of the six positions in a hexagram | yao, stroke |
| **yang line** / **yin line** | the two line values, encoded 1 and 0 | solid/broken, unbroken/broken |
| **changing line** | a line in an "old" state, which flips | moving line, old line |
| **cast hexagram** | the hexagram as first produced | primary, original, ben gua |
| **transformed hexagram** | the hexagram after changing lines flip | derived, resulting, zhi gua |
| **mutation mask** | the six-bit vector marking changing lines | change vector |
| **doubling method** | the recursive bifurcating generation | jia yi bei fa, add-one-doubling |
| **yarrow-stalk procedure** | the three-operation method on 49 stalks | da yan shi fa, milfoil method |
| **Earlier Heaven arrangement** | the ordering analysed here | Fuxi arrangement, xiantian, Former Heaven |

Line states keep their traditional numbers throughout: **6** old yin, **7** young
yang, **8** young yin, **9** old yang. These numbers are used as identifiers, not
as quantities.

## Notation

| Symbol | Meaning |
|---|---|
| $B$, $B'$ | cast hexagram, transformed hexagram |
| $M$ | mutation mask |
| $\oplus$ | bitwise exclusive-or |
| $w(\cdot)$ | Hamming weight |
| $y(h)$ | number of yang lines of $h$ |
| $\mathbb{Z}_2^6$ | the elementary abelian group of order 64 |
| $Q_6$ | the six-dimensional hypercube graph |
| $P^{A}$ | the independent-mask kernel |
| $P^{B}$ | the yarrow-induced kernel |
| $\pi$ | a stationary distribution |
| $H$, $H_b$, $I$ | entropy, binary entropy, mutual information |

Entropies are in **bits** throughout. Never nats.

## Two groups, kept apart

Two distinct groups act on the 64 hexagrams, and conflating them causes trouble.

- **Flipping line values** gives $\mathbb{Z}_2^6$, order 64. The changing-line
  mechanism lives here, and only here.
- **Permuting line positions** gives $S_6$, order 720.

Together they generate the hyperoctahedral group of order $2^6 \cdot 6! = 46{,}080$,
in which $\mathbb{Z}_2^6$ is normal. Earlier algebraic treatments of the system
work with the permutation action; this work is about the flip action.

## Two kernels, kept apart

- $P^{A}$, the **independent-mask kernel**: every line flips with probability
  $1/4$ regardless of its value. Symmetric, uniform stationary distribution.
- $P^{B}$, the **yarrow-induced kernel**: a yang line flips with probability
  $3/8$, a yin line with probability $1/8$. Asymmetric, product-form stationary
  distribution with a 729:1 spread.

They agree on the marginal flip rate of $1/4$ and disagree on almost everything
else. Any statement about "the" transition kernel must say which one.

## Claim tiers

The manuscript sorts every claim into one of three tiers and matches its verbs
to the tier.

| Tier | Basis | Licensed verbs |
|---|---|---|
| **Proved** | formal proof from stated definitions | prove, establish |
| **Machine-verified** | exhaustive enumeration or exact arithmetic | verify, confirm, show |
| **Estimated** | Monte Carlo, or dependent on a modelling assumption | suggest, indicate, estimate |

Statements about historical intent, meaning, or significance belong to none of
these tiers and are not made.
