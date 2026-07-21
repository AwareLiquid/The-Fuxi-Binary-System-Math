"""End-to-end tests for ``verify_all.py``.

``build_report`` runs every check in the package. These tests confirm that it
completes, that the report has the expected shape, and that the three headline
corrections really do come back with the CORRECTED verdict rather than quietly
being confirmed.

The Monte-Carlo trial count is reduced to 50 000 so the suite stays fast; the
seed inside :mod:`fuxi.yarrow` is fixed, so the run is deterministic.
"""

from __future__ import annotations

import pytest

import verify_all
from verify_all import CONFIRMED, CORRECTED, NEW, REFINED

TRIALS = 50_000

ALLOWED_VERDICTS = {CONFIRMED, REFINED, CORRECTED, NEW}

EXPECTED_CHECK_IDS = [
    "E1", "E2", "E3", "E4", "E5", "E6",
    "A1", "A2", "A3", "A4", "A5", "A6",
    "Y1", "Y2", "Y3", "Y4", "Y5", "Y6", "Y7", "Y8", "Y9",
    "M1", "M2", "M3", "M4", "M5",
    "T1", "T2", "T3", "T4", "T5", "T6", "T7",
    "I1", "I2", "I3", "I4", "I5",
    "G1", "G2",
]

#: The checks that contradict the prior analysis and must stay CORRECTED.
MUST_BE_CORRECTED = {
    "Y5": "mask independence: P(change|yang)=3/8 vs P(change|yin)=1/8",
    "Y6": "the derived hexagram is not uniform",
    "M3": "the yarrow kernel is not uniform-stationary",
    "T4": "clustering coefficient of Q6 is 0, not 5/12",
    "I4": "I(B;B') from the true joint is 1.2326, not 1.1323",
    "I5": "the transformed hexagram carries 5.7266 bits, not 6",
    "G1": "the genetic dichotomies span 2 GF(2) dimensions, not 3",
}


@pytest.fixture(scope="module")
def report():
    return verify_all.build_report(TRIALS)


# --------------------------------------------------------------------------
# Shape of the report
# --------------------------------------------------------------------------

def test_build_report_runs_end_to_end_and_returns_40_checks(report):
    assert isinstance(report, verify_all.Report)
    assert len(report.checks) == 40


def test_check_ids_are_exactly_the_expected_set_in_order(report):
    assert [c.cid for c in report.checks] == EXPECTED_CHECK_IDS
    assert len(set(EXPECTED_CHECK_IDS)) == 40, "check ids must be unique"


def test_every_verdict_is_in_the_allowed_set(report):
    for check in report.checks:
        assert check.verdict in ALLOWED_VERDICTS, (
            f"{check.cid} has unknown verdict {check.verdict!r}"
        )


def test_every_check_carries_a_claim_a_stated_and_a_computed_value(report):
    for check in report.checks:
        assert check.topic
        assert check.claim
        assert check.stated
        assert check.computed


def test_counts_sum_to_the_number_of_checks(report):
    counts = report.counts()
    assert set(counts) == ALLOWED_VERDICTS
    assert sum(counts.values()) == len(report.checks) == 40


def test_verdict_breakdown_is_stable(report):
    """24 confirmed, 5 refined, 7 corrected, 4 new."""
    assert report.counts() == {
        CONFIRMED: 24,
        REFINED: 5,
        CORRECTED: 7,
        NEW: 4,
    }


def test_topics_cover_all_seven_modules(report):
    topics = {c.topic for c in report.checks}
    assert topics == {
        "Encoding", "Automaton", "Yarrow", "Markov",
        "Topology", "Information", "Genetic code",
    }


# --------------------------------------------------------------------------
# The corrections
# --------------------------------------------------------------------------

@pytest.mark.parametrize("cid,reason", sorted(MUST_BE_CORRECTED.items()))
def test_headline_corrections_carry_the_corrected_verdict(report, cid, reason):
    check = next(c for c in report.checks if c.cid == cid)
    assert check.verdict == CORRECTED, f"{cid} should be CORRECTED ({reason})"


def test_clustering_check_reports_zero_and_explains_bipartiteness(report):
    check = next(c for c in report.checks if c.cid == "T4")
    assert check.verdict == CORRECTED
    assert "0.4167" in check.stated       # the value that was claimed
    assert "0 triangles" in check.computed
    assert "bipartite" in check.note


def test_mask_independence_check_reports_both_conditionals(report):
    check = next(c for c in report.checks if c.cid == "Y5")
    assert check.verdict == CORRECTED
    assert "3/8" in check.computed
    assert "1/8" in check.computed
    assert "not independent" in check.computed


def test_genetic_dimension_check_reports_gf2_rank_two(report):
    check = next(c for c in report.checks if c.cid == "G1")
    assert check.verdict == CORRECTED
    assert "GF(2) rank 2" in check.computed
    assert "512" in check.note


def test_checks_that_should_pass_are_confirmed(report):
    """Regression guard: the exhaustive algebraic checks must not slip."""
    confirmed = {c.cid for c in report.checks if c.verdict == CONFIRMED}
    for cid in ("E1", "E2", "E3", "E4", "E6", "A1", "A2", "A3", "A4",
                "Y1", "Y2", "Y3", "Y4", "M1", "M2", "T1", "T2", "T5", "T6",
                "I1", "I2", "I3", "G2"):
        assert cid in confirmed, f"{cid} unexpectedly not CONFIRMED"


# --------------------------------------------------------------------------
# Reporting helpers
# --------------------------------------------------------------------------

def test_print_console_runs_without_error(report, capsys):
    verify_all.print_console(report)
    out = capsys.readouterr().out
    assert "40 checks" in out
    assert "corrected" in out


def test_write_markdown_produces_a_file_naming_every_check(report, tmp_path):
    path = tmp_path / "report.md"
    verify_all.write_markdown(report, str(path), TRIALS)
    text = path.read_text(encoding="utf-8")
    assert text.startswith("# Verification report")
    for cid in EXPECTED_CHECK_IDS:
        assert f"### {cid} " in text
    assert "CORRECTED" in text
