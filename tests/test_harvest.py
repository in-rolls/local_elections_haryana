"""Reject broken downloads without replacing a usable source file."""

import io
from pathlib import Path

import harvest
import pytest


class Response(io.BytesIO):
    def __init__(self, payload, length=None):
        super().__init__(payload)
        self.headers = {
            "Content-Length": str(len(payload) if length is None else length)
        }


@pytest.mark.parametrize(
    "payload,length", [(b"<html>failure</html>", None), (b"%PDF-1.4", 100)]
)
def test_invalid_download_preserves_existing_pdf(
    tmp_path, monkeypatch, payload, length
):
    target = tmp_path / "source.pdf"
    target.write_bytes(b"previous")
    monkeypatch.setattr(
        harvest.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: Response(payload, length),
    )
    with pytest.raises(ValueError):
        harvest.fetch("https://example.test/source.pdf", target)
    assert target.read_bytes() == b"previous"
    assert not target.with_suffix(".pdf.part").exists()


def test_complete_pdf_replaces_output_atomically(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[1] / "data/2022/index.pdf"
    payload = source.read_bytes()
    monkeypatch.setattr(
        harvest.urllib.request, "urlopen", lambda *_args, **_kwargs: Response(payload)
    )
    target = tmp_path / "source.pdf"
    assert harvest.fetch("https://example.test/source.pdf", target) == payload
    assert target.read_bytes() == payload
    assert not target.with_suffix(".pdf.part").exists()
