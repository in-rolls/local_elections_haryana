"""Checksums and links from saved historical index pages."""

import hashlib
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit


class IndexLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active = False
        self.heading = ""
        self.capture = None
        self.parts = []
        self.href = ""
        self.links = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "h1":
            self.active = True
        if tag == "footer":
            self.active = False
        if self.active and tag in {"h1", "h2", "h3", "a"}:
            self.capture = tag
            self.parts = []
            self.href = attributes.get("href", "")

    def handle_data(self, data):
        if self.capture and self.active:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag != self.capture:
            return
        label = " ".join(" ".join(self.parts).split())
        if tag == "a" and self.href:
            self.links.append(
                {"href": self.href, "label": label, "heading": self.heading}
            )
        elif tag in {"h1", "h2", "h3"}:
            self.heading = label
        self.capture = None


def links_from_html(body, base_url):
    parser = IndexLinks()
    parser.feed(body)
    return [
        {**link, "url": urljoin(base_url, link["href"])}
        for link in parser.links
        if not link["href"].startswith("#")
        and urlsplit(urljoin(base_url, link["href"])).scheme in {"http", "https"}
    ]


def checksum(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()
