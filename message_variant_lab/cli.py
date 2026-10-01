"""Local CLI. Input records are never inferred or silently discarded."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from .core import SchemaError, aggregate, compare, validate
from .fixtures import generate
from .report import banner, json_text, render


class InputError(ValueError):
    pass


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as error:
        raise InputError(f"ParseError: {path}: line {error.lineno}: {error.msg}") from None
    except UnicodeError:
        raise InputError(f"ParseError: {path}: line 1: invalid UTF-8") from None


def load_input(directory, as_of=None):
    root = Path(directory)
    if not root.is_dir():
        raise InputError(f"MissingInput: {root}: use mvl fixtures --out <dir> or provide an input directory")
    metadata = root / "metadata.json"
    if as_of is None:
        if not metadata.exists() and any(root.iterdir()):
            raise SchemaError(f"{metadata}: as_of: supply metadata.json or --as-of YYYY-MM-DD")
        meta = read_json(metadata) if metadata.exists() else {"as_of": "2026-09-30"}
        if not isinstance(meta, dict) or "as_of" not in meta:
            raise SchemaError(f"{metadata}: as_of: missing field")
        as_of = meta["as_of"]
    rows = []
    paths = sorted(root.glob("records*.jsonl"))
    unexpected = [p.name for p in root.iterdir() if p.is_file() and p.name not in {"metadata.json", "expectations.json"} and p not in paths]
    if unexpected:
        raise SchemaError(f"{root}: input files: unsupported {unexpected}; use records*.jsonl")
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8-sig").splitlines()
        except UnicodeError:
            raise InputError(f"ParseError: {path}: line 1: invalid UTF-8") from None
        for line_number, line in enumerate(lines, 1):
            if not line.strip() or line.startswith("#"):
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise InputError(f"ParseError: {path}: line {line_number}: {error.msg}") from None
            try:
                validate(rows + [row], as_of)
            except SchemaError as error:
                raise SchemaError(f"{path}: line {line_number}: {error}") from None
            rows.append(row)
    validate(rows, as_of)
    return rows, as_of, [p.name for p in paths]


def atomic_write(path, content):
    path = Path(path)
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as handle:
            temporary = handle.name
            handle.write(content)
        os.replace(temporary, path)
    except OSError as error:
        raise InputError(f"WriteError: {path}: {error.strerror or str(error)}") from None
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def parser():
    p = argparse.ArgumentParser(description="Compare recorded outreach outcomes, without predictions.")
    sub = p.add_subparsers(dest="command", required=True)
    f = sub.add_parser("fixtures", help="Generate 200 labelled synthetic records", epilog="Example: mvl fixtures --out demo")
    f.add_argument("--out", required=True)
    for name, help_text in (("run", "Compute observed variant outcomes"), ("validate", "Validate record schema and outcome consistency")):
        c = sub.add_parser(name, help=help_text, epilog=f"Example: mvl {name} --input demo")
        c.add_argument("--input", required=True)
        c.add_argument("--as-of")
        if name == "run":
            c.add_argument("--results", default=".mvl/results.json")
    r = sub.add_parser("report", help="Render computed results with provenance", epilog="Example: mvl report --format md")
    r.add_argument("--format", choices=("md", "json"), default="md")
    r.add_argument("--results", default=".mvl/results.json")
    r.add_argument("--out")
    c = sub.add_parser("compare", help="Compare two variants using exact observed rate differences", epilog="Example: mvl compare --first A --second B")
    c.add_argument("--first", required=True)
    c.add_argument("--second", required=True)
    c.add_argument("--results", default=".mvl/results.json")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "fixtures":
            generate(args.out)
            print("Generated 200 SYNTHETIC records; expectations are hand-computed synthetic ground truth.")
        elif args.command in ("run", "validate"):
            rows, as_of, files = load_input(args.input, args.as_of)
            result = aggregate(rows, as_of)
            result["input_files"] = files
            if args.command == "run":
                atomic_write(args.results, json_text(result))
            print(banner(result))
            print(f"{args.command}: {len(rows)} validated records.")
        else:
            if not Path(args.results).is_file():
                raise InputError(f"MissingInput: {args.results}: run mvl run --input <dir> first")
            result = read_json(Path(args.results))
            if args.command == "compare":
                print(json_text({"banner": banner(result), **compare(result, args.first, args.second)}), end="")
            else:
                content = render(result, args.format)
                if args.out:
                    atomic_write(args.out, content)
                else:
                    print(content, end="")
        return 0
    except (InputError, SchemaError, OSError, KeyError, TypeError, ValueError) as error:
        label = "SchemaError: " if isinstance(error, SchemaError) else ""
        print(f"{label}{error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
