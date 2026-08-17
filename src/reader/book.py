"""The :class:`Book` object: one Gutenberg book, downloaded and cleaned."""

import requests

from . import cleaning
from ._catalog import load_catalog

TEXT_URL = "https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt"


class Book:
    """A single Project Gutenberg book, with download and cleaning helpers.

    Parameters
    ----------
    id : int
        Project Gutenberg identifier, matching the ``Text#`` column of the
        catalog.
    read : bool, optional
        Whether to download the text immediately on instantiation.
        Default is True.

    Attributes
    ----------
    id : int
        Project Gutenberg identifier of the book.
    title : str
        Title as listed in the catalog.
    text : str or None
        Current state of the book text. None until :meth:`read_text` is
        called, then progressively modified in place by the cleaning
        methods.

    Raises
    ------
    IndexError
        If the identifier is absent from the catalog.
    """

    def __init__(self, id: int, read: bool = True):
        catalog = load_catalog()
        current = catalog[catalog["Text#"] == id].iloc[0]
        self.title = current["Title"]
        self.id = id
        self.text = None
        if read:
            self.read_text()

    def read_text(self) -> str:
        """Download the plain text of the book from Project Gutenberg.

        The result is cached in :attr:`text`; subsequent calls return it
        without issuing a new request.

        Returns
        -------
        str
            The raw text of the book, Gutenberg header and footer included.

        Raises
        ------
        FileNotFoundError
            If the server does not answer with HTTP 200, typically because
            no plain-text version exists for this identifier.
        """
        if self.text is not None:
            return self.text
        response = requests.get(TEXT_URL.format(id=self.id))
        if response.status_code != 200:
            raise FileNotFoundError(f"{self.id} : HTTP {response.status_code}")
        response.encoding = "utf-8"
        self.text = response.text
        return self.text

    def remove_new_lines(self) -> str:
        """Collapse every run of whitespace into a single space.

        See :func:`reader.cleaning.remove_new_lines`.

        Returns
        -------
        str
            The flattened text, also stored in :attr:`text`.
        """
        self.text = cleaning.remove_new_lines(self.text)
        return self.text

    def crop(self) -> str:
        """Keep only what lies between the Gutenberg start and end markers.

        See :func:`reader.cleaning.crop`.

        Returns
        -------
        str
            The cropped text, also stored in :attr:`text`.

        Raises
        ------
        ValueError
            If either marker is missing from the text.
        """
        try:
            self.text = cleaning.crop(self.text)
        except ValueError as error:
            raise ValueError(f"{self.id} : {error}") from None
        return self.text

    def strip_credits(self, max_blocks: int = 3) -> str:
        """Drop the transcriber and production credits opening the book.

        See :func:`reader.cleaning.strip_credits`.

        Parameters
        ----------
        max_blocks : int, optional
            How many leading blocks may be inspected for credits.
            Default is 3.

        Returns
        -------
        str
            The text without its opening credits, also stored in
            :attr:`text`.
        """
        self.text = cleaning.strip_credits(self.text, max_blocks)
        return self.text

    def clean(self) -> str:
        """Run the full cleaning pipeline on the text.

        Applies :meth:`crop`, :meth:`strip_credits` and
        :meth:`remove_new_lines` in that order. The order matters: once
        line breaks are collapsed, block boundaries no longer exist and
        credits can no longer be located.

        Returns
        -------
        str
            The cleaned text, also stored in :attr:`text`.

        Raises
        ------
        ValueError
            Propagated from :meth:`crop` when a marker is missing.
        """
        self.crop()
        self.strip_credits()
        self.remove_new_lines()
        return self.text

    def save(self, path: str):
        """Write the current text to a UTF-8 file.

        Parameters
        ----------
        path : str
            Destination path. Its parent directory must already exist.
        """
        with open(path, "w", encoding="utf-8") as file:
            file.write(self.text)

    def __str__(self) -> str:
        """Return the current text.

        Returns
        -------
        str
            The value of :attr:`text`.
        """
        return self.text
