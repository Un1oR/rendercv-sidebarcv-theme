"""Shared fixtures and native Typst layout probes."""

import json
from pathlib import Path
import unittest

from rendercv.renderer.pdf_png import get_typst_compiler
from rendercv.renderer.templater.templater import render_full_template
from rendercv.schema.models.rendercv_model import RenderCVModel
from rendercv.schema.models.validation_context import ValidationContext


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "sidebarcv"
OUTPUT = Path(__file__).resolve().parent / "output"
HEIGHT = 60
LEFT, RIGHT, BOTTOM = 50.4, 561.6, 741.6  # Classic US-letter printable area, pt.


def rows(start, count, height=HEIGHT):
    """Fixed-size visible rows with native layout coordinates, independent of fonts."""
    return [
        f"#block(width: 100%, height: {height}pt, breakable: false)[#layout(size => context metadata(("
        f"probe: {i}, page: here().page(), x: here().position().x.pt(), "
        "y: here().position().y.pt(), width: size.width.pt()))) "
        f"Synthetic row {i}]"
        for i in range(start, start + count)
    ]


def model(content, cv_extra=None, locale=None, **design):
    return RenderCVModel.model_validate(
        {
            "cv": {"sections": content, **(cv_extra or {})},
            "design": {
                "theme": "sidebarcv",
                "page": {"show_footer": False, "show_top_note": False},
                **design,
            },
            "locale": locale or {"language": "english"},
            "settings": {"current_date": "2026-10-14"},
        },
        context={"context": ValidationContext(input_file_path=ROOT / "synthetic.yaml")},
    )


def order(probe):
    return probe["page"], probe["y"]


class RenderCase(unittest.TestCase):
    def render(self, name, content, *, font_input=None, **design):
        # Pagination fixtures opt in; public defaults are tested separately.
        design.setdefault("entries", {"allow_page_break": True})
        cv = model(content, **design)
        OUTPUT.mkdir(parents=True, exist_ok=True)
        path = OUTPUT / f"{name}.typ"
        path.write_text(render_full_template(cv, "typst"), encoding="utf-8")
        # Only the semibold spacing fixture opts into extras/fonts.
        compiler = get_typst_compiler(font_input or OUTPUT / "synthetic.yaml", OUTPUT)
        compiler.compile(input=path, output=path.with_suffix(".pdf"))
        probes = [
            item for item in json.loads(compiler.query("metadata", field="value"))
            if isinstance(item, dict) and "probe" in item
        ]
        self.assertEqual(len(probes), len({item["probe"] for item in probes}))
        for item in probes:
            self.assertGreaterEqual(item["x"], LEFT - 0.1)
            self.assertLessEqual(item["x"] + item["width"], RIGHT + 0.1)
            self.assertLessEqual(item["y"] + HEIGHT, BOTTOM + 0.1)
        return {item["probe"]: item for item in probes}, cv, path.with_suffix(".pdf")

    def assert_after(self, later, earlier, height=HEIGHT):
        self.assertGreater(order(later), (earlier["page"], earlier["y"] + height - 0.1))

    def assert_full(self, probe):
        self.assertAlmostEqual(probe["x"], LEFT, delta=0.1)
        self.assertAlmostEqual(probe["width"], RIGHT - LEFT, delta=0.1)
