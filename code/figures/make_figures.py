#!/usr/bin/env python3
"""Publication figures for the Fuxi binary-system paper.

Every numeric quantity drawn here is computed at run time by calling the
``fuxi`` package. Nothing is hard-coded except axis text and captions.

Usage
-----
    py code/figures/make_figures.py                     # all seven figures
    py code/figures/make_figures.py --only fig4         # just one
    py code/figures/make_figures.py --outdir /some/dir

Each figure is written twice: a vector ``.pdf`` for the manuscript and a
300-dpi ``.png`` for review and slides.
"""

from __future__ import annotations

import argparse
import os
import sys
from fractions import Fraction

import matplotlib

matplotlib.use("Agg")  # non-interactive; must precede pyplot

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

# --------------------------------------------------------------------------
# Make ``import fuxi`` work no matter what the current working directory is:
# this file lives at <repo>/code/figures/, the package at <repo>/code/fuxi/.
# --------------------------------------------------------------------------
_CODE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from fuxi import (  # noqa: E402
    encoding, information, king_wen, markov, orderings, topology, yarrow,
)

DEFAULT_OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "paper", "figures")


# ==========================================================================
# Shared style
# ==========================================================================
#
# Two-hue categorical palette (blue / orange), validated for colour-vision
# deficiency and for >= 3:1 contrast against a white page. A third slot
# (violet) is used only where three series are unavoidable. Because the paper
# may be printed in greyscale, colour NEVER carries meaning alone: every
# comparison is also encoded by hatch (bars), dash pattern + marker shape
# (lines), or marker shape (scatter).

INK          = "#0b0b0b"   # primary text
INK_2        = "#52514e"   # secondary text
INK_MUTED    = "#898781"   # axis / tick labels
GRID         = "#e1e0d9"   # hairline gridlines
AXIS         = "#c3c2b7"   # spines, baselines
SURFACE      = "#ffffff"   # page

S1 = "#2a78d6"   # series 1 — blue    (the model as published / even parity)
S2 = "#eb6834"   # series 2 — orange  (the yarrow-exact correction / odd parity)
S3 = "#4a3aa7"   # series 3 — violet  (Monte-Carlo check)

HATCH_1 = ""       # series 1: solid fill
HATCH_2 = "////"   # series 2
HATCH_3 = "...."   # series 3

# A single-hue sequential ramp, used only where the classes are *ordered* (the
# Hamming distance d = 1..6 of figure 7). Lightness falls monotonically, so the
# six classes stay separable in greyscale print; a surface-coloured edge keeps
# neighbouring segments apart as well. Never used for nominal categories.
D_RAMP = ("#dbe7f6", "#adc9e9", "#7ba7da", "#4c85c8", "#2a5f9e", "#193f68")

NEUTRAL = "#bdbcb3"   # a null / reference series, deliberately not a named hue

FS_TITLE  = 10.5
FS_SUB    = 8.5
FS_LABEL  = 9.0
FS_TICK   = 8.0
FS_ANNOT  = 7.6
FS_VALUE  = 6.8


def apply_style() -> None:
    """Install the shared rcParams. Called once from :func:`main`."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans"],
        "mathtext.fontset": "dejavusans",
        "font.size": FS_TICK,
        "figure.facecolor": SURFACE,
        "figure.dpi": 110,
        "savefig.facecolor": SURFACE,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.06,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": AXIS,
        "axes.linewidth": 0.8,
        "axes.labelcolor": INK_2,
        "axes.labelsize": FS_LABEL,
        "axes.titlesize": FS_TITLE,
        "axes.titlecolor": INK,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.titlepad": 8.0,
        "axes.grid": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "xtick.color": INK_MUTED,
        "ytick.color": INK_MUTED,
        "xtick.labelcolor": INK_2,
        "ytick.labelcolor": INK_2,
        "xtick.labelsize": FS_TICK,
        "ytick.labelsize": FS_TICK,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.size": 3.0,
        "ytick.major.size": 3.0,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        "legend.frameon": False,
        "legend.fontsize": FS_ANNOT,
        "legend.labelcolor": INK_2,
        "legend.handlelength": 1.9,
        "legend.handleheight": 1.0,
        "legend.columnspacing": 1.4,
        "hatch.linewidth": 0.6,
        "pdf.fonttype": 42,   # embed TrueType, keep text selectable
        "ps.fonttype": 42,
    })


def titled(ax, title: str, subtitle: str | None = None) -> None:
    """A bold title with an optional recessive subtitle set clearly beneath it.

    Both are drawn as offset annotations rather than via ``set_title`` so the
    vertical gap between them is explicit and cannot close up on long titles.
    """
    if not subtitle:
        ax.set_title(title, loc="left")
        return
    ax.annotate(
        title, xy=(0.0, 1.0), xycoords="axes fraction",
        xytext=(0, 27), textcoords="offset points",
        ha="left", va="baseline", fontsize=FS_TITLE, fontweight="bold", color=INK,
    )
    ax.annotate(
        subtitle, xy=(0.0, 1.0), xycoords="axes fraction",
        xytext=(0, 10), textcoords="offset points",
        ha="left", va="baseline", fontsize=FS_SUB, color=INK_2,
    )


def ygrid(ax) -> None:
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=GRID, linewidth=0.6)


def xgrid(ax) -> None:
    ax.set_axisbelow(True)
    ax.grid(axis="x", color=GRID, linewidth=0.6)


def caption(fig, text: str) -> None:
    """A caption-worthy line of prose along the bottom of the figure."""
    fig.text(0.005, 0.005, text, ha="left", va="bottom",
             fontsize=FS_ANNOT, color=INK_2, wrap=True)


def save(fig, outdir: str, stem: str) -> list:
    os.makedirs(outdir, exist_ok=True)
    written = []
    for ext, kwargs in (("pdf", {}), ("png", {"dpi": 300})):
        path = os.path.join(outdir, f"{stem}.{ext}")
        fig.savefig(path, **kwargs)
        written.append(path)
    plt.close(fig)
    return written


# ==========================================================================
# Shared computations (cached — the exact-rational kernels are not cheap)
# ==========================================================================

_CACHE: dict = {}


def _yarrow_quantities() -> dict:
    if "q" not in _CACHE:
        dist = yarrow.line_state_distribution("idealized")
        _CACHE["q"] = yarrow.derived_quantities(dist)
    return _CACHE["q"]


def _kernels() -> dict:
    """Both 64x64 kernels plus their exact stationary distributions."""
    if "kernels" not in _CACHE:
        q = _yarrow_quantities()
        kernel_a = markov.independent_mask_kernel(Fraction(1, 4))
        pi_a = [Fraction(1, encoding.N_HEXAGRAMS)] * encoding.N_HEXAGRAMS
        kernel_b = markov.yarrow_kernel(q["p_change_given_yin"], q["p_change_given_yang"])
        pi_b = markov.stationary_product_form(
            q["p_change_given_yin"], q["p_change_given_yang"]
        )
        # Both claims are verified, not assumed.
        assert markov.check_stationary(kernel_a, pi_a), "uniform is not stationary for A"
        assert markov.check_stationary(kernel_b, pi_b), "product form is not stationary for B"
        _CACHE["kernels"] = {
            "A": kernel_a, "pi_A": pi_a,
            "B": kernel_b, "pi_B": pi_b,
        }
    return _CACHE["kernels"]


def _mass_by_yang_count(dist) -> list:
    """Aggregate a distribution over the 64 states into the seven rank classes."""
    agg = [Fraction(0)] * (encoding.N_LINES + 1)
    for value, p in enumerate(dist):
        agg[encoding.yang_count(value)] += Fraction(p)
    return agg


def _per_state_by_yang_count(dist) -> list:
    """Probability of a *single* state at each rank, checking it is well defined."""
    out = []
    for k in range(encoding.N_LINES + 1):
        vals = {Fraction(dist[v]) for v in range(encoding.N_HEXAGRAMS)
                if encoding.yang_count(v) == k}
        assert len(vals) == 1, f"rank {k} is not rank-symmetric: {vals}"
        out.append(vals.pop())
    return out


# ==========================================================================
# Figure 1 — the recursive doubling method
# ==========================================================================

def _draw_gram(ax, x, y, lines, width, dy, colour, lw=1.7):
    """Draw a yin/yang line stack (bottom-first tuple) centred at (x, y)."""
    n = len(lines)
    y0 = y - (n - 1) * dy / 2.0
    half = width / 2.0
    gap = width * 0.16
    for i, bit in enumerate(lines):
        yy = y0 + i * dy
        if bit == encoding.YANG:
            ax.plot([x - half, x + half], [yy, yy], color=colour, lw=lw,
                    solid_capstyle="butt", zorder=4)
        else:
            ax.plot([x - half, x - gap], [yy, yy], color=colour, lw=lw,
                    solid_capstyle="butt", zorder=4)
            ax.plot([x + gap, x + half], [yy, yy], color=colour, lw=lw,
                    solid_capstyle="butt", zorder=4)


def fig1_doubling(outdir: str) -> list:
    """Shao Yong's doubling method as a binary tree, 1 symbol -> 64 hexagrams."""
    n_levels = encoding.N_LINES  # 6

    # Every level is generated by the package; the counts are len(), not 2**n.
    levels = [encoding.doubling_bottom(n) for n in range(n_levels + 1)]
    counts = [len(g) for g in levels]
    # Independent ground truth for the same counts.
    brute = [len(encoding.brute_force_enumeration(n)) for n in range(n_levels + 1)]
    assert counts == brute, "doubling method disagrees with brute-force enumeration"

    fig, ax = plt.subplots(figsize=(7.4, 5.9))

    def xs(n):
        m = counts[n]
        return [(i + 0.5) / m for i in range(m)]

    GLYPH_LEVELS = {1, 2, 3}
    DY = 0.115
    GLYPH_W = {1: 0.130, 2: 0.108, 3: 0.076}

    def pad(n):
        if n in GLYPH_LEVELS:
            return (len(levels[n][0]) - 1) * DY / 2.0 + 0.085
        return 0.055

    # ---- edges -----------------------------------------------------------
    for n in range(n_levels):
        px, cx = xs(n), xs(n + 1)
        for i in range(counts[n]):
            for child in (2 * i, 2 * i + 1):
                ax.plot(
                    [px[i], cx[child]],
                    [-n - pad(n), -(n + 1) + pad(n + 1)],
                    color=AXIS, lw=0.65, zorder=1, solid_capstyle="round",
                )

    # ---- nodes -----------------------------------------------------------
    for n in range(n_levels + 1):
        x = xs(n)
        if n in GLYPH_LEVELS:
            for i, gram in enumerate(levels[n]):
                _draw_gram(ax, x[i], -n, gram, GLYPH_W[n], DY, INK,
                           lw=2.0 if n < 3 else 1.5)
        else:
            size = {0: 46, 4: 20, 5: 12, 6: 7}[n]
            ax.scatter(x, [-n] * len(x), s=size, color=INK, zorder=4,
                       edgecolors="none")

    # ---- level rail: n on the left, 2**n on the right --------------------
    for n in range(n_levels + 1):
        emphasis = n in (3, n_levels)
        ax.text(-0.055, -n, f"n = {n}", ha="right", va="center",
                fontsize=FS_TICK, color=INK if emphasis else INK_2,
                fontweight="bold" if emphasis else "normal")
        ax.text(1.045, -n, f"$2^{{{n}}}$ = {counts[n]}", ha="left", va="center",
                fontsize=FS_TICK, color=INK if emphasis else INK_2,
                fontweight="bold" if emphasis else "normal")

    # ---- the two milestone annotations -----------------------------------
    milestones = ((3, f"{counts[3]} trigrams (bagua)"),
                  (n_levels, f"{counts[n_levels]} hexagrams"))
    for n, label in milestones:
        ax.plot([1.185, 1.245], [-n, -n], color=S1, lw=1.4, zorder=3)
        ax.text(1.262, -n, label, ha="left", va="center",
                fontsize=FS_ANNOT, color=S1, fontweight="bold")

    ax.text(0.5, 0.40,
            "each step splits every symbol in two by adding one line "
            "beneath it: $|G(n)| = 2\\,|G(n-1)|$",
            ha="center", va="center", fontsize=FS_ANNOT, color=INK_2)

    ax.set_xlim(-0.17, 1.56)
    ax.set_ylim(-n_levels - 0.40, 0.58)
    ax.axis("off")

    titled(
        ax,
        "The doubling method generates all 64 hexagrams in six steps",
        "yang $=$ unbroken line, yin $=$ broken line; the new line is added at the bottom",
    )
    caption(fig,
            "Node counts are len(encoding.doubling_bottom(n)), cross-checked against "
            "encoding.brute_force_enumeration(n).")
    fig.subplots_adjust(top=0.90, bottom=0.05, left=0.02, right=0.99)
    return save(fig, outdir, "fig1_doubling")


# ==========================================================================
# Figure 2 — the state-transition graph Q6
# ==========================================================================

def fig2_hypercube(outdir: str) -> list:
    """Q6 laid out in seven Hamming-weight columns; bipartite, triangle-free."""
    counts = topology.basic_counts()
    bipart = topology.is_bipartite()
    clust = topology.clustering()
    ranks = encoding.rank_distribution()
    n_tri = topology.triangle_count()

    # ---- layered layout: column k holds the C(6,k) states of weight k ----
    columns = [[v for v in range(encoding.N_HEXAGRAMS) if encoding.yang_count(v) == k]
               for k in range(encoding.N_LINES + 1)]
    assert [len(c) for c in columns] == ranks

    widest = max(len(c) for c in columns)
    pos = {}
    for k, col in enumerate(columns):
        m = len(col)
        for i, v in enumerate(sorted(col)):
            y = 0.0 if m == 1 else (i - (m - 1) / 2.0) * (2.0 / (widest - 1))
            pos[v] = (float(k), y)

    fig, ax = plt.subplots(figsize=(7.4, 5.2))

    # ---- edges (192 of them) --------------------------------------------
    for edge in topology.edge_set():
        u, v = sorted(edge)
        (x1, y1), (x2, y2) = pos[u], pos[v]
        ax.plot([x1, x2], [y1, y2], color=INK_MUTED, lw=0.45, alpha=0.32, zorder=1)

    # ---- vertices, marked by parity of the yang count --------------------
    even = [v for v in range(encoding.N_HEXAGRAMS) if encoding.yang_count(v) % 2 == 0]
    odd = [v for v in range(encoding.N_HEXAGRAMS) if encoding.yang_count(v) % 2 == 1]
    assert [len(even), len(odd)] == bipart["parts"]

    ax.scatter([pos[v][0] for v in even], [pos[v][1] for v in even],
               s=46, marker="o", facecolor=S1, edgecolor=SURFACE, linewidth=0.9,
               zorder=3, label=f"even yang count — class A ({len(even)} states)")
    ax.scatter([pos[v][0] for v in odd], [pos[v][1] for v in odd],
               s=46, marker="s", facecolor=S2, edgecolor=SURFACE, linewidth=0.9,
               zorder=3, label=f"odd yang count — class B ({len(odd)} states)")

    # ---- column headers ---------------------------------------------------
    top = 1.28
    for k, col in enumerate(columns):
        m = len(col)
        ax.text(k, top, str(k), ha="center", va="bottom",
                fontsize=FS_TICK, color=INK_2, fontweight="bold")
        ax.text(k, top - 0.115, f"{m} state" + ("s" if m != 1 else ""),
                ha="center", va="top", fontsize=FS_VALUE, color=INK_MUTED)

    ax.text(3.0, top + 0.30, "number of yang lines  (Hamming weight)",
            ha="center", va="bottom", fontsize=FS_LABEL, color=INK_2)

    # ---- Kun / Qian ------------------------------------------------------
    ax.annotate("Kun\n$V = 0$", xy=pos[encoding.KUN], xytext=(-0.62, -0.30),
                ha="center", va="top", fontsize=FS_ANNOT, color=INK_2,
                arrowprops=dict(arrowstyle="-", color=INK_MUTED, lw=0.7,
                                shrinkA=2, shrinkB=4))
    ax.annotate("Qian\n$V = 63$", xy=pos[encoding.QIAN], xytext=(6.62, -0.30),
                ha="center", va="top", fontsize=FS_ANNOT, color=INK_2,
                arrowprops=dict(arrowstyle="-", color=INK_MUTED, lw=0.7,
                                shrinkA=2, shrinkB=4))

    # ---- the headline fact ------------------------------------------------
    ax.text(
        3.0, -1.95,
        f"Every edge flips exactly one line, so it always joins the two classes: "
        f"{n_tri} triangles; bipartite, parts {bipart['parts'][0]} + {bipart['parts'][1]}.",
        ha="center", va="top", fontsize=FS_ANNOT, color=INK,
        bbox=dict(boxstyle="round,pad=0.45", facecolor="#f4f7fd",
                  edgecolor=S1, linewidth=0.9),
    )
    ax.text(
        3.0, -2.44,
        f"clustering coefficient = {clust['average_local_clustering']:.1f} "
        f"(local) and {clust['global_transitivity']:.1f} (global) over "
        f"{clust['connected_triples']} connected triples",
        ha="center", va="top", fontsize=FS_VALUE, color=INK_MUTED,
    )

    ax.set_xlim(-1.05, 7.05)
    ax.set_ylim(-2.78, 1.82)
    ax.axis("off")
    # Legend sits in the clear band between the graph body and the callout.
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 0.315), ncol=2,
              handletextpad=0.5)

    titled(
        ax,
        f"State-transition graph $Q_6$: {counts['n_vertices']} hexagrams, "
        f"{counts['n_edges']} edges, {counts['degree']}-regular",
        "vertices laid out in columns by yang count; a one-line change moves one column left or right",
    )
    fig.subplots_adjust(top=0.86, bottom=0.02, left=0.02, right=0.98)
    return save(fig, outdir, "fig2_hypercube")


# ==========================================================================
# Figure 3 — line-state probabilities under three models
# ==========================================================================

MC_TRIALS = 200_000
MC_SEED = 20260722


def fig3_line_states(outdir: str) -> list:
    """The four traditional line states under three probability models."""
    idealized = yarrow.line_state_distribution("idealized")
    exact = yarrow.line_state_distribution("exact")
    mc = yarrow.monte_carlo_line_states(trials=MC_TRIALS, seed=MC_SEED,
                                        mode="uniform_split")

    # The textbook constants in the module must be exactly what the recursion
    # returns; assert rather than trust.
    assert idealized == yarrow.IDEALIZED_LINE_PROBABILITIES

    states = [yarrow.OLD_YIN, yarrow.YOUNG_YANG, yarrow.YOUNG_YIN, yarrow.OLD_YANG]
    descriptions = ["old yin\n(yin $\\rightarrow$ yang)",
                    "young yang\n(stable)",
                    "young yin\n(stable)",
                    "old yang\n(yang $\\rightarrow$ yin)"]
    # The exact textbook rational is folded into the tick label rather than
    # floated as a separate text layer, which used to collide with the ticks.
    names = [
        f"{s}\n{d}\ntextbook ${idealized[s].numerator}/{idealized[s].denominator}$"
        for s, d in zip(states, descriptions)
    ]

    series = [
        ("Idealized (textbook exact rationals)", [idealized[s] for s in states],
         S1, HATCH_1),
        ("Exact uniform-split model", [exact[s] for s in states], S2, HATCH_2),
        (f"Monte Carlo, {MC_TRIALS:,} trials (seed {MC_SEED})",
         [Fraction(mc[s]).limit_denominator(10 ** 9) for s in states], S3, HATCH_3),
    ]

    fig, ax = plt.subplots(figsize=(7.3, 4.7))
    x = np.arange(len(states), dtype=float)
    width = 0.26

    for j, (label, vals, colour, hatch) in enumerate(series):
        offset = (j - 1) * width
        heights = [float(v) for v in vals]
        ax.bar(x + offset, heights, width * 0.90, label=label,
               color=colour, edgecolor=SURFACE, linewidth=1.2,
               hatch=hatch, zorder=3)
        for xi, h in zip(x + offset, heights):
            ax.text(xi, h + 0.008, f"{h:.4f}", ha="center", va="bottom",
                    rotation=90, fontsize=FS_VALUE, color=INK_2)

    # Quantify the sensitivity: the largest gap between the two exact models.
    gaps = [abs(float(exact[s]) - float(idealized[s])) for s in states]
    worst = int(np.argmax(gaps))
    ax.text(
        0.995, 0.985,
        "Split-model sensitivity: the exact uniform-split model departs from the\n"
        f"textbook values by at most {max(gaps):.4f} in absolute probability "
        f"(state {states[worst]}),\nor {100 * max(gaps) / float(idealized[states[worst]]):.1f}% "
        "in relative terms. The Monte Carlo tracks the exact model.",
        transform=ax.transAxes, ha="right", va="top",
        fontsize=FS_ANNOT, color=INK,
        bbox=dict(boxstyle="round,pad=0.45", facecolor="#fdf3ef",
                  edgecolor=S2, linewidth=0.9),
    )

    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=FS_TICK)
    ax.tick_params(axis="x", length=0, pad=4)
    ax.set_ylabel("probability of the line state (dimensionless)")
    # Headroom so the rotated value labels clear the legend and the callout.
    ax.set_ylim(0, 0.76)
    ax.set_yticks(np.arange(0, 0.51, 0.1))
    ygrid(ax)
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, 0.995))

    titled(
        ax,
        "The textbook line-state probabilities are reproduced, but only under the "
        "uniformity assumption",
        "three models of one yarrow-stalk line: exact rationals, exact uniform split, and direct simulation",
    )
    fig.subplots_adjust(top=0.845, bottom=0.215, left=0.085, right=0.985)
    return save(fig, outdir, "fig3_line_states")


# ==========================================================================
# Figure 4 — stationary distributions of the two kernels
# ==========================================================================

def fig4_stationary(outdir: str) -> list:
    """The central correction: the yarrow kernel is not uniform-stationary."""
    ker = _kernels()
    q = _yarrow_quantities()

    per_state_a = _per_state_by_yang_count(ker["pi_A"])
    per_state_b = _per_state_by_yang_count(ker["pi_B"])
    mass_a = _mass_by_yang_count(ker["pi_A"])
    mass_b = _mass_by_yang_count(ker["pi_B"])

    ratio = ker["pi_B"][encoding.KUN] / ker["pi_B"][encoding.QIAN]
    pi_kun = ker["pi_B"][encoding.KUN]
    pi_qian = ker["pi_B"][encoding.QIAN]

    ks = np.arange(encoding.N_LINES + 1)

    fig, (axl, axr) = plt.subplots(1, 2, figsize=(7.6, 4.9))

    # ---- (left) probability of one individual hexagram -------------------
    axl.set_yscale("log")
    axl.plot(ks, [float(v) for v in per_state_a], color=S1, lw=2.0,
             marker="o", ms=6.5, ls="-", mec=SURFACE, mew=0.9, zorder=3,
             label="(a) independent mask — uniform, $1/64$")
    axl.plot(ks, [float(v) for v in per_state_b], color=S2, lw=2.0,
             marker="s", ms=6.0, ls="--", dashes=(4, 2.2), mec=SURFACE, mew=0.9,
             zorder=3, label="(b) yarrow-induced — product form")

    axl.annotate(
        "", xy=(0.0, float(pi_kun)), xytext=(0.0, float(pi_qian)),
        arrowprops=dict(arrowstyle="<->", color=INK, lw=1.1,
                        shrinkA=3, shrinkB=3),
    )
    # Parked low-left, in the wedge under both curves, so it touches no ink.
    axl.text(0.045, 0.135,
             f"$\\pi(\\mathrm{{Kun}})\\,/\\,\\pi(\\mathrm{{Qian}}) = {int(ratio)}$\n"
             f"(${pi_kun.numerator}/{pi_kun.denominator}$ vs "
             f"${pi_qian.numerator}/{pi_qian.denominator}$)",
             transform=axl.transAxes,
             ha="left", va="center", fontsize=FS_ANNOT, color=INK,
             bbox=dict(boxstyle="round,pad=0.4", facecolor="#fdf3ef",
                       edgecolor=S2, linewidth=0.9))

    axl.set_xlabel("number of yang lines in the hexagram")
    axl.set_ylabel("stationary probability of one hexagram (log scale)")
    axl.set_xticks(ks)
    axl.set_xlim(-0.45, 6.45)
    axl.set_ylim(1.4e-4, 0.62)
    axl.set_axisbelow(True)
    axl.grid(color=GRID, linewidth=0.6, which="major")
    axl.legend(loc="upper right", bbox_to_anchor=(1.015, 1.03))
    axl.set_title("(a)  per-hexagram mass", loc="left", fontsize=FS_LABEL)

    # ---- (right) total mass in each rank class ---------------------------
    width = 0.38
    axr.bar(ks - width / 2, [float(v) for v in mass_a], width * 0.92,
            color=S1, edgecolor=SURFACE, linewidth=1.2, hatch=HATCH_1,
            zorder=3, label="(a) independent-mask kernel")
    axr.bar(ks + width / 2, [float(v) for v in mass_b], width * 0.92,
            color=S2, edgecolor=SURFACE, linewidth=1.2, hatch=HATCH_2,
            zorder=3, label="(b) yarrow-induced kernel")

    def _fmt(v: float) -> str:
        """Keep three significant digits: 0.000244 must not print as '0.000'."""
        return f"{v:.3f}" if v >= 5e-4 else f"{v:.1e}"

    for k in ks:
        for off, vals in ((-width / 2, mass_a), (width / 2, mass_b)):
            v = float(vals[k])
            axr.text(k + off, v + 0.008, _fmt(v), ha="center", va="bottom",
                     rotation=90, fontsize=FS_VALUE, color=INK_2)

    axr.set_xlabel("number of yang lines in the hexagram")
    axr.set_ylabel("total stationary mass of the class")
    axr.set_xticks(ks)
    axr.set_xlim(-0.62, 6.62)
    axr.set_ylim(0, 0.62)
    axr.set_yticks(np.arange(0, 0.41, 0.1))
    ygrid(axr)
    axr.legend(loc="upper right", bbox_to_anchor=(1.015, 1.03))
    axr.set_title("(b)  mass aggregated by class", loc="left", fontsize=FS_LABEL)

    fig.text(0.006, 0.985,
             "The yarrow procedure does not leave the uniform distribution invariant",
             ha="left", va="top", fontsize=FS_TITLE, fontweight="bold", color=INK)
    fig.text(0.006, 0.938,
             "(a) is flat by construction; (b) is the exact product form, verified "
             "against the 64$\\times$64 kernel in exact rational arithmetic",
             ha="left", va="top", fontsize=FS_SUB, color=INK_2)
    # Formerly an in-axes callout on panel (b), where it ran through the k = 2
    # and k = 3 value labels; demoted to a footnote line instead.
    fig.text(0.006, 0.028,
             "The chain drifts toward yin because a yang line changes three times "
             "as readily as a yin line: "
             f"$P(\\mathrm{{change}}\\mid\\mathrm{{yang}}) = "
             f"{q['p_change_given_yang'].numerator}/{q['p_change_given_yang'].denominator}$ "
             f"but $P(\\mathrm{{change}}\\mid\\mathrm{{yin}}) = "
             f"{q['p_change_given_yin'].numerator}/{q['p_change_given_yin'].denominator}$.",
             ha="left", va="bottom", fontsize=FS_ANNOT, color=INK_2)

    fig.subplots_adjust(top=0.815, bottom=0.185, left=0.088, right=0.985, wspace=0.30)
    return save(fig, outdir, "fig4_stationary")


# ==========================================================================
# Figure 5 — convergence to stationarity
# ==========================================================================

MIX_EPS = 0.01
MIX_STEPS = 15


def _tv_trajectory(kernel, stationary, start, n_steps):
    """TV distance to stationarity after 0, 1, ..., n_steps steps."""
    mat = np.array([[float(x) for x in row] for row in kernel])
    pi = [float(x) for x in stationary]
    dist = np.zeros(len(pi))
    dist[start] = 1.0
    out = [markov.total_variation(dist, pi)]
    for _ in range(n_steps):
        dist = dist @ mat
        out.append(markov.total_variation(dist, pi))
    return out


def _worst_start(kernel, stationary, eps, n_steps):
    """The initial state whose TV distance is the last to fall below eps."""
    mat = np.array([[float(x) for x in row] for row in kernel])
    pi = np.array([float(x) for x in stationary])
    dists = np.eye(len(pi))
    crossing = np.full(len(pi), n_steps + 1)
    residual = np.zeros(len(pi))
    for t in range(1, n_steps + 1):
        dists = dists @ mat
        tv = 0.5 * np.abs(dists - pi).sum(axis=1)
        fresh = (crossing > n_steps) & (tv < eps)
        crossing[fresh] = t
        residual[fresh] = tv[fresh]
    # latest crossing wins; ties broken by the larger residual at that step
    order = np.lexsort((residual, crossing))
    return int(order[-1]), int(crossing[order[-1]])


def fig5_mixing(outdir: str) -> list:
    """Total-variation decay for both kernels from the worst-case start."""
    ker = _kernels()

    start_a, cross_a = _worst_start(ker["A"], ker["pi_A"], MIX_EPS, MIX_STEPS)
    start_b, cross_b = _worst_start(ker["B"], ker["pi_B"], MIX_EPS, MIX_STEPS)

    # Cross-check against the package's own mixing-time routine.
    t_a = markov.mixing_time(ker["A"], ker["pi_A"], epsilon=MIX_EPS)
    t_b = markov.mixing_time(ker["B"], ker["pi_B"], epsilon=MIX_EPS)
    assert (cross_a, cross_b) == (t_a, t_b), (cross_a, t_a, cross_b, t_b)

    traj_a = _tv_trajectory(ker["A"], ker["pi_A"], start_a, MIX_STEPS)
    traj_b = _tv_trajectory(ker["B"], ker["pi_B"], start_b, MIX_STEPS)

    gap_a = markov.spectral_gap(ker["A"])
    gap_b = markov.spectral_gap(ker["B"])

    steps = np.arange(MIX_STEPS + 1)

    fig, ax = plt.subplots(figsize=(7.2, 4.9))
    ax.set_yscale("log")

    ax.axhline(MIX_EPS, color=INK_MUTED, lw=0.9, ls=(0, (5, 3)), zorder=2)
    ax.text(MIX_STEPS, MIX_EPS * 1.35, f"$\\varepsilon = {MIX_EPS}$",
            ha="right", va="bottom", fontsize=FS_ANNOT, color=INK_MUTED)

    ax.plot(steps, traj_a, color=S1, lw=2.0, ls="-", marker="o", ms=5.5,
            mec=SURFACE, mew=0.9, zorder=4,
            label=f"independent-mask kernel (worst start: $V = {start_a}$)")
    ax.plot(steps, traj_b, color=S2, lw=2.0, ls="--", dashes=(4, 2.2),
            marker="s", ms=5.0, mec=SURFACE, mew=0.9, zorder=4,
            label=f"yarrow-induced kernel (worst start: $V = {start_b}$)")

    for t, traj, colour, va in ((t_a, traj_a, S1, "bottom"), (t_b, traj_b, S2, "top")):
        ax.plot([t, t], [ax.get_ylim()[0], traj[t]], color=colour, lw=0.9,
                ls=":", zorder=3)
        ax.scatter([t], [traj[t]], s=90, facecolor="none", edgecolor=colour,
                   linewidth=1.6, zorder=5)

    ax.annotate(
        f"crosses $\\varepsilon$ at step {t_a}",
        xy=(t_a, traj_a[t_a]), xytext=(t_a - 3.4, 2.2e-3),
        ha="center", va="center", fontsize=FS_ANNOT, color=S1,
        arrowprops=dict(arrowstyle="->", color=S1, lw=1.0, shrinkA=2, shrinkB=6),
    )
    ax.annotate(
        f"crosses $\\varepsilon$ at step {t_b}",
        xy=(t_b, traj_b[t_b]), xytext=(t_b + 3.2, 4.0e-2),
        ha="center", va="center", fontsize=FS_ANNOT, color=S2,
        arrowprops=dict(arrowstyle="->", color=S2, lw=1.0, shrinkA=2, shrinkB=6),
    )

    ax.text(
        0.985, 0.972,
        f"Both kernels are six-fold tensor powers of a two-state chain with second\n"
        f"eigenvalue $1/2$: spectral gap {gap_a:.3f} for the independent mask and "
        f"{gap_b:.3f} for\nthe yarrow kernel. The two decay slopes are therefore parallel "
        f"(a factor of\nabout 2 per step) — the correction shifts the curve, not its rate.",
        transform=ax.transAxes, ha="right", va="top",
        fontsize=FS_ANNOT, color=INK,
        bbox=dict(boxstyle="round,pad=0.45", facecolor="#f4f7fd",
                  edgecolor=S1, linewidth=0.9),
    )

    ax.set_xlabel("step number $t$ (one application of the kernel)")
    ax.set_ylabel("total-variation distance to stationarity (dimensionless)")
    ax.set_xticks(steps[::1])
    ax.set_xlim(-0.35, MIX_STEPS + 0.35)
    ax.set_ylim(1e-5, 2.0)
    ax.set_axisbelow(True)
    ax.grid(color=GRID, linewidth=0.6)
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 0.02))

    titled(
        ax,
        "Both kernels mix at the same rate; only the target differs",
        "worst-case initial state, distance measured against each kernel's own stationary distribution",
    )
    fig.subplots_adjust(top=0.855, bottom=0.115, left=0.095, right=0.985)
    return save(fig, outdir, "fig5_mixing")


# ==========================================================================
# Figure 6 — information quantities
# ==========================================================================

def fig6_information(outdir: str) -> list:
    """Entropy and mutual information: model as published vs yarrow-exact."""
    q = _yarrow_quantities()

    h_cast = information.hexagram_entropy()                      # 6 bits
    h_derived_assumed = information.hexagram_entropy()           # uniform => 6 bits
    h_derived_exact = encoding.N_LINES * information.binary_entropy(q["p_derived_yang"])
    mi_mask = information.mutual_information_independent_mask(Fraction(1, 4))
    mi_yarrow = information.mutual_information_from_line_joint(q["joint"])
    h_mask = information.mask_entropy(Fraction(1, 4))

    rows = [
        ("$H(B)$\ncast hexagram", h_cast, h_cast,
         "uniform on 64 states under both models"),
        ("$H(B')$\ntransformed hexagram", h_derived_assumed, h_derived_exact,
         "the transformed hexagram is yin-biased, so it is not uniform"),
        ("$I(B; B')$\nmutual information", mi_mask, mi_yarrow,
         "the true joint law transmits more than the independent mask does"),
    ]

    y = np.arange(len(rows), dtype=float)[::-1]
    height = 0.34
    delta_x = 6.62   # a single aligned column for the change, clear of every bar

    fig, ax = plt.subplots(figsize=(7.5, 4.5))

    for i, (_, v_assumed, v_exact, _) in enumerate(rows):
        yy = y[i]
        ax.barh(yy + height / 2, v_assumed, height * 0.90,
                color=S1, edgecolor=SURFACE, linewidth=1.2, hatch=HATCH_1, zorder=3,
                label="model as published (independent mask)" if i == 0 else None)
        ax.barh(yy - height / 2, v_exact, height * 0.90,
                color=S2, edgecolor=SURFACE, linewidth=1.2, hatch=HATCH_2, zorder=3,
                label="yarrow-induced (exact)" if i == 0 else None)
        ax.text(v_assumed + 0.075, yy + height / 2, f"{v_assumed:.4f} bits",
                ha="left", va="center", fontsize=FS_VALUE, color=INK)
        ax.text(v_exact + 0.075, yy - height / 2, f"{v_exact:.4f} bits",
                ha="left", va="center", fontsize=FS_VALUE, color=INK)

        delta = v_exact - v_assumed
        if abs(delta) > 1e-12:
            ax.text(delta_x, yy, f"{delta:+.4f} bits", ha="left", va="center",
                    fontsize=FS_VALUE, color=S2, fontweight="bold")
        else:
            ax.text(delta_x, yy, "unchanged", ha="left", va="center",
                    fontsize=FS_VALUE, color=INK_MUTED)

    ax.text(delta_x, y[0] + height + 0.28, "change", ha="left", va="center",
            fontsize=FS_VALUE, color=INK_MUTED, style="italic")

    for i, (_, _, _, note) in enumerate(rows):
        ax.text(0.075, y[i] - height - 0.155, note, ha="left", va="center",
                fontsize=FS_VALUE, color=INK_MUTED)

    ax.set_yticks(y)
    ax.set_yticklabels([r[0] for r in rows], fontsize=FS_TICK, color=INK)
    ax.tick_params(axis="y", length=0, pad=6)
    ax.set_xlabel("information (bits)")
    ax.set_xlim(0, 8.3)
    ax.set_xticks(np.arange(0, 6.1, 1.0))
    ax.set_ylim(-0.78, len(rows) - 0.14)
    xgrid(ax)
    ax.legend(loc="lower right", bbox_to_anchor=(1.005, -0.02))

    # Formerly a boxed callout in the upper right, which sat on top of the
    # H(B) bars; it is a footnote now.
    caption(
        fig,
        f"$H(M) = {h_mask:.4f}$ bits for the independent mask, so "
        f"$I = 6 - H(M) = {mi_mask:.4f}$ bits. Computing $I$ from the actual "
        f"$2\\times 2$ per-line joint instead gives {mi_yarrow:.4f} bits: "
        f"the transformation retains {100 * mi_yarrow / h_cast:.1f}% of the six bits, "
        f"not {100 * mi_mask / h_cast:.1f}%.",
    )

    titled(
        ax,
        "Correcting the model changes two of the three information quantities",
        "all values in bits; the cast hexagram carries six bits under either model",
    )
    fig.subplots_adjust(top=0.845, bottom=0.175, left=0.165, right=0.985)
    return save(fig, outdir, "fig6_information")


# ==========================================================================
# Figure 7 — the orderings compared as codes and as symmetry structures
# ==========================================================================

ORDER_TRIALS = 4_000
ORDER_SEED = 20260722


def fig7_orderings(outdir: str) -> list:
    """Symmetry versus proximity: King Wen is exact on one, ordinary on the other."""
    n_steps = encoding.N_HEXAGRAMS - 1          # 63 consecutive pairs
    n_couplets = encoding.N_HEXAGRAMS // 2      # 32

    # ---- panel (a): the four orderings as codes --------------------------
    rows = [
        ("Gray code\n(reflected binary)", orderings.gray_ordering()),
        ("Earlier Heaven\nas binary counting", orderings.counting_ordering()),
        ("Earlier Heaven\ntraditional reading", orderings.fuxi_traditional_ordering()),
        ("King Wen\nsequence", king_wen.king_wen_ordering()),
    ]
    profiles = [orderings.distance_profile(order) for _, order in rows]

    for p in profiles:
        assert p["steps"] == n_steps
        assert sum(p["counts"]) == n_steps
        assert p["counts"][0] == 0, "a step of distance zero would repeat a hexagram"

    # The Gray code attains the optimum: every step flips exactly one line.
    assert profiles[0]["counts"][1] == n_steps and profiles[0]["mean"] == 1.0
    # The two readings of the Earlier Heaven arrangement are different sequences
    # over the same set, related by bit reversal, which is an isometry of Q6 —
    # so their distance profiles are identical, term by term.
    rel = orderings.bit_reversal_relation()
    assert rel["reverse_is_hypercube_isometry"]
    assert rel["same_underlying_set"] and not rel["same_sequence"]
    assert rel["positions_that_differ"] > 0
    assert profiles[1]["counts"] == profiles[2]["counts"]
    assert profiles[1]["mean"] == profiles[2]["mean"]
    assert profiles[1]["total_line_changes"] == orderings.fuxi_total_changes_closed_form()

    null = orderings.random_profile_distribution(ORDER_TRIALS, seed=ORDER_SEED)
    exact_null_mean = orderings.expected_random_consecutive_distance()
    assert abs(null["mean"] - exact_null_mean) < 0.05, "simulated null missed the exact mean"
    z_kw = (profiles[3]["mean"] - null["mean"]) / null["stdev"]
    # The headline of panel (a): King Wen is *above* the random mean, not below.
    assert z_kw > 0, "King Wen should sit above the random mean, not below it"

    # ---- panel (b): the couplet claim ------------------------------------
    pair = orderings.pairing_structure(rows[3][1])
    matching = orderings.canonical_matching()
    assert pair["couplets"] == n_couplets
    assert pair["claim_holds"] and pair["unexplained_pairs"] == 0
    assert pair["reversal_pairs"] + pair["complement_pairs"] == n_couplets
    assert matching["is_perfect_matching"]
    assert (matching["reversal_pairs"], matching["complement_pairs"]) == (
        pair["reversal_pairs"], pair["complement_pairs"]
    )
    # The complement couplets are exactly the self-reversing ones.
    for _, a, b in pair["complement_detail"]:
        assert orderings.is_palindromic(a) and orderings.is_palindromic(b)
    comp_labels = ", ".join(
        f"{2 * c - 1}–{2 * c}" for c, _, _ in pair["complement_detail"]
    )

    expected = orderings.expected_explained_couplets_random()
    sim = orderings.pairing_simulation(ORDER_TRIALS, seed=ORDER_SEED)
    nullp = orderings.pairing_null_probability()
    assert sim["max_couplets_explained"] < n_couplets
    assert expected["expected_couplets"] < sim["max_couplets_explained"]
    assert 0.0 < nullp["probability"] < 1e-40
    p_exp = int(np.floor(np.log10(nullp["probability"])))
    p_mant = nullp["probability"] / 10.0 ** p_exp

    # ======================================================================
    fig = plt.figure(figsize=(7.7, 8.4))
    gs = fig.add_gridspec(
        2, 2, height_ratios=[1.0, 0.86], width_ratios=[2.30, 1.0],
        left=0.152, right=0.984, top=0.840, bottom=0.148,
        hspace=0.34, wspace=0.13,
    )
    ax_dist = fig.add_subplot(gs[0, 0])
    ax_mean = fig.add_subplot(gs[0, 1], sharey=ax_dist)
    ax_pair = fig.add_subplot(gs[1, :])

    y_pos = [3.0, 2.0, 1.0, 0.0]          # top row first
    bar_h = 0.62
    x_pad = n_steps * 1.34                # dead margin on the right for the brace

    # ---- (a left) stacked distribution of the 63 consecutive distances ---
    for yy, prof in zip(y_pos, profiles):
        left = 0
        for d in range(1, encoding.N_LINES + 1):
            width = prof["counts"][d]
            if width == 0:
                continue
            ax_dist.barh(yy, width, bar_h, left=left, color=D_RAMP[d - 1],
                         edgecolor=SURFACE, linewidth=1.2, zorder=3)
            if width >= 6:
                ax_dist.text(left + width / 2.0, yy, str(width),
                             ha="center", va="center", fontsize=FS_VALUE,
                             color=SURFACE if d >= 4 else INK, zorder=4)
            left += width
        assert left == n_steps

    # The two Earlier Heaven rows are drawn from different sequences yet come
    # out pixel-identical; say so, in the clear margin beside them.
    x_br, y_hi, y_lo = n_steps * 1.055, y_pos[1] + 0.40, y_pos[2] - 0.40
    ax_dist.plot([x_br, x_br], [y_hi, y_lo], color=INK_MUTED, lw=0.9,
                 clip_on=False, zorder=5)
    for yy in (y_hi, y_lo):
        ax_dist.plot([x_br, x_br + n_steps * 0.028], [yy, yy], color=INK_MUTED,
                     lw=0.9, clip_on=False, zorder=5)
    ax_dist.text(n_steps * 1.11, (y_hi + y_lo) / 2.0, "identical\nprofiles",
                 ha="left", va="center", fontsize=FS_ANNOT, color=INK)

    ax_dist.set_xlim(0, x_pad)
    ax_dist.set_ylim(y_pos[-1] - 0.78, y_pos[0] + 0.62)
    ax_dist.set_xticks([0, 21, 42, n_steps])
    ax_dist.set_yticks(y_pos)
    ax_dist.set_yticklabels([r[0] for r in rows], fontsize=FS_TICK)
    ax_dist.get_yticklabels()[-1].set_fontweight("bold")   # King Wen is the subject
    ax_dist.get_yticklabels()[-1].set_color(INK)
    ax_dist.tick_params(axis="y", length=0, pad=5)
    ax_dist.set_xlabel(f"number of the {n_steps} consecutive steps, "
                       "by the number of lines $d$ that change")
    xgrid(ax_dist)
    ax_dist.spines["bottom"].set_bounds(0, n_steps)
    # The ramp is ordered, so the legend is built in ramp order rather than in
    # the order the segments happen to be drawn.
    ax_dist.legend(
        handles=[Patch(facecolor=D_RAMP[d - 1], edgecolor=SURFACE, linewidth=1.2,
                       label=f"$d = {d}$") for d in range(1, encoding.N_LINES + 1)],
        loc="lower left", bbox_to_anchor=(0.0, 1.005), ncol=6,
        handlelength=1.1, handletextpad=0.45, columnspacing=1.0,
    )
    ax_dist.set_title("(a)  the orderings as codes", loc="left",
                      fontsize=FS_LABEL, pad=24)

    # ---- (a right) the means against the random null ---------------------
    lo, hi = null["mean"] - null["stdev"], null["mean"] + null["stdev"]
    ax_mean.axvspan(lo, hi, facecolor="#e4e2d7", edgecolor="none", zorder=1)
    ax_mean.axvline(null["mean"], color=INK_MUTED, lw=0.9, ls=(0, (4, 2.4)), zorder=2)
    # Set just outside the band so the dashed mean line stays unobstructed.
    ax_mean.text(lo - 0.065, (y_pos[0] + y_pos[-1]) / 2.0,
                 "random null (mean $\\pm$ 1 s.d.)", rotation=90,
                 ha="center", va="center", fontsize=FS_VALUE, color=INK_2, zorder=2)

    for i, (yy, prof) in enumerate(zip(y_pos, profiles)):
        is_kw = (i == 3)
        ax_mean.plot([prof["mean"]], [yy], marker="s" if is_kw else "o",
                     ms=6.2 if is_kw else 6.8,
                     color=S2 if is_kw else S1, mec=SURFACE, mew=0.9, zorder=4)
        ax_mean.text(prof["mean"] + 0.10, yy, f"{prof['mean']:.3f}",
                     ha="left", va="center", fontsize=FS_VALUE,
                     color=S2 if is_kw else INK, zorder=4,
                     fontweight="bold" if is_kw else "normal")
    ax_mean.text(profiles[3]["mean"] + 0.10, y_pos[3] - 0.42,
                 f"{z_kw:+.1f} s.d.", ha="left", va="center",
                 fontsize=FS_VALUE, color=S2)
    ax_mean.text(profiles[0]["mean"] + 0.10, y_pos[0] - 0.42, "the optimum",
                 ha="left", va="center", fontsize=FS_VALUE, color=INK_MUTED)

    ax_mean.set_xlim(0.72, 4.48)
    ax_mean.set_xticks([1, 2, 3, 4])
    ax_mean.set_xlabel("mean lines\nchanged per step")
    ax_mean.tick_params(labelleft=False, left=False)
    ax_mean.set_axisbelow(True)
    ax_mean.grid(axis="x", color=GRID, linewidth=0.6)
    ax_mean.set_title("and their means", loc="left", fontsize=FS_SUB,
                      color=INK_2, fontweight="normal", pad=24)

    # ---- (b) the couplet structure ---------------------------------------
    yb = [2.6, 1.3, 0.0]
    hb = 0.42
    n_rev, n_comp = pair["reversal_pairs"], pair["complement_pairs"]

    # Gridlines are drawn by hand rather than with xgrid() so that they stop
    # above the legend and the callout instead of running through their text.
    grid_top, grid_bot = yb[0] + 0.80, yb[2] - 0.45
    for xt in range(0, n_couplets + 1, 8):
        ax_pair.plot([xt, xt], [grid_bot, grid_top], color=GRID, lw=0.6, zorder=0)
    ax_pair.plot([n_couplets, n_couplets], [grid_bot, grid_top], color=AXIS,
                 lw=0.9, ls=(0, (3, 2.4)), zorder=2)
    ax_pair.barh(yb[0], n_rev, hb, color=S1, edgecolor=SURFACE, linewidth=1.4,
                 hatch=HATCH_1, zorder=3, label="couplet closed by reversal")
    ax_pair.barh(yb[0], n_comp, hb, left=n_rev, color=S2, edgecolor=SURFACE,
                 linewidth=1.4, hatch=HATCH_2, zorder=3,
                 label="couplet closed by complement")
    ax_pair.barh(yb[1], sim["max_couplets_explained"], hb, color=NEUTRAL,
                 edgecolor=SURFACE, linewidth=1.4, zorder=3,
                 label="random ordering (null)")
    ax_pair.barh(yb[2], expected["expected_couplets"], hb, color=NEUTRAL,
                 edgecolor=SURFACE, linewidth=1.4, zorder=3)

    ax_pair.text(n_rev / 2.0, yb[0] + hb / 2 + 0.10, f"{n_rev} by reversal",
                 ha="center", va="bottom", fontsize=FS_ANNOT, color=INK)
    ax_pair.plot([n_rev + n_comp / 2.0] * 2,
                 [yb[0] - hb / 2, yb[0] - hb / 2 - 0.16],
                 color=INK_MUTED, lw=0.7, zorder=2)
    ax_pair.text(n_rev + n_comp / 2.0, yb[0] - hb / 2 - 0.21,
                 f"{n_comp} by complement:\nKing Wen {comp_labels}",
                 ha="center", va="top", fontsize=FS_VALUE, color=INK_2)
    ax_pair.text(n_couplets + 0.9, yb[0],
                 f"{n_rev + n_comp} of {n_couplets}\n"
                 f"{pair['unexplained_pairs']} unexplained",
                 ha="left", va="center", fontsize=FS_ANNOT, color=INK,
                 fontweight="bold")

    ax_pair.text(sim["max_couplets_explained"] + 0.7, yb[1],
                 f"{sim['max_couplets_explained']}", ha="left", va="center",
                 fontsize=FS_VALUE, color=INK)
    ax_pair.text(expected["expected_couplets"] + 0.7, yb[2],
                 f"{expected['expected_couplets']:.2f}", ha="left", va="center",
                 fontsize=FS_VALUE, color=INK)

    ax_pair.text(
        n_couplets + 7.6, -0.90,
        "A uniformly random ordering satisfies the couplet claim with\n"
        f"probability $32!\\cdot 2^{{32}}/64! = {p_mant:.1f}\\times 10^{{{p_exp}}}$.",
        ha="right", va="center", fontsize=FS_ANNOT, color=INK,
        bbox=dict(boxstyle="round,pad=0.45", facecolor="#f4f7fd",
                  edgecolor=S1, linewidth=0.9),
    )

    ax_pair.set_xlim(0, n_couplets + 8.0)
    ax_pair.set_ylim(-1.62, yb[0] + 0.80)
    ax_pair.set_xticks(np.arange(0, n_couplets + 1, 8))
    ax_pair.set_yticks(yb)
    ax_pair.set_yticklabels([
        "King Wen\nsequence",
        f"random ordering\nbest of {ORDER_TRIALS:,}",
        "random ordering\nexpected",
    ], fontsize=FS_TICK)
    ax_pair.get_yticklabels()[0].set_fontweight("bold")
    ax_pair.get_yticklabels()[0].set_color(INK)
    ax_pair.tick_params(axis="y", length=0, pad=5)
    ax_pair.set_xlabel(f"couplets explained (of {n_couplets})")
    ax_pair.set_axisbelow(True)
    ax_pair.spines["bottom"].set_bounds(0, n_couplets)
    ax_pair.legend(loc="lower left", bbox_to_anchor=(0.0, 0.0), ncol=1,
                   handlelength=1.5, handletextpad=0.55)
    ax_pair.set_title("(b)  the King Wen sequence, as a symmetry structure:  "
                      "how each couplet closes",
                      loc="left", fontsize=FS_LABEL, pad=10)

    # ---- figure furniture -------------------------------------------------
    fig.text(0.006, 0.990,
             "King Wen is organised by symmetry, not by proximity",
             ha="left", va="top", fontsize=FS_TITLE, fontweight="bold", color=INK)
    fig.text(0.006, 0.955,
             "as a code the sequence is unremarkable — it changes more lines per step "
             "than a random ordering does;\nas a symmetry structure it is exact — every "
             "one of the 32 couplets is accounted for, with nothing left over",
             ha="left", va="top", fontsize=FS_SUB, color=INK_2)

    caption(
        fig,
        f"Both nulls are computed at run time (seed {ORDER_SEED}): the band in (a) is "
        f"orderings.random_profile_distribution({ORDER_TRIALS:,}), mean {null['mean']:.3f} and "
        f"s.d. {null['stdev']:.3f} against an exact expectation of {exact_null_mean:.3f}; the "
        f"rows in (b) are orderings.expected_explained_couplets_random() and "
        f"orderings.pairing_simulation({ORDER_TRIALS:,}). The two Earlier Heaven rows are different "
        f"sequences — they disagree at {rel['positions_that_differ']} of the 64 positions — "
        f"but bit reversal is an isometry of $Q_6$, so no distance statistic can separate them.",
    )
    return save(fig, outdir, "fig7_orderings")


# ==========================================================================
# Driver
# ==========================================================================

FIGURES = {
    "fig1": fig1_doubling,
    "fig2": fig2_hypercube,
    "fig3": fig3_line_states,
    "fig4": fig4_stationary,
    "fig5": fig5_mixing,
    "fig6": fig6_information,
    "fig7": fig7_orderings,
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Render the Fuxi paper figures as PDF (vector) and PNG (300 dpi)."
    )
    parser.add_argument("--outdir", default=DEFAULT_OUTDIR,
                        help="directory for the output files "
                             "(default: %(default)s)")
    parser.add_argument("--only", choices=sorted(FIGURES), default=None,
                        help="render a single figure instead of all of them")
    args = parser.parse_args(argv)

    outdir = os.path.abspath(args.outdir)
    apply_style()

    names = [args.only] if args.only else sorted(FIGURES)
    for name in names:
        paths = FIGURES[name](outdir)
        for path in paths:
            print(f"wrote {path}  ({os.path.getsize(path):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
