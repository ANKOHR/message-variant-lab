"""Synthetic fixture generation, deterministic with no randomness or seed."""
from pathlib import Path
from .report import json_text

# Hand-computed: each variant has 100 sends. A: 20/10/5; B: 40/20/10.
EXPECTATIONS = {"synthetic": True, "total": 200, "totals": {"replied": 60, "positive": 30, "meeting": 15},
                "variants": {"A": {"sent": 100, "replied": 20, "positive": 10, "meeting": 5, "rates": {"replied": "1/5", "positive": "1/10", "meeting": "1/20"}},
                             "B": {"sent": 100, "replied": 40, "positive": 20, "meeting": 10, "rates": {"replied": "2/5", "positive": "1/5", "meeting": "1/10"}}}}


def records():
    return [{"id": f"{variant}-{i:03}", "variant": variant, "structure": "Problem, evidence, ask" if variant == "A" else "Evidence, problem, ask",
             "sent_date": "2026-09-01", "replied": i < reply, "positive": i < positive, "meeting": i < meeting, "synthetic": True}
            for variant, reply, positive, meeting in (("A", 20, 10, 5), ("B", 40, 20, 10)) for i in range(100)]


def generate(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "records.jsonl").write_text("# SYNTHETIC fixture data; not real outreach results\n" + "".join(__import__("json").dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records()), encoding="utf-8")
    (out / "expectations.json").write_text(json_text({"label": "SYNTHETIC hand-computed ground truth", **EXPECTATIONS}), encoding="utf-8")
    (out / "metadata.json").write_text(json_text({"label": "SYNTHETIC fixture metadata", "synthetic": True, "as_of": "2026-09-30"}), encoding="utf-8")
