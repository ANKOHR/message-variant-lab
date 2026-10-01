import json
import time
import pytest
from message_variant_lab.cli import main
from message_variant_lab.fixtures import generate, records


def test_run_completes_on_fixture(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    started = time.perf_counter()
    assert main(["fixtures", "--out", "demo"]) == 0
    assert main(["run", "--input", "demo"]) == 0
    assert main(["report", "--format", "md"]) == 0
    assert time.perf_counter() - started < 5
    assert "Data provenance" in capsys.readouterr().out


def test_empty_input_renders_without_traceback(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "empty").mkdir()
    assert main(["run", "--input", "empty"]) == 0
    assert main(["report", "--format", "json"]) == 0
    assert '"total": 0' in capsys.readouterr().out


def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path / "records.jsonl").write_text("# header\n{bad}")
    assert main(["validate", "--input", str(tmp_path), "--as-of", "2026-09-30"]) == 2
    error = capsys.readouterr().err
    assert "ParseError" in error and "records.jsonl: line 2" in error


def test_determinism_byte_identical(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    generate("demo")
    assert main(["run", "--input", "demo"]) == 0
    first = (tmp_path / ".mvl/results.json").read_bytes()
    assert main(["run", "--input", "demo"]) == 0
    assert first == (tmp_path / ".mvl/results.json").read_bytes()
    for fmt in ("md", "json"):
        main(["report", "--format", fmt, "--out", "first.txt"])
        main(["report", "--format", fmt, "--out", "second.txt"])
        assert (tmp_path / "first.txt").read_bytes() == (tmp_path / "second.txt").read_bytes()


def test_cli_smoke_all_subcommands(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for command in ("fixtures", "run", "report", "validate", "compare"):
        with pytest.raises(SystemExit) as error:
            main([command, "--help"])
        assert error.value.code == 0
    assert main(["fixtures", "--out", "demo"]) == 0
    assert main(["validate", "--input", "demo"]) == 0
    assert main(["run", "--input", "demo"]) == 0
    assert main(["compare", "--first", "A", "--second", "B"]) == 0
    assert main(["report", "--format", "json"]) == 0


def test_missing_input_and_write_failure(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["run", "--input", "absent"]) == 2
    assert "MissingInput" in capsys.readouterr().err
    generate("demo")
    assert main(["run", "--input", "demo", "--results", "demo"]) == 2
    assert "WriteError" in capsys.readouterr().err
    assert sorted(p.name for p in (tmp_path / "demo").iterdir()) == ["expectations.json", "metadata.json", "records.jsonl"]


def test_tiny_hand_written_input(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "tiny").mkdir()
    rows = [dict(id=str(i), variant="A", structure="Problem, ask", sent_date="2026-09-01", replied=i < 2, positive=i < 1, meeting=False, synthetic=True) for i in range(5)]
    (tmp_path / "tiny/records.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    assert main(["run", "--input", "tiny", "--as-of", "2026-09-30"]) == 0
    result = json.loads((tmp_path / ".mvl/results.json").read_text())
    assert result["total"] == 5 and result["totals"] == {"replied": 2, "positive": 1, "meeting": 0}
