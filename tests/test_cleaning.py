"""Tests for the pure text helpers in :mod:`reader.cleaning`."""

import pytest

from reader import cleaning


class TestCrop:
    def test_keeps_only_what_lies_between_the_markers(self, raw_book):
        cropped = cleaning.crop(raw_book)

        assert cropped.startswith("Produced by")
        assert cropped.endswith("in want of a wife.")
        assert "This ebook is for the use of anyone" not in cropped
        assert "Updated editions" not in cropped

    def test_markers_themselves_are_removed(self, raw_book):
        cropped = cleaning.crop(raw_book)

        assert "START OF THE PROJECT GUTENBERG" not in cropped
        assert "END OF THE PROJECT GUTENBERG" not in cropped

    @pytest.mark.parametrize("marker", ["START OF THIS", "start of the"])
    def test_marker_wording_and_case_vary(self, marker):
        text = f"header\n*** {marker} PROJECT GUTENBERG EBOOK X ***\nbody\n" \
               "*** END OF THE PROJECT GUTENBERG EBOOK X ***\nfooter"

        assert cleaning.crop(text) == "body"

    def test_marker_spanning_several_lines(self):
        text = (
            "header\n*** START OF THE PROJECT GUTENBERG EBOOK\nA VERY LONG TITLE ***\n"
            "body\n*** END OF THE PROJECT GUTENBERG EBOOK A VERY LONG TITLE ***\nfooter"
        )

        assert cleaning.crop(text) == "body"

    def test_missing_start_marker(self):
        text = "body\n*** END OF THE PROJECT GUTENBERG EBOOK X ***\n"

        with pytest.raises(ValueError, match="START marker not found"):
            cleaning.crop(text)

    def test_missing_end_marker(self):
        text = "*** START OF THE PROJECT GUTENBERG EBOOK X ***\nbody\n"

        with pytest.raises(ValueError, match="END marker not found"):
            cleaning.crop(text)


class TestStripCredits:
    @pytest.mark.parametrize(
        "credit",
        [
            "Produced by John Doe",
            "Prepared by John Doe",
            "E-text prepared by John Doe",
            "Transcribed from the 1898 edition by David Price",
            "Produit par Jean Dupont",
            "Scanned by John Doe",
            "This eBook was produced by John Doe",
            "Note du transcripteur",
            "[Produced by John Doe]",
            "(produced by John Doe)",
        ],
    )
    def test_recognised_credit_wordings(self, credit):
        text = f"{credit}\n\nChapter I.\n\nThe body."

        assert cleaning.strip_credits(text) == "Chapter I.\n\nThe body."

    def test_several_leading_credit_blocks(self):
        text = "Produced by A\n\nScanned by B\n\nChapter I."

        assert cleaning.strip_credits(text) == "Chapter I."

    def test_leading_blank_blocks_are_dropped(self):
        text = "\n\n   \n\nProduced by A\n\nChapter I."

        assert cleaning.strip_credits(text) == "Chapter I."

    def test_stops_at_the_first_block_of_actual_text(self):
        text = "Chapter I.\n\nProduced by A\n\nThe body."

        assert cleaning.strip_credits(text) == text

    def test_max_blocks_limits_how_far_credits_are_stripped(self):
        text = "Produced by A\n\nScanned by B\n\nPrepared by C\n\nChapter I."

        assert cleaning.strip_credits(text, max_blocks=2) == "Prepared by C\n\nChapter I."
        assert cleaning.strip_credits(text, max_blocks=4) == "Chapter I."

    def test_max_blocks_counts_blank_blocks_too(self):
        # The first block is empty, so only two credit blocks fit under
        # the default limit of three.
        text = "\n\nProduced by A\n\nScanned by B\n\nPrepared by C\n\nChapter I."

        assert cleaning.strip_credits(text) == "Prepared by C\n\nChapter I."

    def test_paragraph_structure_of_the_body_is_preserved(self):
        text = "Produced by A\n\nChapter I.\n\nFirst.\n\nSecond."

        assert cleaning.strip_credits(text) == "Chapter I.\n\nFirst.\n\nSecond."

    def test_text_without_credits_is_untouched(self):
        text = "Chapter I.\n\nThe body."

        assert cleaning.strip_credits(text) == text


class TestRemoveNewLines:
    def test_collapses_every_run_of_whitespace(self):
        assert cleaning.remove_new_lines("a\n\nb\tc   d\r\ne") == "a b c d e"

    def test_strips_the_edges(self):
        assert cleaning.remove_new_lines("\n  a b  \n\n") == "a b"

    def test_already_flat_text_is_unchanged(self):
        assert cleaning.remove_new_lines("a b c") == "a b c"

    def test_empty_text(self):
        assert cleaning.remove_new_lines("   \n\t ") == ""


class TestClean:
    def test_full_pipeline(self, raw_book):
        assert cleaning.clean(raw_book) == (
            "Chapter I. It is a truth universally acknowledged, that a single "
            "man in possession of a good fortune, must be in want of a wife."
        )

    def test_max_blocks_is_passed_through_to_strip_credits(self):
        text = (
            "*** START OF THE PROJECT GUTENBERG EBOOK X ***\n\n"
            "Produced by A\n\nScanned by B\n\nPrepared by C\n\nChapter I.\n\n"
            "*** END OF THE PROJECT GUTENBERG EBOOK X ***"
        )

        assert "Prepared by C" in cleaning.clean(text, max_blocks=2)
        assert "Prepared by C" not in cleaning.clean(text, max_blocks=4)

    def test_propagates_the_crop_error(self):
        with pytest.raises(ValueError, match="START marker not found"):
            cleaning.clean("no markers here")

    def test_flattening_before_stripping_destroys_the_book(self, raw_book):
        # Why clean() crops, strips and only then flattens: collapsing the
        # line breaks first leaves a single block, which the credits
        # opening it now match in full, so the whole text is dropped.
        flattened = cleaning.remove_new_lines(cleaning.crop(raw_book))

        assert cleaning.strip_credits(flattened) == ""
        assert cleaning.clean(raw_book) != ""
