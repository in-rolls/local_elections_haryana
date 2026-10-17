"""Transcribe 2010 Hindi printings where the English categories are suspect.

The English notifications of seven 2010 blocks print too few women's seats
(`data/2010/reference/category_defects.csv`). Each notification was also published
in Hindi. The Hindi PDFs carry Kruti Dev text that the parser cannot place reliably,
so their pages are transcribed from images with the hosted model already used for
the 2000 gazettes. Responses, usage and request identities are kept for audit.
This is a discovery stage: its output is evidence for reviewing the English
categories and is not a published dataset.
"""

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import tomllib
from pathlib import Path

import requests

from local_elections_haryana.acquire import pilot_hosted as hosted
from local_elections_haryana.paths import ROOT
from local_elections_haryana.source import checksum

BASE = ROOT / "data/discovery/2026-10-17/hindi_printings_2010"
OUT = BASE / "responses"
PROMPT = (
    "This page is a Haryana State Election Commission notification of 2010, printed "
    "in Hindi, listing persons elected Sarpanch and Panch for each gram panchayat. "
    "Transcribe every table row in original top-to-bottom order, keeping Devanagari "
    "as printed. body_raw is the gram panchayat name printed on that row, never a "
    "person's name; repeat nothing that is not printed on the row. ward_raw is only "
    "the printed ward number. winner_raw and relation_raw are the two personal-name "
    "columns. office_raw is the printed office (सरपंच or पंच) or null. category_raw "
    "is the complete category cell exactly as printed, including महिला, or null when "
    "the cell is blank. Do not infer a category from a name or fill gaps. Ignore "
    "mastheads and footnotes. Return only the rows array."
)


def payload(image):
    body = hosted.payload_for(image)
    body["messages"][0]["content"][0]["text"] = PROMPT
    # Transcription needs little reasoning; at "high" a dense page spent the whole
    # output allowance thinking and returned a truncated table.
    body["reasoning_effort"] = "low"
    return body


def render(pdf, page, folder):
    prefix = Path(folder) / f"{pdf.stem}_{page:03d}"
    subprocess.run(
        ["pdftoppm", "-f", str(page), "-l", str(page), "-singlefile", "-scale-to",
         "2000", "-jpeg", "-jpegopt", "quality=85", str(pdf), str(prefix)],
        check=True, capture_output=True, timeout=120,
    )  # fmt: skip
    return prefix.with_suffix(".jpg")


def pages(pdf):
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True)
    return int(
        next(x for x in info.stdout.splitlines() if x.startswith("Pages")).split()[1]
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cap", type=float, default=3.0)
    ap.add_argument("--limit", type=int, help="pages to submit in this stage")
    ap.add_argument("--only", help="restrict to one PDF stem")
    args = ap.parse_args()
    cfg = tomllib.loads(hosted.CONFIG_PATH.read_text())
    client = requests.Session()
    client.headers["Authorization"] = (
        f"Bearer {os.getenv('MODEL_API_KEY') or cfg['meta']['api_key']}"
    )
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [
        (pdf, p)
        for pdf in sorted(BASE.glob("*.pdf"))
        if not args.only or pdf.stem == args.only
        for p in range(1, pages(pdf) + 1)
    ]
    done = 0
    with tempfile.TemporaryDirectory(prefix="hr-hindi-") as folder:
        for pdf, page in jobs:
            label = f"{pdf.stem}_{page:03d}"
            if (OUT / f"response_{label.lower()}.json").exists():
                continue
            if args.limit is not None and done >= args.limit:
                break
            image = render(pdf, page, folder)
            body = payload(image.read_bytes())
            encoded = json.dumps(body, sort_keys=True).encode()
            identity = {
                "label": label,
                "source_sha256": checksum(pdf),
                "source_page": page,
                "image_sha256": checksum(image),
                "request_sha256": hashlib.sha256(encoded).hexdigest(),
                "prompt_sha256": hashlib.sha256(PROMPT.encode()).hexdigest(),
                "model": hosted.MODEL,
                "code_sha256": checksum(Path(__file__)),
            }
            record = hosted.submit_one(
                client, body, identity, OUT, args.cap, max_requests=600,
                allow_empty=True, read_timeout=300,
            )  # fmt: skip
            done += 1
            print(
                label,
                record.get("rows"),
                round(record.get("usage_priced_usd", 0), 4),
                flush=True,
            )


if __name__ == "__main__":
    main()
