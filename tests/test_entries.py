"""Entries behavior of the theme."""

import subprocess

from tests.support import RenderCase


class EntriesTests(RenderCase):
    def test_all_entry_types_and_classic_fallback(self):
        sections = {
            "text": ["TEXTMARKER"],
            "bullet": [{"bullet": "BULLETMARKER"}],
            "numbered": [{"number": "NUMBERMARKER"}],
            "reversed": [{"reversed_number": "REVERSEFIRST"}, {"reversed_number": "REVERSESECOND"}],
            "one_line": [{"label": "Label", "details": "ONELINEMARKER"}],
            "experience": [{"company": "Company", "position": "EXPERIENCEMARKER", "date": "2024"}],
            "education": [{"institution": "School", "area": "EDUCATIONMARKER", "degree": "BS", "date": "2020"}],
            "normal": [{"name": "NORMALMARKER", "highlights": ["A highlight"]}],
            "publication": [{"title": "PUBLICATIONMARKER", "authors": ["Author"], "date": "2023"}],
        }
        for theme in ["sidebarcv", "classic"]:
            with self.subTest(theme=theme):
                _, cv, pdf = self.render(f"entries-{theme}", sections, theme=theme)
                text = subprocess.check_output(["pdftotext", "-layout", str(pdf), "-"], text=True)
                for token in ["TEXTMARKER", "BULLETMARKER", "NUMBERMARKER", "ONELINEMARKER", "EXPERIENCEMARKER", "EDUCATIONMARKER", "NORMALMARKER", "PUBLICATIONMARKER"]:
                    self.assertIn(token, text)
                self.assertRegex(text, r"2\.\s+REVERSEFIRST")
                self.assertRegex(text, r"1\.\s+REVERSESECOND")
                self.assertEqual(cv.design.typography.font_family.body, "Source Sans 3")
