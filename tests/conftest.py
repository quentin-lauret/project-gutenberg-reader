"""Shared fixtures.

Nothing in the suite touches the network: the catalog is replaced by a
small in-memory frame, and ``requests.get`` is monkeypatched wherever a
download is involved.
"""

import pandas as pd
import pytest

import reader

CATALOG_ROWS = [
    {"Text#": 1342, "Type": "Text", "Title": "Pride and Prejudice", "Language": "en"},
    {"Text#": 796, "Type": "Text", "Title": "La Chartreuse De Parme", "Language": "fr"},
]

RAW_BOOK = """The Project Gutenberg eBook of Pride and Prejudice

This ebook is for the use of anyone anywhere in the United States.

*** START OF THE PROJECT GUTENBERG EBOOK PRIDE AND PREJUDICE ***

Produced by Anonymous Volunteers, and David Widger

Chapter I.

It is a truth universally acknowledged, that a single man in
possession of a good fortune, must be in want of a wife.

*** END OF THE PROJECT GUTENBERG EBOOK PRIDE AND PREJUDICE ***

Updated editions will replace the previous one.
"""


@pytest.fixture
def raw_book():
    """A short book with the exact shape of a Gutenberg plain-text file."""
    return RAW_BOOK


@pytest.fixture(autouse=True)
def fake_catalog():
    """Install a two-row catalog for the duration of a test."""
    catalog = pd.DataFrame(CATALOG_ROWS)
    reader.set_catalog(catalog)
    yield catalog
    reader.set_catalog(None)


class FakeResponse:
    """Minimal stand-in for :class:`requests.Response`."""

    def __init__(self, text: str = "", status_code: int = 200):
        self.text = text
        self.status_code = status_code
        self.encoding = None


class FakeDownload:
    """The response served to :meth:`Book.read_text`, plus the URLs asked for."""

    def __init__(self, response: FakeResponse):
        self.response = response
        self.calls = []


@pytest.fixture
def fake_get(monkeypatch):
    """Replace ``requests.get`` with one always serving the same response.

    Returns a callable taking the body and status code to serve, and
    giving back the :class:`FakeDownload` recording the requested URLs.
    """
    def install(text: str = "", status_code: int = 200) -> FakeDownload:
        download = FakeDownload(FakeResponse(text, status_code))

        def get(url, *args, **kwargs):
            download.calls.append(url)
            return download.response

        monkeypatch.setattr(reader.book.requests, "get", get)
        return download

    return install
