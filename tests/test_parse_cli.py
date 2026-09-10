"""Guard published data and rejected OCR caches during local re-parsing."""

from types import SimpleNamespace

import parse
import pytest


def test_failed_pdf_does_not_replace_outputs(tmp_path, monkeypatch):
    monkeypatch.setattr(parse, "DATA", tmp_path)
    source = tmp_path / "2016" / "pdfs"
    source.mkdir(parents=True)
    (source / "broken.pdf").write_bytes(b"broken")
    output = tmp_path / "result"
    output.mkdir()
    target = output / "gp_reservation.csv"
    target.write_text("previous snapshot\n")
    assert parse.main(["--year", "2016", "--out", str(output)]) == 1
    assert target.read_text() == "previous snapshot\n"


def test_limited_parse_cannot_overwrite_published_data(tmp_path, monkeypatch):
    monkeypatch.setattr(parse, "DATA", tmp_path)
    with pytest.raises(SystemExit) as exc:
        parse.main(["--limit", "1", "--out", str(tmp_path / "2022")])
    assert exc.value.code == 2


def test_cached_ocr_requires_explicit_opt_in(tmp_path, monkeypatch):
    calls = []
    page = SimpleNamespace(extract_text=lambda: "", find_tables=lambda: [])

    class PDF:
        pages = (page,)

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

    monkeypatch.setattr(parse.pdfplumber, "open", lambda _path: PDF())
    monkeypatch.setattr(parse, "ocr_rows", lambda *_args: calls.append(True) or [])
    assert list(parse.parse_pdf(tmp_path / "source.pdf")) == []
    assert calls == []
    list(parse.parse_pdf(tmp_path / "source.pdf", use_cached_ocr=True))
    assert calls == [True]


@pytest.mark.parametrize(("year", "expected"), [("2016", False), ("2022", True)])
def test_cli_uses_ocr_only_for_accepted_year(tmp_path, monkeypatch, year, expected):
    monkeypatch.setattr(parse, "DATA", tmp_path)
    source = tmp_path / year / "pdfs"
    source.mkdir(parents=True)
    (source / "example.pdf").touch()
    calls = []

    def parsed(_path, _pattern, *, use_cached_ocr):
        calls.append(use_cached_ocr)
        return []

    monkeypatch.setattr(parse, "parse_pdf", parsed)
    assert parse.main(["--year", year]) == 1
    assert calls == [expected]
