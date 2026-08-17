"""Download and clean Project Gutenberg books.

    >>> from reader import Book
    >>> book = Book(1342)
    >>> book.clean()

The module-level ``catalog`` is the Gutenberg catalog as a pandas
``DataFrame``. It is downloaded on first access rather than on import,
so ``import reader`` never touches the network by itself.
"""

from ._catalog import CATALOG_URL, load_catalog, set_catalog
from .book import Book

__all__ = ["Book", "catalog", "load_catalog", "set_catalog", "CATALOG_URL"]


def __getattr__(name: str):
    """Resolve ``reader.catalog`` lazily, downloading it on first access."""
    if name == "catalog":
        return load_catalog()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(__all__)
