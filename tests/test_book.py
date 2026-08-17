"""Tests for :class:`reader.Book`."""

import pytest

from reader import Book


class TestInit:
    def test_reads_the_title_from_the_catalog(self, fake_get, raw_book):
        fake_get(raw_book)

        assert Book(1342).title == "Pride and Prejudice"
        assert Book(796).title == "La Chartreuse De Parme"

    def test_downloads_on_instantiation_by_default(self, fake_get, raw_book):
        download = fake_get(raw_book)

        book = Book(1342)

        assert book.text == raw_book
        assert download.calls == ["https://www.gutenberg.org/cache/epub/1342/pg1342.txt"]

    def test_read_false_defers_the_download(self, fake_get, raw_book):
        download = fake_get(raw_book)

        book = Book(1342, read=False)

        assert book.text is None
        assert download.calls == []

    def test_unknown_identifier(self, fake_get, raw_book):
        fake_get(raw_book)

        with pytest.raises(IndexError):
            Book(999999)


class TestReadText:
    def test_returns_the_downloaded_text(self, fake_get, raw_book):
        fake_get(raw_book)

        assert Book(1342, read=False).read_text() == raw_book

    def test_forces_utf8_decoding(self, fake_get, raw_book):
        download = fake_get(raw_book)

        Book(1342)

        assert download.response.encoding == "utf-8"

    def test_second_call_does_not_hit_the_network(self, fake_get, raw_book):
        download = fake_get(raw_book)
        book = Book(1342)

        assert book.read_text() == raw_book
        assert len(download.calls) == 1

    def test_cleaned_text_is_not_re_downloaded(self, fake_get, raw_book):
        download = fake_get(raw_book)
        book = Book(1342)
        cleaned = book.clean()

        assert book.read_text() == cleaned
        assert len(download.calls) == 1

    @pytest.mark.parametrize("status", [404, 403, 500])
    def test_non_200_response(self, fake_get, status):
        fake_get("Not found", status_code=status)

        with pytest.raises(FileNotFoundError, match=f"1342 : HTTP {status}"):
            Book(1342)


class TestCleaningMethods:
    @pytest.fixture
    def book(self, fake_get, raw_book):
        fake_get(raw_book)
        return Book(1342)

    def test_crop_stores_and_returns_the_same_text(self, book):
        assert book.crop() == book.text
        assert book.text.startswith("Produced by")

    def test_strip_credits_stores_and_returns_the_same_text(self, book):
        book.crop()

        assert book.strip_credits() == book.text
        assert book.text.startswith("Chapter I.")

    def test_remove_new_lines_stores_and_returns_the_same_text(self, book):
        assert book.remove_new_lines() == book.text
        assert "\n" not in book.text

    def test_clean_runs_the_whole_pipeline(self, book):
        assert book.clean() == (
            "Chapter I. It is a truth universally acknowledged, that a single "
            "man in possession of a good fortune, must be in want of a wife."
        )

    def test_clean_is_the_same_as_chaining_the_three_methods(self, book):
        other = Book(1342)
        other.crop()
        other.strip_credits()
        other.remove_new_lines()

        assert book.clean() == other.text

    def test_strip_credits_forwards_max_blocks(self, book):
        book.crop()

        assert "Produced by" in book.strip_credits(max_blocks=0)

    def test_crop_error_names_the_book(self, fake_get):
        fake_get("no markers here")
        book = Book(1342)

        with pytest.raises(ValueError, match=r"1342 : START marker not found"):
            book.crop()

    def test_clean_propagates_the_crop_error(self, fake_get):
        fake_get("no markers here")
        book = Book(1342)

        with pytest.raises(ValueError, match=r"1342 : START marker not found"):
            book.clean()

    def test_failed_crop_leaves_the_text_untouched(self, fake_get):
        fake_get("no markers here")
        book = Book(1342)

        with pytest.raises(ValueError):
            book.clean()
        assert book.text == "no markers here"


class TestSave:
    def test_writes_the_current_text_as_utf8(self, tmp_path, fake_get):
        fake_get("caractères accentués")
        path = tmp_path / "book.txt"

        Book(1342).save(str(path))

        assert path.read_text(encoding="utf-8") == "caractères accentués"

    def test_writes_the_cleaned_text_after_clean(self, tmp_path, fake_get, raw_book):
        fake_get(raw_book)
        book = Book(1342)
        book.clean()
        path = tmp_path / "book.txt"

        book.save(str(path))

        assert path.read_text(encoding="utf-8") == book.text

    def test_overwrites_an_existing_file(self, tmp_path, fake_get):
        fake_get("new")
        path = tmp_path / "book.txt"
        path.write_text("much longer previous content", encoding="utf-8")

        Book(1342).save(str(path))

        assert path.read_text(encoding="utf-8") == "new"


class TestStr:
    def test_returns_the_current_text(self, fake_get, raw_book):
        fake_get(raw_book)
        book = Book(1342)

        assert str(book) == raw_book

        book.clean()
        assert str(book) == book.text
