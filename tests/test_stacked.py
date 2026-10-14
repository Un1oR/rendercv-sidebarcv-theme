"""Stacked behavior of the theme."""

import subprocess
import xml.etree.ElementTree as ET

from rendercv.renderer.templater.templater import render_full_template

from tests.support import RenderCase, rows


class StackedTests(RenderCase):
    def test_stacked_details_put_items_on_separate_lines_and_preserve_markdown(self):
        for name, details in [
            ("plain", "Alpha, Beta, Gamma"),
            ("formatted", "**Alpha**, [Beta](https://example.com), *Gamma*"),
            ("sentence", "Alpha, Beta, Gamma."),
        ]:
            for section, entries in [
                ("skills", [{"label": "Tools", "details": details}]),
                ("hobbies", [details]),
            ]:
                if name == "sentence" and section != "hobbies":
                    continue
                with self.subTest(name=name, section=section):
                    _, cv, pdf = self.render(f"stacked-{section}-{name}", {
                        "experience": rows(100, 1), section: entries,
                    }, sections={"overrides": {section: {
                        "stacked_details": True, "strip_trailing_period": True,
                    }}})
                    xml = subprocess.check_output(["pdftotext", "-bbox", str(pdf), "-"], text=True)
                    words = {word.text: word for word in ET.fromstring(xml).findall(".//{*}word")}
                    self.assertNotIn("Gamma.", words)
                    self.assertLess(float(words["Alpha"].attrib["yMin"]), float(words["Beta"].attrib["yMin"]))
                    self.assertLess(float(words["Beta"].attrib["yMin"]), float(words["Gamma"].attrib["yMin"]))
                    self.assertIn(details, render_full_template(cv, "markdown"))

    def test_stacked_items_capitalize_only_their_first_letter_with_label_selection(self):
        for language, source, original, capitalized in [
            ("english", "road trips, **cross**-platform C++, [open](https://example.com)-source iOS, codeReview tools",
             ["road trips", "cross-platform C++", "open-source iOS", "codeReview tools"],
             ["Road trips", "Cross-platform C++", "Open-source iOS", "CodeReview tools"]),
            ("russian", "автопутешествия, **новые** места, [открытый](https://example.com) код, интеграцияAPI",
             ["автопутешествия", "новые места", "открытый код", "интеграцияAPI"],
             ["Автопутешествия", "Новые места", "Открытый код", "ИнтеграцияAPI"]),
        ]:
            label = 'Qualities "C#"' if language == "english" else 'Качества "C#"'
            for section in ["skills", "hobbies"]:
                for case, capitalize in enumerate([None, True, False, [label, "Technology"], []]):
                    with self.subTest(language=language, section=section, capitalize=capitalize):
                        options = {"stacked_details": True}
                        if capitalize is not None:
                            options["capitalize_stacked_details"] = capitalize
                        entries = [source] if section == "hobbies" else [
                            {"label": label, "details": source},
                            {"label": "Technology", "details": "iOS, eBPF"},
                            {"label": "technology", "details": "iOS, eBPF"},
                        ]
                        _, cv, pdf = self.render(f"stacked-case-{language}-{section}-{case}", {
                            "experience": rows(100, 1), section: entries,
                        }, locale={"language": language}, sections={"overrides": {section: options}})
                        text = " ".join(subprocess.check_output(["pdftotext", str(pdf), "-"], text=True).split())
                        capitalize_all = capitalize is True
                        capitalize_selected = section == "skills" and isinstance(capitalize, list) and label in capitalize
                        self.assertIn(" ".join(capitalized if capitalize_all or capitalize_selected else original), text)
                        if section == "skills":
                            self.assertIn("Technology IOS EBPF" if capitalize_all or capitalize_selected else "Technology iOS eBPF", text)
                            self.assertIn("technology IOS EBPF" if capitalize_all else "technology iOS eBPF", text)
                        self.assertIn(source, render_full_template(cv, "markdown"))

    def test_stacking_preserves_punctuation_unless_text_cleanup_is_requested(self):
        for strip in [False, True]:
            _, cv, pdf = self.render(f"stacked-punctuation-{strip}", {
                "experience": rows(100, 1),
                "skills": [{"label": "Tools", "details": "Node.js, Ph.D."}],
                "hobbies": ["Maps, sketches."],
                "notes": ["Unstacked text."],
            }, sections={"overrides": {
                "skills": {"stacked_details": True, "strip_trailing_period": strip},
                "hobbies": {"stacked_details": True, "strip_trailing_period": strip},
                "notes": {"strip_trailing_period": strip},
            }})
            text = subprocess.check_output(["pdftotext", str(pdf), "-"], text=True)
            self.assertIn("Node.js", text)
            self.assertIn("Ph.D.", text, "OneLineEntry punctuation is never stripped")
            self.assertIn("sketches\n" if strip else "sketches.\n", text)
            self.assertIn("Unstacked text.", text, "Cleanup applies only to stacked TextEntry")
            self.assertIn("Maps, sketches.", render_full_template(cv, "markdown"))

    def test_bullet_separator_preserves_commas_and_inline_formatting(self):
        source = "**Research, analysis** • [Maps](https://example.com) • Writing."
        _, cv, pdf = self.render("stacked-bullet-separator", {
            "experience": rows(100, 1),
            "skills": [{"label": "Methods", "details": source}],
            "hobbies": [source],
        }, sections={"overrides": {
            section: {"stacked_details": True, "stacked_separator": "•"}
            for section in ["skills", "hobbies"]
        }})
        xml = subprocess.check_output(["pdftotext", "-bbox", str(pdf), "-"], text=True)
        words = ET.fromstring(xml).findall(".//{*}word")
        for text in ["Research,", "analysis", "Maps", "Writing."]:
            self.assertEqual(sum(word.text == text for word in words), 2)
        for occurrence in range(2):
            positions = {
                text: float([word for word in words if word.text == text][occurrence].attrib["yMin"])
                for text in ["Research,", "analysis", "Maps", "Writing."]
            }
            self.assertAlmostEqual(positions["Research,"], positions["analysis"], delta=0.1)
            self.assertLess(positions["analysis"], positions["Maps"])
            self.assertLess(positions["Maps"], positions["Writing."])
        self.assertIn(source, render_full_template(cv, "markdown"))
