"""Top gallery CVs must visibly demonstrate all three sidebar break policies."""

from collections import defaultdict
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

from ruamel.yaml import YAML

from tests.support import ROOT


def visible_text(value):
    """Ignore inline markup, punctuation and wrapping when checking PDF content."""
    value = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", str(value))
    return "".join(character for character in value.casefold() if character.isalnum())


class GalleryPaginationTests(unittest.TestCase):
    def render_example(self, name):
        data = YAML(typ="safe").load(ROOT / "examples" / f"{name}.yaml")
        with tempfile.TemporaryDirectory(prefix=f"sidebarcv-gallery-{name}-") as directory:
            work = Path(directory)
            shutil.copytree(ROOT / "sidebarcv", work / "sidebarcv")
            shutil.copy2(ROOT / "examples" / f"{name}.yaml", work / "cv.yaml")
            if photo := data["cv"].get("photo"):
                shutil.copy2(ROOT / "examples" / photo, work / photo)
            result = subprocess.run([
                sys.executable, "-m", "rendercv", "render", "cv.yaml", "--dont-generate-png",
            ], cwd=work, capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            pdf, = (work / "rendercv_output").glob("*.pdf")
            xml = subprocess.check_output(["pdftotext", "-bbox", str(pdf), "-"], text=True)
            text = subprocess.check_output(["pdftotext", "-raw", str(pdf), "-"], text=True)
        pages = ET.fromstring(xml).findall(".//{*}page")
        text = re.sub(re.escape(data["cv"]["name"]) + r"\s*[–-]\s*\d+\s*/\s*\d+", "", text)
        actual = visible_text(text)
        fields = {"name", "company", "position", "institution", "area", "degree", "title",
                  "label", "details", "summary", "bullet", "number", "reversed_number", "tags"}
        for section, entries in data["cv"]["sections"].items():
            options = data["design"].get("sections", {}).get("overrides", {}).get(section, {})
            for entry in entries:
                values = [entry] if isinstance(entry, str) else [
                    value for key, value in entry.items()
                    if key in fields and value is not None and not (key == "details" and options.get("stacked_details"))
                ] + (entry.get("highlights") or []) + (entry.get("authors") or [])
                if isinstance(entry, dict) and options.get("stacked_details") and "details" in entry:
                    values.extend(entry["details"].split(options.get("stacked_separator", ",")))
                for value in values:
                    self.assertIn(visible_text(value), actual, f"{name}: PDF lost body content {value!r}")
        return data, pages

    def sidebar_lines(self, pages, section):
        heading = section.title()
        start_page, heading_word = next((number, word) for number, page in enumerate(pages, 1)
                                       for word in page.findall(".//{*}word") if word.text == heading)
        sidebar_left = float(heading_word.attrib["xMin"])
        lines = []
        for number, page in enumerate(pages, 1):
            rows = defaultdict(list)
            for word in page.findall(".//{*}word"):
                in_section = number > start_page or (number == start_page and
                             float(word.attrib["yMin"]) >= float(heading_word.attrib["yMin"]))
                if in_section and float(word.attrib["xMin"]) >= sidebar_left - 0.1:
                    rows[round(float(word.attrib["yMin"]), 2)].append(word.text)
            page_lines = [" ".join(words) for _, words in sorted(rows.items())]
            lines.append(page_lines)
        return lines, sidebar_left

    def group_pages(self, data, pages, section):
        lines, sidebar_left = self.sidebar_lines(pages, section)
        texts = [" ".join(page_lines).casefold() for page_lines in lines]
        separator = data["design"]["sections"]["overrides"][section].get("stacked_separator", ",")
        locations = {}
        for group in data["cv"]["sections"][section]:
            label = group["label"]
            found = [number for number, page_lines in enumerate(lines, 1) if label in page_lines]
            self.assertEqual(len(found), 1, f"{label}: group heading must occur once")
            item_pages = found[:]
            for item in group["details"].split(separator):
                pattern = re.compile(r"(?<!\w)" + re.escape(item.strip().casefold()) + r"(?!\w)")
                occurrences = [number for number, text in enumerate(texts, 1) if pattern.search(text)]
                self.assertEqual(len(occurrences), 1, f"{label}: each item belongs to exactly one page")
                self.assertEqual(sum(len(pattern.findall(text)) for text in texts), 1,
                                 f"{label}: sidebar items must not be lost or duplicated")
                item_pages.extend(occurrences)
            locations[label] = item_pages
        return locations, sidebar_left

    def test_john_uses_only_theme_defaults_and_keeps_inline_entries_together(self):
        data, pages = self.render_example("john")
        self.assertEqual(data["design"], {"theme": "sidebarcv"}, "The defaults example must have no design overrides")
        self.assertEqual(len(pages), 3)
        lines, _ = self.sidebar_lines(pages, "skills")
        texts = [visible_text(" ".join(page_lines)) for page_lines in lines]
        locations = {}
        for entry in data["cv"]["sections"]["skills"]:
            complete_entry = visible_text(f"{entry['label']} {entry['details']}")
            found = [number for number, text in enumerate(texts, 1) if complete_entry in text]
            self.assertEqual(len(found), 1, f"{entry['label']}: its label and all details must stay on one page")
            self.assertEqual(sum(text.count(complete_entry) for text in texts), 1)
            locations[entry["label"]] = found[0]
        self.assertEqual(locations, {
            "Languages": 1, "ML Frameworks": 1, "Infrastructure": 1, "Research Areas": 2,
        }, "Default inline entries visibly cross the page boundary without splitting")

    def test_alice_moves_the_whole_skills_section(self):
        data, pages = self.render_example("alice")
        self.assertEqual(len(pages), 2)
        locations, sidebar_left = self.group_pages(data, pages, "skills")
        self.assertTrue(all(set(numbers) == {2} for numbers in locations.values()))
        self.assertTrue(any(word.text == "Skills" for word in pages[1].findall(".//{*}word")))
        last_sidebar_word = max(float(word.attrib["yMax"]) for word in pages[0].findall(".//{*}word")
                                if float(word.attrib["xMin"]) >= sidebar_left - 0.1)
        self.assertLess(last_sidebar_word, 450, "Keeping Skills must leave a visible page-1 sidebar gap")

    def test_bob_splits_inside_the_tools_group(self):
        data, pages = self.render_example("bob")
        self.assertEqual(len(pages), 2)
        locations, _ = self.group_pages(data, pages, "methods")
        self.assertEqual(locations["Tools"], [1] * 4 + [2] * 3,
                         "Tools begins with three items on page 1 and continues with three on page 2")
