"""Gallery page selection and temporary hero inputs."""

from pathlib import Path
import tempfile
import unittest

from docs.build_gallery import page_pngs, prepare_example
from ruamel.yaml import YAML


class GalleryTests(unittest.TestCase):
    def test_pages_exclude_copied_portrait_and_sort_numerically(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("Alice_CV_10.png", "Alice_CV_2.png", "Alice_CV_1.png",
                         "alice-portrait.png", "Alice_CV_portrait.png", "Other_CV_1.png"):
                (root / name).touch()
            self.assertEqual([path.name for path in page_pngs(root / "Alice_CV.pdf")],
                             ["Alice_CV_1.png", "Alice_CV_2.png", "Alice_CV_10.png"])

    def test_hero_changes_only_photo_and_section_break_in_temporary_input(self):
        original = 'cv:\n  name: Alice\n  photo: portrait.png\n  sections:\n    summary: ["Same content"]\ndesign:\n  theme: sidebarcv\n  sections:\n    overrides:\n      skills:\n        allow_page_break: false\n        entries:\n          allow_page_break: false\n'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "alice.yaml"
            source.write_text(original, encoding="utf-8")
            (root / "portrait.png").write_bytes(b"portrait")
            for name in ("gallery", "hero"):
                work = root / name
                work.mkdir()
                prepare_example(source, work / "cv.yaml", hero=name == "hero")
            expected = YAML(typ="safe").load(original)
            expected["cv"].pop("photo")
            expected["design"]["sections"]["overrides"]["skills"]["allow_page_break"] = True
            self.assertEqual(YAML(typ="safe").load(root / "hero/cv.yaml"), expected)
            self.assertFalse((root / "hero/portrait.png").exists())
            self.assertEqual((root / "gallery/cv.yaml").read_text(encoding="utf-8"), original)
            self.assertEqual((root / "gallery/portrait.png").read_bytes(), b"portrait")
            self.assertEqual(source.read_text(encoding="utf-8"), original)

if __name__ == "__main__":
    unittest.main()
