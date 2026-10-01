import json
from message_variant_lab.fixtures import generate, EXPECTATIONS
from message_variant_lab.cli import load_input
from message_variant_lab.core import aggregate


def test_fixtures_labelled_synthetic(tmp_path):
    generate(tmp_path)
    assert (tmp_path / "records.jsonl").read_text().startswith("# SYNTHETIC")
    for path in tmp_path.glob("*.json"):
        assert json.loads(path.read_text())["synthetic"] is True
        assert "SYNTHETIC" in json.loads(path.read_text())["label"]
    rows, _, _ = load_input(tmp_path)
    assert len(rows) == 200 and all(r["synthetic"] for r in rows)


def test_fixture_ground_truth_matches_hand_computed(tmp_path):
    generate(tmp_path)
    rows, as_of, _ = load_input(tmp_path)
    result = aggregate(rows, as_of)
    assert result["total"] == EXPECTATIONS["total"]
    assert result["totals"] == EXPECTATIONS["totals"]
    for row in result["variants"]:
        assert {k: row[k] for k in EXPECTATIONS["variants"][row["variant"]]} == EXPECTATIONS["variants"][row["variant"]]
