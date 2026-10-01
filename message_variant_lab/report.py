"""Deterministic reports with explicit provenance and measurement limits."""
import json


def json_text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def banner(result):
    p = result["provenance"]
    return f"Data provenance: {p['synthetic_records']} synthetic fixture records; {p['real_records']} real records declared as Henry's own hand-entered data by the input author (not independently verified)."


def render(result, format="md"):
    if format == "json":
        return json_text({"banner": banner(result), **result})
    lines = ["# Message Variant Lab", "", banner(result), "", f"As of: {result['as_of']}", f"Total sent: {result['total']}",
             f"Totals: replied={result['totals']['replied']}, positive={result['totals']['positive']}, meeting={result['totals']['meeting']}", "",
             "| Variant | Sent | Replies | Positive | Meetings | Reply rate | Positive rate | Meeting rate |",
             "| --- | ---: | ---: | ---: | ---: | --- | --- | --- |"]
    for row in result["variants"]:
        name = row["variant"].replace("|", "\\|")
        lines.append(f"| {name} | {row['sent']} | {row['replied']} | {row['positive']} | {row['meeting']} | {row['rates']['replied']} | {row['rates']['positive']} | {row['rates']['meeting']} |")
    lines += ["", "Rates are exact fractions of recorded sends, including sends with no recorded reply.", "", result["interpretation"], "", result["savings"], ""]
    return "\n".join(lines)
