"""Dates behavior of the theme."""

import subprocess
import xml.etree.ElementTree as ET

from rendercv.renderer.templater.templater import render_full_template

from tests.support import RenderCase


class DatesTests(RenderCase):
    def test_inline_date_metadata_and_opt_in_equal_date_collapse(self):
        content = {
            "experience": [
                {"company": "Company", "position": "SAME", "start_date": "2020-07", "end_date": "2020-07", "location": "SAMEPLACE"},
                {"company": "Company", "position": "DISTINCT", "start_date": "2020-07", "end_date": "2021-08", "location": "RANGEPLACE"},
                {"company": "Company", "position": "DATEONLY", "date": "2019-09"},
                {"company": "Company", "position": "LOCATIONONLY", "location": "ONLYPLACE"},
                {"company": "Company", "position": "DAYRANGE", "start_date": "2020-07-01", "end_date": "2020-07-10", "location": "DAYPLACE"},
                {"company": "Company", "position": "FREETEXT", "date": "2023 – 2023", "location": "TEXTPLACE"},
            ],
            "education": [{"institution": "School", "area": "Area", "degree": "BS",
                           "start_date": 2018, "end_date": 2018, "location": "EDPLACE"}],
            "projects": [{"name": "NORMAL", "start_date": 2022, "end_date": 2022, "location": "NORMPLACE"}],
        }
        for language, months in [
            ("english", ("July", "August", "September")),
            ("russian", ("Июль", "Август", "Сентябрь")),
        ]:
            markdown = []
            for collapse in [False, True]:
                with self.subTest(language=language, collapse=collapse):
                    templates = {
                        "single_date": "MONTH_NAME YEAR",
                        "experience_entry": {"main_column": "**POSITION**, COMPANY\nDATE • LOCATION\nSUMMARY\nHIGHLIGHTS"},
                        "education_entry": {"main_column": "**DEGREE, AREA**\nINSTITUTION\nDATE • LOCATION\nSUMMARY\nHIGHLIGHTS"},
                        "normal_entry": {"main_column": "**NAME**\nDATE • LOCATION\nSUMMARY\nHIGHLIGHTS"},
                    }
                    if collapse:
                        templates["collapse_same_dates"] = True
                    _, cv, pdf = self.render(f"date-metadata-{language}-{collapse}", content,
                        locale={"language": language}, templates=templates,
                        sections={"show_time_spans_in": []},
                        colors={"date_and_location": "rgb(100, 100, 100)"} if collapse else {})
                    markdown.append(render_full_template(cv, "markdown"))
                    xml = ET.fromstring(subprocess.check_output(["pdftohtml", "-xml", "-stdout", str(pdf)], text=True))
                    colors = {font.attrib["id"]: font.attrib["color"] for font in xml.findall(".//fontspec")}
                    lines = [("".join(line.itertext()).strip(), colors[line.attrib["font"]]) for line in xml.findall(".//text")]
                    july, august, september = months
                    expected = {
                        "SAMEPLACE": f"{july} 2020" if collapse else f"{july} 2020 – {july} 2020",
                        "RANGEPLACE": f"{july} 2020 – {august} 2021",
                        "DAYPLACE": f"{july} 2020" if collapse else f"{july} 2020 – {july} 2020",
                        "TEXTPLACE": "2023 – 2023",
                        "EDPLACE": "2018" if collapse else "2018 – 2018",
                        "NORMPLACE": "2022" if collapse else "2022 – 2022",
                    }
                    for location, date in expected.items():
                        found = [(text, color) for text, color in lines if location in text]
                        self.assertEqual(len(found), 1)
                        self.assertEqual(found[0][0], f"{date} • {location}", "Date and location share one line")
                        if collapse:
                            self.assertEqual(found[0][1], "#646464")
                        elif location != "EDPLACE":
                            self.assertEqual(found[0][1], "#000000", "Metadata color is opt-in")
                    self.assertIn((f"{september} 2019", "#646464" if collapse else "#000000"), lines)
                    self.assertIn(("ONLYPLACE", "#646464" if collapse else "#000000"), lines)
            self.assertEqual(markdown[0], markdown[1], "PDF date styling does not rewrite Markdown")
            _, _, pdf = self.render(f"date-day-precision-{language}", {
                "experience": [content["experience"][4]],
            }, locale={"language": language}, sections={"show_time_spans_in": []}, templates={
                "single_date": "DAY MONTH_NAME YEAR", "collapse_same_dates": True,
                "experience_entry": {"main_column": "**POSITION**\nDATE • LOCATION"},
            })
            text = subprocess.check_output(["pdftotext", str(pdf), "-"], text=True)
            self.assertIn(f"1 {months[0]} 2020 – 10 {months[0]} 2020 • DAYPLACE", text,
                          "Distinct displayed endpoints must remain a range")
