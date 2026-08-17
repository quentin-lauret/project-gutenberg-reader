"""Tests for catalog loading and for the package's public surface."""

import pandas as pd
import pytest

import reader

CSV = "Text#,Type,Title,Language\n1,Text,A Book,en\n2,Text,Un Livre,fr\n"


@pytest.fixture
def csv_path(tmp_path):
    """A local stand-in for ``pg_catalog.csv``."""
    path = tmp_path / "pg_catalog.csv"
    path.write_text(CSV, encoding="utf-8")
    return str(path)


class TestLoadCatalog:
    def test_reads_the_csv(self, csv_path):
        reader.set_catalog(None)

        catalog = reader.load_catalog(csv_path)

        assert list(catalog.columns) == ["Text#", "Type", "Title", "Language"]
        assert catalog["Text#"].tolist() == [1, 2]

    def test_result_is_cached(self, csv_path):
        reader.set_catalog(None)
        first = reader.load_catalog(csv_path)

        assert reader.load_catalog("/does/not/exist.csv") is first

    def test_force_re_reads(self, csv_path):
        reader.set_catalog(None)
        first = reader.load_catalog(csv_path)

        second = reader.load_catalog(csv_path, force=True)

        assert second is not first
        assert second.equals(first)

    def test_set_catalog_installs_a_frame(self):
        frame = pd.DataFrame([{"Text#": 7, "Title": "Injected"}])

        assert reader.set_catalog(frame) is frame
        assert reader.load_catalog() is frame

    def test_set_catalog_none_clears_the_cache(self, csv_path):
        reader.set_catalog(pd.DataFrame([{"Text#": 7, "Title": "Injected"}]))

        reader.set_catalog(None)

        assert reader.load_catalog(csv_path)["Title"].tolist() == ["A Book", "Un Livre"]

    def test_default_url_points_at_gutenberg(self):
        assert reader.CATALOG_URL == (
            "https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv"
        )


class TestPackageSurface:
    def test_catalog_attribute_is_the_loaded_frame(self, fake_catalog):
        assert reader.catalog is fake_catalog

    def test_catalog_attribute_is_resolved_lazily(self, monkeypatch):
        # Importing the package must not download anything; the CSV is
        # read only when reader.catalog is first touched.
        reader.set_catalog(None)
        frame = pd.DataFrame([{"Text#": 1, "Title": "Lazy"}])
        calls = []
        monkeypatch.setattr(
            reader._catalog.pd,
            "read_csv",
            lambda url, *args, **kwargs: (calls.append(url), frame)[1],
        )

        assert calls == []
        assert reader.catalog is frame
        assert calls == [reader.CATALOG_URL]

    def test_unknown_attribute(self):
        with pytest.raises(AttributeError, match="no attribute 'nope'"):
            reader.nope

    def test_public_names_all_resolve(self):
        assert "catalog" in dir(reader)
        for name in reader.__all__:
            assert getattr(reader, name) is not None
