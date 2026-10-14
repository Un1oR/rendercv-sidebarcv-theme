"""Schema behavior of the theme."""

import unittest

from pydantic import ValidationError

from tests.support import model


class SchemaTests(unittest.TestCase):
    def test_invalid_geometry_and_placement(self):
        for override in [
            {"sidebar_width": 0}, {"sidebar_width": 1}, {"column_gap": "-1cm"},
            {"templates": {"collapse_same_dates": "maybe"}},
            {"colors": {"date_and_location": "invalid"}},
            {"colors": {"tags": "invalid"}},
            {"sections": {"overrides": {"skills": {"placement": "floating"}}}},
            {"sections": {"overrides": {"skills": {"allow_page_break": "maybe"}}}},
            {"sections": {"overrides": {"skills": {"entries": {"allow_page_break": "maybe"}}}}},
            {"sections": {"overrides": {"skills": {"entries": {"keep_together": True}}}}},
            {"sections": {"overrides": {"skills": {"capitalize_stacked_details": "maybe"}}}},
            {"sections": {"overrides": {"skills": {"capitalize_stacked_details": [True]}}}},
            {"sections": {"overrides": {"skills": {"capitalize_stacked_details": {"label": "Technology"}}}}},
            {"sections": {"overrides": {"skills": {"strip_trailing_period": "maybe"}}}},
            {"sections": {"overrides": {"skills": {"stacked_separator": ";"}}}},
            {"sections": {"overrides": {"skills": {"preserve_case_labels": []}}}},
            {"sections": {"overrides": {2: {"placement": "sidebar"}}}},
        ]:
            with self.subTest(override=override), self.assertRaises(ValidationError):
                model({}, **override)

    def test_stacking_does_not_change_case_or_punctuation_by_default(self):
        options = model({}, sections={"overrides": {"skills": {"stacked_details": True}}}).design.sections.overrides["skills"]
        self.assertFalse(options.capitalize_stacked_details)
        self.assertFalse(options.strip_trailing_period)
        self.assertEqual(options.stacked_separator, ",")
        self.assertFalse(model({}).design.entries.allow_page_break)
        self.assertEqual(model({}).design.sections.show_time_spans_in, ["experience"])
