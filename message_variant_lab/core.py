"""Pure validation and aggregation. No predictions or hypothetical savings."""
from datetime import date
from fractions import Fraction


class SchemaError(ValueError):
    """An explicit input field violates the schema."""


FIELDS = {"id", "variant", "structure", "sent_date", "replied", "positive", "meeting", "synthetic"}


def validate(records, as_of):
    try:
        cutoff = date.fromisoformat(as_of)
    except (ValueError, TypeError):
        raise SchemaError("as_of: expected ISO date") from None
    seen = set()
    for index, record in enumerate(records, 1):
        prefix = f"record {index}"
        if not isinstance(record, dict):
            raise SchemaError(f"{prefix}: expected object")
        missing, extra = FIELDS - record.keys(), record.keys() - FIELDS
        if missing or extra:
            raise SchemaError(f"{prefix}: missing fields {sorted(missing)}; unknown fields {sorted(extra)}")
        for field in ("id", "variant", "structure"):
            value = record[field]
            if not isinstance(value, str) or not value.strip() or len(value) > 10000:
                raise SchemaError(f"{prefix}: {field}: expected nonblank string of at most 10000 characters")
            if chr(0x2014) in value or any(ord(c) < 32 for c in value):
                raise SchemaError(f"{prefix}: {field}: forbidden control character or U+2014")
        if record["id"] in seen:
            raise SchemaError(f"{prefix}: id: duplicate {record['id']!r}")
        seen.add(record["id"])
        for field in ("replied", "positive", "meeting", "synthetic"):
            if type(record[field]) is not bool:
                raise SchemaError(f"{prefix}: {field}: expected boolean")
        try:
            sent = date.fromisoformat(record["sent_date"])
        except (ValueError, TypeError):
            raise SchemaError(f"{prefix}: sent_date: expected ISO date") from None
        if sent > cutoff:
            raise SchemaError(f"{prefix}: sent_date: future date relative to as_of")
        if record["meeting"] and not record["positive"] or record["positive"] and not record["replied"]:
            raise SchemaError(f"{prefix}: meeting/positive/replied: inconsistent outcome funnel")
    structures = {}
    for record in records:
        variant = record["variant"]
        if variant in structures and structures[variant] != record["structure"]:
            raise SchemaError(f"variant {variant!r}: structure: conflicting definitions")
        structures[variant] = record["structure"]
    return records


def aggregate(records, as_of):
    validate(records, as_of)
    variants = []
    for name in sorted({r["variant"] for r in records}):
        rows = [r for r in records if r["variant"] == name]
        counts = {key: sum(r[key] for r in rows) for key in ("replied", "positive", "meeting")}
        variants.append({"variant": name, "structure": rows[0]["structure"], "sent": len(rows), **counts,
                         "rates": {key: str(Fraction(value, len(rows))) for key, value in counts.items()}})
    return {"as_of": as_of, "total": len(records), "totals": {key: sum(r[key] for r in records) for key in ("replied", "positive", "meeting")},
            "provenance": {"synthetic_records": sum(r["synthetic"] for r in records),
                           "real_records": sum(not r["synthetic"] for r in records)}, "variants": variants,
            "interpretation": "Observed input outcomes only. Unequal targeting, follow-up and observation windows can confound comparisons. No causal or statistical significance claim.",
            "savings": "Unmeasured: time and money saved are not computed without a measured baseline."}


def compare(result, first, second):
    rows = {r["variant"]: r for r in result["variants"]}
    for name in (first, second):
        if name not in rows:
            raise SchemaError(f"variant: unknown {name!r}")
    return {"first": first, "second": second, "meaning": "Observed rate difference: second minus first; no causal claim.",
            "rate_differences": {key: str(Fraction(rows[second]["rates"][key]) - Fraction(rows[first]["rates"][key])) for key in ("replied", "positive", "meeting")}}
