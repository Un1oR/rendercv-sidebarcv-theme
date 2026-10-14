"""Header behavior of the theme."""

import subprocess
import xml.etree.ElementTree as ET

from tests.support import HEIGHT, RenderCase, rows


class HeaderTests(RenderCase):
    def test_header_summary_and_contact_placement(self):
        for placement in ["sidebar", "header"]:
            with self.subTest(placement=placement):
                p, _, pdf = self.render(f"header-contacts-{placement}", {
                    "summary": rows(10, 1), "experience": rows(100, 1), "skills": rows(200, 1),
                }, cv_extra={"name": "NAMECHECK", "location": "CONTACTCHECK"},
                    sections={"overrides": {"summary": {"placement": "header"}}},
                    header={"connections": {"placement": placement, "show_icons": False}})
                xml = subprocess.check_output(["pdftotext", "-bbox", str(pdf), "-"], text=True)
                words = ET.fromstring(xml).findall(".//{*}word")
                text = [word.text for word in words]
                self.assertEqual(text.count("10"), 1, "Header summary renders once")
                self.assertEqual(text.count("NAMECHECK"), 1)
                self.assertEqual(text.count("CONTACTCHECK"), 1)
                self.assertNotIn("Summary", text, "Header summary has no section heading")
                self.assert_after(p[100], p[10])
                self.assert_after(p[200], p[10])
                contact = next(word for word in words if word.text == "CONTACTCHECK")
                if placement == "sidebar":
                    self.assertGreater(float(contact.attrib["xMin"]), p[100]["x"] + p[100]["width"])
                    self.assertGreater(float(contact.attrib["yMin"]), p[10]["y"] + HEIGHT)
                else:
                    self.assertLess(float(contact.attrib["yMin"]), p[100]["y"])
