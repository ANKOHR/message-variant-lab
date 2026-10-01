import json
from message_variant_lab.core import aggregate
from message_variant_lab.fixtures import records, EXPECTATIONS
from message_variant_lab.report import render


def test_report_matches_ground_truth_exact():
    result = json.loads(render(aggregate(records(), "2026-09-30"), "json"))
    assert result["totals"] == EXPECTATIONS["totals"]
    assert result["total"] == 200
    for row in result["variants"]:
        assert {k: row[k] for k in EXPECTATIONS["variants"][row["variant"]]} == EXPECTATIONS["variants"][row["variant"]]


def test_report_zero_false_positives():
    rows = records()
    for row in rows:
        row.update(replied=False, positive=False, meeting=False)
    result = json.loads(render(aggregate(rows, "2026-09-30"), "json"))
    assert result["totals"] == {"replied": 0, "positive": 0, "meeting": 0}


def test_report_carries_provenance_banner():
    rows = records()
    rows[0]["synthetic"] = False
    for fmt in ("md", "json"):
        text = render(aggregate(rows, "2026-09-30"), fmt)
        assert "199 synthetic" in text and "1 real" in text
        assert "not independently verified" in text


def test_hypothetical_figures_labelled():
    text = render(aggregate(records(), "2026-09-30"))
    assert "Unmeasured: time and money saved are not computed" in text
    assert "No causal or statistical significance claim" in text


def test_no_em_dashes_in_outputs():
    for fmt in ("md", "json"):
        assert chr(0x2014) not in render(aggregate(records(), "2026-09-30"), fmt)
