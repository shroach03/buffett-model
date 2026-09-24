"""CLI regression tests: briefs contain non-ASCII (×, −, ≥) and must write and print
cleanly on platforms whose default codepage is not UTF-8 (Windows)."""
from pathlib import Path

from buffett.cli import main


def test_analyze_writes_utf8_with_lf_endings(tmp_path, capsys):
    assert main(["analyze", "ROL", "--out", str(tmp_path)]) == 0
    raw = (tmp_path / "ROL.md").read_bytes()
    text = raw.decode("utf-8")           # must be valid UTF-8, whatever the platform default
    assert "≥" in text and "×" in text
    assert b"\r\n" not in raw            # reproducible briefs: LF everywhere
    assert "Verdict" in capsys.readouterr().out


def test_screen_prints_multiplication_sign(capsys):
    assert main(["screen", "ROL"]) == 0
    assert "×" in capsys.readouterr().out
