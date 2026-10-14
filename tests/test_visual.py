"""Public examples cover CLI installation, complete outputs, and visual regression."""

from pathlib import Path
import tempfile
import unittest

from PIL import Image, ImageChops, ImageDraw

from tests.visual import check_content, check_example, compare_page


class VisualTests(unittest.TestCase):
    def test_starter(self):
        check_example("starter")

    def test_john(self):
        check_example("john")

    def test_alice(self):
        check_example("alice")

    def test_bob(self):
        check_example("bob")


class ComparatorTests(unittest.TestCase):
    def test_content_check_handles_markup_and_nested_highlights_without_losing_words(self):
        data = {"cv": {"name": "Sample Name", "sections": {"experience": [{
            "company": "Company", "summary": None,
            "highlights": ["Main **point** - Child item"],
        }]}}}
        markdown = "Sample Name\nCompany\n- Main **point**\n  - Child item"
        html = "<h1>Sample Name</h1><p>Company</p><ul><li>Main <strong>point</strong></li><li>Child item</li></ul>"
        check_content(data, markdown, html)
        with self.assertRaisesRegex(AssertionError, "HTML lost content"):
            check_content(data, markdown, html.replace("Child item", "Child"))

    def test_tolerance_accepts_small_noise_but_rejects_one_pixel_displacement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected, actual, diff = (root / name for name in ["expected.png", "actual.png", "diff.png"])
            source = Image.new("RGB", (20, 20), (250, 250, 250))
            ImageDraw.Draw(source).rectangle((5, 5, 10, 10), fill=(10, 10, 10))
            source.save(expected)
            source.point(lambda channel: channel + 2).save(actual)
            compare_page(expected, actual, diff)
            ImageChops.offset(source, 1, 0).save(actual)
            with self.assertRaisesRegex(AssertionError, "pixels exceed"):
                compare_page(expected, actual, diff)
            self.assertTrue(diff.exists())
            source.putpixel((0, 0), (0, 0, 0))
            source.save(actual)
            with self.assertRaisesRegex(AssertionError, "1 pixels exceed"):
                compare_page(expected, actual, diff)
            Image.new("RGB", (20, 21), "white").save(actual)
            with self.assertRaisesRegex(AssertionError, "Page size changed"):
                compare_page(expected, actual, diff)
