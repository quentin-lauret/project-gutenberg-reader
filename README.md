# Project Gutenberg Reader

Downloads a book from [Project Gutenberg](https://www.gutenberg.org/) and cleans
its text: strips the legal header and footer, the transcription credits, and
normalises whitespace.

## Installation

```bash
pip install .
```

In development mode (changes under `src/reader/` are picked up without
reinstalling):

```bash
pip install -e .
```

Dependencies (`pandas`, `requests`) are installed automatically.

## Usage

```python
from reader import Book

book = Book(1342)          # Gutenberg identifier (Text#), here Pride and Prejudice
print(book.title)

book.clean()               # crop + strip_credits + remove_new_lines
book.save("pride.txt")
```

The identifier is the `Text#` column of the Gutenberg catalog, which is
downloaded the first time it is needed.

### The catalog

The first catalog lookup - creating a `Book`, or reading `reader.catalog` -
downloads
[`pg_catalog.csv`](https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv)
into a pandas `DataFrame` named `catalog` and keeps it in memory afterwards, so
`import reader` itself never touches the network. About 79,000 rows, one per
Gutenberg entry. Every column is a string except `Text#`.

| Column | Description |
| --- | --- |
| `Text#` | Gutenberg identifier (`int`). The value passed to `Book(...)`, and the one used to build the download URL |
| `Type` | Media type. `Text` for the vast majority, but also `Sound`, `Image`, `Dataset`, `MovingImage`, `Collection`, `StillImage` |
| `Issued` | Date the entry was published on Gutenberg, `YYYY-MM-DD` - a string, not a `datetime` |
| `Title` | Title, sometimes spanning several lines in the original CSV |
| `Language` | ISO 639-1 code (`en`, `fr`, `de`, …). Multilingual entries hold several codes separated by `; ` |
| `Authors` | `Surname, First name, birth-death`, several authors separated by `; `. Empty for ~165 entries |
| `Subjects` | Library of Congress subject headings separated by `; `, each using ` -- ` to separate facets |
| `LoCC` | Library of Congress classification code (`PQ` for Romance literature, `PR` for English literature, …) |
| `Bookshelves` | Gutenberg thematic shelves separated by `; `. Empty for ~3,300 entries |

An example row, `catalog[catalog["Text#"] == 796].iloc[0]`:

| Column | Value |
| --- | --- |
| `Text#` | `796` |
| `Type` | `Text` |
| `Issued` | `1997-01-01` |
| `Title` | `La Chartreuse De Parme` |
| `Language` | `fr` |
| `Authors` | `Stendhal, 1783-1842` |
| `Subjects` | `Love stories; Political fiction; Parma (Italy) -- Fiction; Italy -- Social life and customs -- 19th century -- Fiction; Young men -- Italy -- Parma -- Fiction` |
| `LoCC` | `PQ` |
| `Bookshelves` | `Best Books Ever Listings; FR Littérature; Category: Historical Novels; Category: Novels; Category: French Literature` |

Because the multi-valued columns are plain strings, filtering on them means
substring matching rather than equality:

```python
novels = catalog[catalog["Bookshelves"].str.contains("Category: Novels", na=False)]
stendhal = catalog[catalog["Authors"].str.contains("Stendhal", na=False)]
```

The `na=False` argument matters - `Authors`, `Subjects`, `LoCC` and
`Bookshelves` all have missing values, and `str.contains` yields `NaN` for
those, which cannot be used as a boolean mask.

### Downloading a whole corpus

The catalog is a pandas `DataFrame` exposed by the module, so books can be
filtered and then downloaded in bulk - here every French-language work:

```python
import os
import time

from reader import Book, catalog

os.makedirs("books", exist_ok=True)

french_catalog = catalog[catalog["Language"] == "fr"]

i = 0
for _, row in french_catalog.iterrows():
    book_id = row["Text#"]
    print(f"Downloading book {book_id}...")
    try:
        book = Book(book_id)
        book.clean()
    except Exception as e:
        print(f"Error while downloading book {book_id} | {e}")
        continue
    book.save(f"books/{i}.txt")
    i += 1
    time.sleep(0.1)
```

The `try`/`except` is needed: not every book has a plain-text version
(`FileNotFoundError`) and some lack the expected Gutenberg markers
(`ValueError`). The counter `i` only advances on successful downloads, so the
resulting files are numbered without gaps. The `time.sleep` call keeps the
loop from hammering the Gutenberg servers.

Mind the volume: the catalog holds 4,142 French entries (out of 79,000
overall), meaning as many HTTP requests. For a quick trial, filter further or
truncate with `french_catalog.head(10)`.

Nine of those French entries are audio recordings rather than books; they simply
fail the download and get caught by the `except`. Adding
`& (catalog["Type"] == "Text")` to the filter skips them upfront.

### Cleaning steps

`clean()` chains the three methods below, in this order - which matters: once
line breaks are collapsed, credit blocks can no longer be identified.

| Method | Effect |
| --- | --- |
| `crop()` | Keeps only the text between the `*** START OF ... ***` and `*** END OF ... ***` markers |
| `strip_credits()` | Removes the transcription credit blocks at the top of the text |
| `remove_new_lines()` | Replaces every run of whitespace and line breaks with a single space |

Each method can also be called on its own; it modifies `book.text` in place and
returns the result.

The same three steps exist as plain string functions in `reader.cleaning`, for
text that did not come from a `Book`:

```python
from reader import cleaning

cleaned = cleaning.clean(raw_text)   # crop + strip_credits + remove_new_lines
```

### Errors

- `FileNotFoundError` - no plain-text version exists for this identifier.
- `ValueError` - one of the two Gutenberg markers is missing from the text.

## Contributing

Contributions are welcome, and the cleaning heuristics in particular get better
the more books people run them against.

### Development setup

```bash
git clone git@github.com:quentin-lauret/project-gutenberg-reader.git
cd project-gutenberg-reader
pip install -e ".[test]"
```

### Layout

| Path | Contents |
| --- | --- |
| `src/reader/book.py` | The `Book` class: download, clean, save |
| `src/reader/cleaning.py` | The cleaning steps as pure string functions, plus the regexes they use |
| `src/reader/_catalog.py` | Catalog loading and caching |
| `tests/` | The test suite |

### Tests

```bash
pytest
```

The suite never touches the network: the catalog is replaced by a small
in-memory frame and `requests.get` is stubbed out, both from fixtures in
`tests/conftest.py`. New cleaning heuristics belong in `tests/test_cleaning.py`,
where they can be exercised on a text literal rather than on a download.

### Pull requests

Work on a branch, keep one topic per pull request, and say which books you
tested against - the `Text#` values are enough. Docstrings follow the NumPy
style already used throughout the package.

Be considerate of the Project Gutenberg servers while testing: keep a delay
between requests and avoid re-downloading books you already have.
