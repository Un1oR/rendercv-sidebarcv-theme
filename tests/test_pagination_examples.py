"""The gallery's three views must visibly exercise different page-break policies."""

import copy
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops
from ruamel.yaml import YAML

from docs.build_gallery import PAGINATION_CROPS
from tests.support import ROOT


class PaginationExampleTests(unittest.TestCase):
    def render_variant(self, directory, mode):
        work = directory / mode
        work.mkdir()
        shutil.copytree(ROOT / "sidebarcv", work / "sidebarcv")
        shutil.copy2(ROOT / "examples" / "pagination.yaml", work / "cv.yaml")
        shutil.copy2(ROOT / "examples" / f"pagination-{mode}.yaml", work / "design.yaml")
        result = subprocess.run([
            sys.executable, "-m", "rendercv", "render", "cv.yaml",
            "--design", "design.yaml",
        ], cwd=work, capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        pdf, = (work / "rendercv_output").glob("*.pdf")
        xml = subprocess.check_output(["pdftotext", "-bbox", str(pdf), "-"], text=True)
        pages = ET.fromstring(xml).findall(".//{*}page")
        self.assertEqual(len(pages), 2, f"{mode} must demonstrate the page 1 → 2 boundary")
        words = [
            [{"text": word.text, **{key: float(value) for key, value in word.attrib.items()}}
             for word in page.findall(".//{*}word")]
            for page in pages
        ]
        images = []
        for number in range(1, len(pages) + 1):
            with Image.open(pdf.with_name(f"{pdf.stem}_{number}.png")) as image:
                self.assertEqual(image.size, (1224, 1584), "Gallery crops use 144-dpi US-letter pages")
                images.append(image.convert("RGB"))
        return words, images

    def assert_preview_contains(self, page, image, phrases, crop):
        """Check visible ink: PDF font boxes include blank descent below the glyphs."""
        words = [word["text"] for word in page]
        for phrase in phrases:
            tokens = phrase.split()
            starts = [index for index in range(len(words) - len(tokens) + 1)
                      if words[index:index + len(tokens)] == tokens]
            self.assertEqual(len(starts), 1, f"Preview text {phrase!r} must be unique")
            for word in page[starts[0]:starts[0] + len(tokens)]:
                bounds = (math.floor(word["xMin"] * 2), math.floor(word["yMin"] * 2),
                          math.ceil(word["xMax"] * 2), math.ceil(word["yMax"] * 2))
                region = image.crop(bounds)
                ink = ImageChops.difference(region, Image.new("RGB", region.size, "white")).getbbox()
                self.assertIsNotNone(ink, f"{phrase!r} must have visible text")
                self.assertGreaterEqual(bounds[0] + ink[0], crop[0], phrase)
                self.assertGreaterEqual(bounds[1] + ink[1], crop[1], phrase)
                self.assertLessEqual(bounds[0] + ink[2], crop[2], phrase)
                self.assertLessEqual(bounds[1] + ink[3], crop[3], phrase)

    def test_same_content_exposes_section_group_and_inside_group_breaks(self):
        yaml = YAML(typ="safe")
        source = yaml.load(ROOT / "examples" / "pagination.yaml")
        sections = source["cv"]["sections"]
        groups = sections["skills"]
        preceding = [*sections["toolbox"], *sections["languages"]]
        designs = []
        for mode in ["flow", "section", "groups"]:
            design = copy.deepcopy(yaml.load(ROOT / "examples" / f"pagination-{mode}.yaml")["design"])
            options = design["sections"]["overrides"]["skills"]
            options.pop("allow_page_break")
            options.pop("entries")
            designs.append(design)
        self.assertEqual(designs[0], designs[1], "The comparison changes pagination only")
        self.assertEqual(designs[0], designs[2], "The comparison changes pagination only")

        with tempfile.TemporaryDirectory(prefix="sidebarcv-pagination-test-") as directory:
            rendered = {mode: self.render_variant(Path(directory), mode)
                        for mode in ["flow", "section", "groups"]}
        variants = {mode: result[0] for mode, result in rendered.items()}
        images = {mode: result[1] for mode, result in rendered.items()}

        sidebar_left = next(word["xMin"] for page in variants["flow"] for word in page
                            if word["text"] == "Skills")
        group_pages = {}
        sidebar_bottom = {}
        main_columns = []
        for mode, pages in variants.items():
            sidebar = [[word for word in page if word["xMin"] >= sidebar_left - 0.1] for page in pages]
            text = [" ".join(word["text"] for word in page) for page in sidebar]
            group_pages[mode] = {}
            for group in [*preceding, *groups]:
                items = [group["label"], *group["details"].split(", ")]
                item_pages = []
                for item in items:
                    found = [number for number, page in enumerate(text, 1) if item in page]
                    self.assertEqual(len(found), 1, f"{mode}: {item!r} must occur on exactly one page")
                    self.assertEqual(sum(page.count(item) for page in text), 1,
                                     f"{mode}: {item!r} must not be duplicated")
                    item_pages.extend(found)
                group_pages[mode][group["label"]] = set(item_pages)
                if mode == "flow" and group["label"] == "Delivery":
                    self.assertEqual(item_pages, [1] * 5 + [2] * 3,
                                     "Delivery's label and first four items precede the break; three items follow")
            sidebar_bottom[mode] = max(word["yMax"] for word in sidebar[0])
            main_columns.append([
                [(word["text"], word["xMin"], word["yMin"]) for word in page
                 if word["xMin"] < sidebar_left - 0.1]
                for page in pages
            ])

        self.assertEqual(group_pages["flow"]["Delivery"], {1, 2}, "Free flow splits a real skill group")
        self.assertEqual(group_pages["section"], {
            **{group["label"]: {1} for group in preceding},
            **{group["label"]: {2} for group in groups},
        },
                         "Keeping the section moves its complete contents to page 2")
        self.assertEqual(group_pages["groups"], {
            **{group["label"]: {1} for group in preceding}, "Collaboration": {1},
            "Delivery": {2}, "Leadership": {2},
        }, "Group-level control retains useful page-1 content without splitting groups")
        self.assertGreater(sidebar_bottom["flow"] - sidebar_bottom["groups"], 60,
                           "Keeping Delivery leaves a visible gap at the end of page 1")
        self.assertGreater(sidebar_bottom["groups"] - sidebar_bottom["section"], 60,
                           "Keeping the entire section leaves a much larger page-1 gap")
        self.assertEqual(main_columns[0], main_columns[1], "Sidebar policy must not move the main column")
        self.assertEqual(main_columns[0], main_columns[2], "Sidebar policy must not move the main column")

        # The compact previews must show why space is left, not a blank crop of page 1.
        self.assert_preview_contains(variants["section"][0], images["section"][0], [
            "Languages", "English:", "Native", "French:", "Working proficiency",
        ], PAGINATION_CROPS[0])
        collaboration = next(group for group in groups if group["label"] == "Collaboration")
        self.assert_preview_contains(variants["groups"][0], images["groups"][0], [
            collaboration["label"], *collaboration["details"].split(", "),
        ], PAGINATION_CROPS[0])
        delivery = next(group for group in groups if group["label"] == "Delivery")
        self.assert_preview_contains(variants["groups"][1], images["groups"][1], [
            delivery["label"], *delivery["details"].split(", "),
        ], PAGINATION_CROPS[1])
        self.assertGreater(PAGINATION_CROPS[0][3] / 2 - sidebar_bottom["section"], 120,
                           "The section preview must retain its real page-1 whitespace")
        self.assertGreater(PAGINATION_CROPS[0][3] / 2 - sidebar_bottom["groups"], 60,
                           "The groups preview must retain its real page-1 whitespace")
