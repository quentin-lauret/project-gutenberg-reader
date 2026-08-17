"""Pure text-cleaning helpers.

Every function here takes a string and returns a string, without touching
the network or any global state. :class:`reader.book.Book` wraps them so
they can be applied to a downloaded book in place.
"""

import re

START = re.compile(r"\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", re.S | re.I)
END = re.compile(r"\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", re.S | re.I)
CREDITS = re.compile(
    r"^\s*[\[(]?\s*(produced by|prepared by|e?-?text prepared by|transcribed (from|by)"
    r"|produit par|scanned by|this (e?-?text|file|ebook)|note[s]? (du|de la) transcript)",
    re.I,
)


def crop(text: str) -> str:
    """Keep only what lies between the Gutenberg start and end markers.

    Removes the legal header and footer that Project Gutenberg wraps
    around every book.

    Parameters
    ----------
    text : str
        Raw text of a Gutenberg book.

    Returns
    -------
    str
        The text between the two markers, stripped.

    Raises
    ------
    ValueError
        If either marker is missing from the text.
    """
    beg_marker = START.search(text)
    if beg_marker is None:
        raise ValueError("START marker not found")
    end_marker = END.search(text)
    if end_marker is None:
        raise ValueError("END marker not found")
    return text[beg_marker.end():end_marker.start()].strip()


def strip_credits(text: str, max_blocks: int = 3) -> str:
    """Drop the transcriber and production credits opening the book.

    Blocks are examined only until the first one that is neither empty
    nor a credits block, so a later occurrence in the body of the book
    is left untouched.

    Parameters
    ----------
    text : str
        Text whose blocks are separated by blank lines.
    max_blocks : int, optional
        How many leading blocks may be inspected for credits.
        Default is 3.

    Returns
    -------
    str
        The text without its opening credits.
    """
    blocks = re.split(r"\n\s*\n", text)
    kept = []
    for i, b in enumerate(blocks):
        if not kept:
            if not b.strip():
                continue
            if i < max_blocks and CREDITS.search(b.strip()):
                continue
        kept.append(b)
    return "\n\n".join(kept).strip()


def remove_new_lines(text: str) -> str:
    """Collapse every run of whitespace into a single space.

    Line breaks, tabs and repeated spaces are all replaced, so the text
    becomes one continuous block. Paragraph boundaries are lost, which
    is why this must run after :func:`strip_credits`.

    Parameters
    ----------
    text : str
        Text to flatten.

    Returns
    -------
    str
        The flattened text.
    """
    return re.sub(r"\s+", " ", text).strip()


def clean(text: str, max_blocks: int = 3) -> str:
    """Run the full cleaning pipeline on a raw book text.

    Applies :func:`crop`, :func:`strip_credits` and
    :func:`remove_new_lines` in that order. The order matters: once line
    breaks are collapsed, block boundaries no longer exist and credits
    can no longer be located.

    Parameters
    ----------
    text : str
        Raw text of a Gutenberg book.
    max_blocks : int, optional
        Passed through to :func:`strip_credits`. Default is 3.

    Returns
    -------
    str
        The cleaned text.

    Raises
    ------
    ValueError
        Propagated from :func:`crop` when a marker is missing.
    """
    return remove_new_lines(strip_credits(crop(text), max_blocks))
