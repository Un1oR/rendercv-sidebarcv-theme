"""Layout behavior of the theme."""

from rendercv.renderer.templater.templater import render_full_template

from tests.support import LEFT, RenderCase, order, rows


class LayoutTests(RenderCase):
    def test_independent_columns_and_full_width_barrier(self):
        for left, right in [(14, 2), (2, 14), (14, 17)]:
            with self.subTest(left=left, right=right):
                p, _, _ = self.render(f"columns-{left}-{right}", {
                    "experience": rows(100, left),
                    "skills": rows(200, right),
                    "publications": rows(300, 1),
                })
                self.assertEqual(len(p), left + right + 1)
                self.assertEqual(p[100]["page"], 1)
                self.assertEqual(p[200]["page"], 1)
                self.assertAlmostEqual(p[100]["y"], p[200]["y"], delta=0.1)
                for i in range(100, 100 + left):
                    self.assertAlmostEqual(p[i]["x"], LEFT, delta=0.1)
                    self.assertAlmostEqual(p[i]["width"], p[100]["width"], delta=0.1)
                for i in range(200, 200 + right):
                    self.assertGreater(p[i]["x"], p[100]["x"] + p[100]["width"])
                    self.assertAlmostEqual(p[i]["width"], p[200]["width"], delta=0.1)
                self.assertGreater(max(p[99 + left]["page"], p[199 + right]["page"]), 1)
                self.assert_after(p[300], p[99 + left])
                self.assert_after(p[300], p[199 + right])
                self.assert_full(p[300])

    def test_publications_can_be_main_before_sidebar_ends(self):
        p, _, _ = self.render("publications-in-main", {
            "experience": rows(100, 2), "skills": rows(200, 14),
            "publications": rows(300, 1),
        }, sections={"overrides": {"publications": {"placement": "main"}}})
        self.assert_after(p[300], p[101])
        self.assertLess(order(p[300]), order(p[213]))
        self.assertAlmostEqual(p[300]["width"], p[100]["width"], delta=0.1)

    def test_prefix_tail_and_late_sidebar(self):
        p, cv, _ = self.render("prefix-and-tail", {
            "summary": rows(10, 1), "experience": rows(100, 2),
            "publications": rows(300, 1), "projects": rows(400, 1),
            "skills": rows(200, 3),
        })
        for i in [10, 300, 400]:
            self.assert_full(p[i])
        self.assert_after(p[100], p[10])
        self.assertAlmostEqual(p[100]["y"], p[200]["y"], delta=0.1)
        self.assert_after(p[300], p[202])
        self.assert_after(p[400], p[300])
        markdown = render_full_template(cv, "markdown")
        offsets = [markdown.index(title) for title in ["Summary", "Experience", "Publications", "Projects", "Skills"]]
        self.assertEqual(offsets, sorted(offsets), "Markdown keeps semantic source order")

    def test_empty_columns_collapse(self):
        for name, sections in [
            ("no-sidebar", {"experience": rows(100, 2)}),
            ("empty-sidebar", {"experience": rows(100, 2), "skills": []}),
            ("only-sidebar", {"skills": rows(100, 2)}),
            ("empty-main", {"experience": [], "skills": rows(100, 2)}),
        ]:
            with self.subTest(name=name):
                p, _, _ = self.render(name, sections)
                for probe in p.values():
                    self.assert_full(probe)

    def test_duplicate_normalized_titles_do_not_lose_entries(self):
        p, _, _ = self.render("duplicate-normalized-titles", {
            "Skills": [], "skills": rows(200, 1),
        })
        self.assertEqual(set(p), {200})
        self.assert_full(p[200])

    def test_configurable_width_gap_and_section_names(self):
        p, _, _ = self.render("custom-width-and-names", {
            "experience": rows(100, 1), "Custom Sidebar": rows(200, 1),
        }, sidebar_width=0.4, column_gap="1cm",
            sections={"overrides": {"Custom Sidebar": {"placement": "sidebar", "allow_page_break": False}}})
        self.assertAlmostEqual(p[200]["width"] / p[100]["width"], 0.4 / 0.6, delta=0.001)
        self.assertAlmostEqual(p[200]["x"] - p[100]["x"] - p[100]["width"], 72 / 2.54, delta=0.1)
