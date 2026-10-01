# Message Variant Lab

A local Python CLI for comparing recorded outreach structures. It counts sends, replies, positive replies and meetings by variant. Exact rational rates and differences are computed from records. It does not discover demand or predict results.

## Quickstart

Python 3.10 or newer, CPU only, no runtime dependencies. Install locally without fetching packages:

```powershell
python -m pip install --no-build-isolation --no-deps -e .
mvl fixtures --out demo
mvl run --input demo
mvl report --format md
python -m pytest -q
```

Alternatively use `python -m message_variant_lab.cli` in place of `mvl`. No network calls, GPU packages, language models or database server are used.

## Input reference

A directory contains `records*.jsonl` and optional `metadata.json`. Each nonblank, noncomment line is one JSON object. Comments start with `#`. Other files are rejected except `expectations.json`, which is never used to compute results. Only JSONL records and JSON metadata are supported; CSV/YAML are rejected with a named schema error rather than guessed. Malformed JSON errors name the file and physical line.

```json
{"id":"lead-1","variant":"A","structure":"Problem, evidence, ask","sent_date":"2026-09-01","replied":true,"positive":true,"meeting":false,"synthetic":false}
```

Every field is required; unknown fields are rejected, including amounts or savings. IDs are unique across files. Text is nonblank and at most 10,000 characters; Unicode and Windows paths are supported with normal JSON escaping. Control characters and U+2014 are rejected. Boolean fields require JSON booleans. Dates are ISO dates and cannot exceed the explicit observation cutoff. Meetings require positive replies, which require replies. Each variant has one consistent structure. Invalid records fail the entire run and are never silently dropped.

Set `metadata.json` to `{"as_of":"2026-09-30","synthetic":false}` or supply `--as-of YYYY-MM-DD`. An empty directory returns zero counts with the documented default cutoff 2026-09-30. Nonempty directories require an explicit cutoff. Outcomes are snapshots as of that cutoff, declared by the author. The CLI cannot verify when a reply occurred. Use equivalent observation windows and targeting to make comparisons meaningful. Missing replies count as false, not as inferred outcomes. Label real records `synthetic:false` only for Henry's own hand-entered data; the tool trusts this declaration and does not independently authenticate it.

## Commands and examples

- `mvl fixtures --out demo`: create 200 labelled synthetic records and hand-computed expectations.
- `mvl validate --input demo`: check schema, duplicate IDs, dates and outcome funnel.
- `mvl run --input demo --results .mvl/results.json`: compute and atomically store results.
- `mvl report --format md`: render stored results. JSON is available with `--format json`; `--out report.md` writes atomically.
- `mvl compare --first A --second B`: exact observed rate differences, second minus first, with provenance.

All commands have `--help` with examples. Missing input returns `MissingInput` with a usage hint. Parsing returns `ParseError`; field violations return `SchemaError`. Errors exit 2. Output failures return `WriteError`, preserve prior files and remove temporary files. Fixture generation overwrites its three named files; do not point it at real data. Reports consume the saved run, so rerun after editing inputs. Stored results are trusted local artifacts, not an authenticated audit trail.

## Architecture

```text
records*.jsonl + metadata.json
             |
         cli loader -> pure core validation -> pure aggregation
                                                |
                                          .mvl/results.json
                                                |
                                      report or compare renderer
fixtures generator -> labelled records + independent expectations
```

Outputs include the cutoff, input filenames, variant structure and counts. Records are traceable by ID in the input files. Rates are exact fractions, with no rounding or division by zero on empty input. Same input, filenames and cutoff give byte-identical UTF-8 output. No randomness is used, so no seed is required. Absolute workspace paths and current timestamps are excluded from computed artifacts.

## Honesty boundary and fixture policy

Only input outcomes are measured. Synthetic counts are computed fixture results, never real outreach performance. Every report and comparison includes synthetic and real record counts in its provenance banner. Real provenance is an author declaration. There is no significance test, causal claim, demand prediction or recommended winner. Targeting, follow-up, small samples and observation windows can confound any observed difference.

Time or money saved is unmeasured and explicitly refused without a measured baseline. No hypothetical or illustrative savings figures are shipped. Fixture JSONL has a synthetic header and `synthetic:true` on every record; JSON fixture metadata and expectations carry synthetic fields and labels. JSON has no comment syntax, so its label field serves as the header. The planted fixture has 100 sends each for A and B: A has 20 replies, 10 positive replies and 5 meetings; B has 40, 20 and 10. Total counts are 200, 60, 30 and 15. Expectations are written independently of aggregation. A separate hand-written five-record test establishes the smallest real workflow.

## Evidence and acceptance

`python -m pytest -q` checks exact hand-computed counts and rates, zero false positives on all-negative input, corruption sensitivity, empty input, named errors, Unicode, long text, atomic output failure and byte determinism. The end-to-end fixture test times generation, run and report together against the five-second threshold. Local measured build timing and test count are recorded in BUILD-DONE.txt. This validates computational correctness on planted data, not improved outbound performance.

## Two-week improvement hook and verdict

After two weeks of actual use, hand-check at least 20 records and the variant totals. Measure core-output error rate as mismatched checked fields divided by checked fields, recording numerator, denominator, dates and usage days in EVIDENCE.md. If error rate exceeds 10 percent, fix the most frequent failure cause and repeat the audit, or kill with a recorded reason. If unused, record that evidence and kill. Do not estimate time savings; measure against a timed manual baseline if desired.

Final verdict is pending the real-use evidence window. Choose expand for daily use or revenue, integrate for heavy overlap with a sibling, commercialise if a buyer would pay as-is, maintain as portfolio evidence otherwise, or kill if unused or acceptance cannot be met. No real trial data is shipped.
