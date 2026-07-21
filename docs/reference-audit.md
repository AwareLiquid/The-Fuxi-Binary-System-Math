# Reference audit

The formalization checks the claims. This file checks the citations.

Twenty-two references circulating with the informal version of this analysis
were each checked against a publisher page, DOI record, or authoritative index.
The rule applied was strict: a citation was not accepted on the strength of
matching metadata appearing in a citation aggregator or in another paper's
reference list, because that is exactly how a copying error propagates.

**Result: 9 verified, 12 corrected, 1 does not exist.**

That failure rate is worth stating plainly. Better than half the reference list
carried at least one wrong field.

## Does not exist

> Ke Z. *Analysis of the Dayan divination method and the probability of milfoil
> divination of Yi-ology.* Studies of Zhouyi, 2006(3): 62–67.

This reference should not be cited. The full table of contents of 《周易研究》
2006 年第 3 期 contains fourteen articles. None is on divination probability,
none has an author surnamed Ke, and nothing appears at pages 62–67 matching the
description. Ke Zineng (柯资能) does have articles in *Studies of Zhouyi*, in
2001(3) and 2007(2), but none in 2006.

The supplied English title is a close translation of a real article, but a
different one:

> 孙涤. 解析大衍筮法及易卦的蓍占概率. 《文史哲》 2018 年第 1 期, 47–59 页.
> Sun D. *Analysis of the Dayan divination method and the yarrow-divination
> probabilities of the Yi hexagrams.* Literature, History and Philosophy,
> 2018(1): 47–59.

confirmed on the journal's own site. A second real candidate covering the same
ground is 向传三, 《周易筮法的概率研究》, 《周易研究》1997 年第 4 期.

The manuscript cites the Sun article in place of the non-existent one.

## Corrected

| Reference | Field(s) wrong | Corrected to |
|---|---|---|
| Maitre, *Science in Context* | year, volume, issue, pages | **2023, 36(1), 38–59** |
| Schöter, *The Oracle* | issue, pages, title | **2(7), 19–34**, "Boolean Algebra and the Yi Jing" |
| Schöter, *J. Chinese Philosophy* | pages | **297–317** |
| Hu et al., *Prog. Biophys. Mol. Biol.* | pages | **354–368** |
| Castro-Chávez 2012 | title truncated, no vol/page | full title; **1(1): 3** |
| Lien et al., *Prog. Drug Res.* | volume, pages, author list | **48, 9–25**; four named authors, no "et al." |
| Tang, *The Northern Forum* | year, issue, pages | **2017, no. 5, 43–46** |
| Zenil, *A Computable Universe* | year, pages | **2012, 1–20** |
| Sorkin, *Lectures on Quantum Gravity* | place, editors | **New York**; eds. Gomberoff & Marolf |
| Mattingly, *Living Rev. Relativ.* | title | "**Modern** Tests of Lorentz Invariance" |
| Lai, *Int. J. Sino-Western Studies* | pages | **58–67** |
| Beane et al. | stray "Wolfram model /" prefix | prefix deleted |

### The Maitre trap

This one is worth singling out because it looks like a typo and is not. The
article was published in *Science in Context* **36(1), March 2023, pp. 38–59**.
It appeared online first on 15 August 2025, and Cambridge registered the DOI in
2025 while clearing a backlog, so the DOI string itself contains `725`. Citing
it as a 2025 article is a natural mistake that both Crossref and the Cambridge
Core landing page contradict.

## Verified

Aiton & Shimao 1981; Goldenberg 1975; Hayata 2012 (with a caveat, below);
Lloyd 2005; Bostrom 2003; Gorard 2020; Wolfram 2002; Freeland & Hurst 1998;
Castro-Chávez 2014.

## Caveats on verified entries

**Hayata 2012.** Volume, issue and start page are confirmed. The end page (65)
rests on the citation itself: the publisher's site (scipress.org) was offline
during the audit and the Internet Archive rate-limited the request.

**Lloyd 2005.** The supplied title matches **v1 only**. Later arXiv versions are
retitled "A theory of quantum gravity based on quantum computation". Cite
`quant-ph/0501135v1` explicitly.

**Bostrom 2003.** The printed article reads "Are *You* Living in a Computer
Simulation?"; the publisher's deposited metadata says "Are *We*". The printed
form is used.

**Tang 2017.** Confirmed through the NCPSSD national index rather than through a
copy anyone has read. Note the transliteration is 蒙特卡**洛**, not 蒙特卡**罗**;
searching the latter returns nothing.

**Lai 2019.** Appears nowhere outside the publisher's own archive. That absence
reflects the discoverability of a small journal, not a problem with the article;
the page range was confirmed on the publisher's table of contents.

## Venue flags

Castro-Chávez 2012 (Herbert Publications) and Castro-Chávez 2014 (OMICS
Publishing Group) are in titles from publishers widely listed as predatory. Both
works exist and both DOIs resolve. This is recorded because a reviewer may
decline to let them carry evidential weight, not because the metadata is wrong.

## Method

Each reference was resolved to the work itself, its publisher page, or an
authoritative index record. Where a Chinese-language reference could not be
resolved that way, the journal's own issue table of contents was pulled and read
in full, which is how the non-existent reference above was identified: a negative
result over a complete table of contents is much stronger evidence than a failed
search.
