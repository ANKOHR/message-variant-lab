import copy
import pytest
from message_variant_lab.core import SchemaError, aggregate, compare
from message_variant_lab.fixtures import records


def test_rejects_adversarial_values():
    for field, value in [("sent_date", "2099-01-01"), ("replied", -1), ("structure", "x" * 10001), ("amount", -10), ("meeting", "yes"), ("variant", "bad" + chr(0x2014))]:
        rows = records()
        rows[0][field] = value
        with pytest.raises(SchemaError, match=field):
            aggregate(rows, "2026-09-30")
    rows = records()
    rows[1]["id"] = rows[0]["id"]
    with pytest.raises(SchemaError, match="duplicate"):
        aggregate(rows, "2026-09-30")


def test_handles_unicode_and_long_inputs():
    rows = records()
    for row in rows:
        row["structure"] = "你好 café C:\\Users\\Henry " + "x" * 9000
    assert aggregate(rows, "2026-09-30")["total"] == 200


def test_corrupted_ground_truth_changes_result():
    rows = copy.deepcopy(records())
    rows[99]["replied"] = True
    assert aggregate(rows, "2026-09-30")["totals"]["replied"] == 61


def test_exact_comparison():
    result = aggregate(records(), "2026-09-30")
    assert compare(result, "A", "B")["rate_differences"] == {"replied": "1/5", "positive": "1/10", "meeting": "1/20"}


def test_funnel_and_structure_consistency():
    rows = records()
    rows[-1]["meeting"] = True
    with pytest.raises(SchemaError, match="inconsistent"):
        aggregate(rows, "2026-09-30")
    rows = records()
    rows[1]["structure"] = "different"
    with pytest.raises(SchemaError, match="structure"):
        aggregate(rows, "2026-09-30")
