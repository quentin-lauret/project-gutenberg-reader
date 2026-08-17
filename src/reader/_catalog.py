"""Access to the Project Gutenberg catalog.

The catalog is a single CSV listing every Gutenberg entry. It is fetched
on first use and kept in memory afterwards, so importing the package
costs nothing until a catalog lookup actually happens.

The module is private so that the package can expose the loaded
``DataFrame`` itself as ``reader.catalog``; the entry points here are
re-exported by :mod:`reader`.
"""

import pandas as pd

CATALOG_URL = "https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv"

_catalog = None


def load_catalog(url: str = CATALOG_URL, force: bool = False) -> pd.DataFrame:
    """Return the Gutenberg catalog as a :class:`pandas.DataFrame`.

    The first call downloads the CSV; later calls return the cached
    frame without hitting the network.

    Parameters
    ----------
    url : str, optional
        Where to read the CSV from. Defaults to :data:`CATALOG_URL`; a
        local path also works.
    force : bool, optional
        Re-read the CSV even if a catalog is already cached.
        Default is False.

    Returns
    -------
    pandas.DataFrame
        One row per Gutenberg entry, keyed by the ``Text#`` column.
    """
    global _catalog
    if _catalog is None or force:
        _catalog = pd.read_csv(url)
    return _catalog


def set_catalog(catalog):
    """Install an already-built catalog as the cached one.

    Useful to work from a local copy of the CSV, and to keep tests off
    the network.

    Parameters
    ----------
    catalog : pandas.DataFrame or None
        Frame to use, expected to hold at least the ``Text#`` and
        ``Title`` columns. Passing None clears the cache, so the next
        :func:`load_catalog` downloads the CSV again.

    Returns
    -------
    pandas.DataFrame or None
        The value that was just installed.
    """
    global _catalog
    _catalog = catalog
    return _catalog
