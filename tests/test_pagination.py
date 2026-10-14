"""Pagination behavior of the theme."""

import subprocess
import xml.etree.ElementTree as ET

from typst import TypstError
from rendercv.renderer.templater.templater import render_full_template

from tests.support import HEIGHT, LEFT, ROOT, RenderCase, rows


class PaginationTests(RenderCase):
    def test_section_break_override_moves_heading_and_all_entries(self):
        sections = {"experience": rows(100, 14), "skills": rows(200, 8), "hobbies": rows(300, 3)}
        loose, _, _ = self.render("sidebar-breakable", sections)
        kept, _, pdf = self.render("sidebar-kept", sections,
                                  sections={"overrides": {"hobbies": {"allow_page_break": False}}})
        self.assertLess(loose[300]["page"], loose[302]["page"])
        self.assertEqual({kept[i]["page"] for i in range(300, 303)}, {2})
        xml = subprocess.check_output(["pdftotext", "-bbox", str(pdf), "-"], text=True)
        pages = ET.fromstring(xml).findall(".//{*}page")
        headings = [(number, float(word.attrib["yMin"]))
                    for number, page in enumerate(pages, 1)
                    for word in page.findall(".//{*}word") if word.text == "Hobbies"]
        self.assertEqual(len(headings), 1)
        self.assertEqual(headings[0][0], kept[300]["page"])
        self.assertLess(headings[0][1], kept[300]["y"])

    def test_oversized_unbreakable_section_fails(self):
        with self.assertRaisesRegex(TypstError, "section with allow_page_break: false is taller"):
            self.render("oversized-kept", {"skills": rows(200, 14)},
                        sections={"overrides": {"skills": {"allow_page_break": False}}})

    def test_standard_section_break_setting_keeps_sections_not_document(self):
        p, _, _ = self.render("global-section-keep", {
            "experience": rows(100, 6), "projects": rows(200, 6),
            "skills": rows(300, 2),
        }, sections={"allow_page_break": False})
        self.assertEqual({p[i]["page"] for i in range(100, 106)}, {1})
        self.assertEqual({p[i]["page"] for i in range(200, 206)}, {2})

    def test_section_true_overrides_global_false(self):
        p, _, _ = self.render("section-allows-break", {
            "experience": rows(100, 2), "skills": rows(200, 14),
        }, sections={"allow_page_break": False,
                     "overrides": {"skills": {"allow_page_break": True}}})
        self.assertEqual(len(p), 16)
        self.assertEqual({p[i]["page"] for i in range(100, 102)}, {1})
        self.assertGreater(p[213]["page"], p[200]["page"])

    def test_entry_break_policy_keeps_skill_groups_not_whole_section(self):
        groups = [
            [f"GROUP{i}", *(f"ITEM{i}X{j}" for j in range(10))]
            for i in range(8)
        ]
        content = {
            "experience": rows(100, 14),
            "skills": [{"label": group[0], "details": ", ".join(group[1:])} for group in groups],
        }
        for name, global_break, local_break in [
            ("local-kept", True, False),
            ("global-kept", False, None),
            ("local-breakable", False, True),
        ]:
            with self.subTest(name=name):
                override = {"stacked_details": True}
                if local_break is not None:
                    override["entries"] = {"allow_page_break": local_break}
                _, _, pdf = self.render(f"skill-groups-{name}", content,
                    entries={"allow_page_break": global_break},
                    sections={"overrides": {"skills": override}})
                xml = subprocess.check_output(["pdftotext", "-bbox", str(pdf), "-"], text=True)
                words = [(word.text, number, float(word.attrib["yMin"]))
                         for number, page in enumerate(ET.fromstring(xml).findall(".//{*}page"), 1)
                         for word in page.findall(".//{*}word")]
                skill_pages = set()
                split_groups = []
                for group in groups:
                    found = [(text, page, y) for text, page, y in words if text in group]
                    self.assertEqual(sorted(text for text, _, _ in found), sorted(group))
                    pages = {page for _, page, _ in found}
                    skill_pages.update(pages)
                    split_groups.append(len(pages) > 1)
                    self.assertEqual([text for text, _, _ in found], group)
                    self.assertEqual([(page, y) for _, page, y in found],
                                     sorted((page, y) for _, page, y in found))
                self.assertGreater(len(skill_pages), 1, "Skills still spans pages")
                if local_break is True:
                    self.assertTrue(any(split_groups), "Fixture exercises a group at a page boundary")
                else:
                    self.assertFalse(any(split_groups), "Each label stays with all its details")

    def test_oversized_unbreakable_stacked_entry_fails(self):
        with self.assertRaisesRegex(TypstError, "entry with allow_page_break: false is taller"):
            self.render("oversized-skill-group", {
                "experience": rows(100, 2),
                "skills": [{"label": "Too many items", "details": ", ".join(f"Item{i}" for i in range(70))}],
            }, sections={"overrides": {"skills": {
                "stacked_details": True, "entries": {"allow_page_break": False},
            }}})

    def test_kept_stacked_entries_preserve_native_spacing_without_overlap(self):
        for spacing in ["0.3em", "0.9em"]:
            positions = {}
            for allow in [True, False]:
                with self.subTest(spacing=spacing, allow=allow):
                    _, _, pdf = self.render(f"stacked-gap-{spacing}-{allow}", {
                        "experience": rows(100, 2),
                        "skills": [{"label": "FIRST", "details": "Alpha, Beta, LAST"},
                                   {"label": "NEXT", "details": "Gamma, Delta"}],
                    }, font_input=ROOT / "extras" / "synthetic.yaml",
                    typography={"line_spacing": "0.45em", "bold_weight": 600}, sections={
                        "space_between_text_based_entries": spacing,
                        "overrides": {"skills": {"stacked_details": True,
                                                 "entries": {"allow_page_break": allow}}},
                    })
                    xml = subprocess.check_output(["pdftotext", "-bbox", str(pdf), "-"], text=True)
                    words = {word.text: word for word in ET.fromstring(xml).findall(".//{*}word")}
                    last_bottom = float(words["LAST"].attrib["yMax"])
                    next_top = float(words["NEXT"].attrib["yMin"])
                    positions[allow] = (last_bottom, next_top)
                    self.assertGreater(next_top, last_bottom, "Next group must not overlap the last item")
            for loose, kept in zip(positions[True], positions[False]):
                self.assertAlmostEqual(loose, kept, delta=0.01,
                                       msg="Keeping an entry changes pagination, not native spacing")

    def test_regular_entry_override_is_scoped_to_its_section(self):
        for global_break, local_break in [(True, False), (False, True)]:
            with self.subTest(global_break=global_break, local_break=local_break):
                p, _, _ = self.render(f"regular-entry-policy-{local_break}", {
                    "experience": rows(100, 7),
                    "projects": [{"name": "PROJECT", "highlights": rows(200, 5)}],
                    "following": [{"name": "FOLLOWING", "highlights": rows(300, 9)}],
                    "skills": rows(400, 1),
                }, entries={"allow_page_break": global_break},
                    sections={"overrides": {"projects": {"entries": {"allow_page_break": local_break}}}})
                project_pages = {p[i]["page"] for i in range(200, 205)}
                following_pages = {p[i]["page"] for i in range(300, 309)}
                self.assertEqual(len(project_pages) > 1, local_break)
                self.assertEqual(len(following_pages) > 1, global_break)

    def test_oversized_regular_entries_split_between_fresh_pages(self):
        for kind, identity in [
            ("experience", {"company": "Company", "position": "RECORD"}),
            ("education", {"institution": "University", "area": "Degree"}),
        ]:
            for prefix in [False, True]:
                markdown = []
                for allow in [False, True]:
                    with self.subTest(kind=kind, prefix=prefix, allow=allow):
                        entries = [identity | {"highlights": rows(100, 2)}] if prefix else []
                        entries += [identity | {"highlights": rows(200, 16)},
                                    identity | {"highlights": rows(300, 2)}]
                        p, cv, _ = self.render(f"oversized-{kind}-{prefix}-{allow}", {
                            "records": entries, "skills": rows(400, 2),
                        }, sections={"overrides": {"records": {"entries": {"allow_page_break": allow}}}})
                        markdown.append(render_full_template(cv, "markdown"))
                        expected = set(range(200, 216)) | {300, 301, 400, 401}
                        if prefix:
                            expected |= {100, 101}
                        self.assertEqual(set(p), expected, "Oversized entry retains every row exactly once")
                        self.assertGreater(p[215]["page"], p[200]["page"])
                        if allow:
                            self.assertEqual(p[200]["page"], 1)
                            self.assertEqual(p[300]["page"], p[215]["page"], "Breakable entries keep normal flow")
                        else:
                            self.assertEqual(p[300]["page"], p[301]["page"])
                            self.assertEqual(p[200]["page"], 2 if prefix else 1,
                                             "Fresh start must not insert a blank leading page")
                            self.assertEqual(p[300]["page"], p[215]["page"] + 1,
                                             "Next record starts after the oversized record's final page")
                            self.assertLess(p[200]["y"], LEFT + HEIGHT)
                            self.assertLess(p[300]["y"], LEFT + HEIGHT)
                self.assertEqual(markdown[0], markdown[1], "Fallback changes PDF layout, not source content")
