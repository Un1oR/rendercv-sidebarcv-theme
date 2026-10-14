"""Classic typography with one independent sidebar and a full-width tail."""

import re
from typing import Literal

from pydantic import Field, field_validator, model_validator
from rendercv.schema.models.base import BaseModelWithoutExtraKeys
from rendercv.renderer.templater.entry_templates_from_input import remove_not_provided_placeholders
from rendercv.renderer.templater.markdown_parser import markdown_to_typst
from rendercv.renderer.templater.string_processor import make_keywords_bold, substitute_placeholders
from rendercv.schema.models.design.classic_theme import ClassicTheme, Colors, Connections, Header, Sections, Templates, Typography
from rendercv.schema.models.design.color import Color
from rendercv.schema.models.design.typst_dimension import TypstDimension


DEFAULT_PLACEMENT = {
    "summary": "full",
    "education": "sidebar",
    "skills": "sidebar",
    "languages": "sidebar",
    "hobbies": "sidebar",
    "publications": "full",
    "talks": "full",
    "talks_and_publications": "full",
}


def merge(defaults, overrides):
    """Apply partial design overrides without losing the theme's nested defaults."""
    result = defaults | overrides
    for key in defaults.keys() & overrides.keys():
        if isinstance(defaults[key], dict) and isinstance(overrides[key], dict):
            result[key] = merge(defaults[key], overrides[key])
    return result


class EntryOverride(BaseModelWithoutExtraKeys):
    allow_page_break: bool | None = None


class SectionOverride(BaseModelWithoutExtraKeys):
    placement: Literal["main", "sidebar", "full", "header"] | None = None
    allow_page_break: bool | None = None
    stacked_details: bool = False
    stacked_separator: Literal[",", "•"] = ","
    capitalize_stacked_details: bool | list[str] = False
    strip_trailing_period: bool = False
    entries: EntryOverride = Field(default_factory=EntryOverride)


class SidebarSections(Sections):
    overrides: dict[str, SectionOverride] = Field(default_factory=dict)

    @field_validator("overrides", mode="before")
    @classmethod
    def normalize_names(cls, value):
        if isinstance(value, dict) and all(isinstance(key, str) for key in value):
            return {key.lower().replace(" ", "_"): item for key, item in value.items()}
        return value


class SidebarConnections(Connections):
    placement: Literal["header", "sidebar"] = "header"
    sidebar_title: str = "Contact"


class SidebarHeader(Header):
    connections: SidebarConnections = Field(default_factory=SidebarConnections)
    photo_vertical_alignment: Literal["top", "center", "bottom"] = "center"


class SidebarColors(Colors):
    date_and_location: Color | None = None
    tags: Color | None = None


class SidebarTemplates(Templates):
    collapse_same_dates: bool = False


class SidebarTypography(Typography):
    bold_weight: int = Field(default=700, ge=100, le=900)


class SidebarcvTheme(ClassicTheme):
    theme: Literal["sidebarcv"] = "sidebarcv"
    sections: SidebarSections = Field(default_factory=SidebarSections)
    header: SidebarHeader = Field(default_factory=SidebarHeader)
    colors: SidebarColors = Field(default_factory=SidebarColors)
    templates: SidebarTemplates = Field(default_factory=SidebarTemplates)
    typography: SidebarTypography = Field(default_factory=SidebarTypography)
    sidebar_width: float = Field(default=0.25, gt=0, lt=1)
    column_gap: TypstDimension = "0.7cm"

    @field_validator("column_gap")
    @classmethod
    def nonnegative_gap(cls, value):
        if value.startswith("-"):
            raise ValueError("column_gap must be nonnegative")
        return value

    def placement(self, name):
        options = self.sections.overrides.get(name, SectionOverride())
        return options.placement or DEFAULT_PLACEMENT.get(name, "main")

    def section_page_break(self, name):
        options = self.sections.overrides.get(name, SectionOverride())
        return self.sections.allow_page_break if options.allow_page_break is None else options.allow_page_break

    def section_entries_page_break(self, name):
        options = self.sections.overrides.get(name, SectionOverride()).entries
        return self.entries.allow_page_break if options.allow_page_break is None else options.allow_page_break

    @staticmethod
    def typst_label(label, bold_keywords):
        return markdown_to_typst(make_keywords_bold(label, bold_keywords))

    def prepare_entry(self, entry):
        """Style metadata rows, preserving the native entry renderer and templates."""
        fields = {key: getattr(entry, key) for key in ("DATE", "LOCATION") if hasattr(entry, key)}
        updated = fields.copy()
        if (
            self.templates.collapse_same_dates
            and getattr(entry, "START_DATE", None) is not None
            and entry.START_DATE == getattr(entry, "END_DATE", None)
        ):
            date_range = substitute_placeholders(
                markdown_to_typst(self.templates.date_range.replace("START_DATE", "STARTDATE").replace("END_DATE", "ENDDATE")),
                {"STARTDATE": entry.START_DATE, "ENDDATE": entry.END_DATE},
            )
            updated["DATE"] = fields["DATE"].replace(date_range, entry.START_DATE, 1)

        columns = {}
        template = getattr(self.templates, entry.entry_type_in_snake_case)
        for column in ("main_column", "date_and_location_column"):
            body = getattr(entry, column)
            for line in getattr(template, column).splitlines():
                # Inspect the user template, never parse the generated Typst.
                if not re.fullmatch(r"\W*(?:DATE|LOCATION)(?:DATE|LOCATION|\W)*", line):
                    continue
                source = remove_not_provided_placeholders({"row": line}, fields)["row"]
                old = substitute_placeholders(markdown_to_typst(source), fields)
                if "DATE" in line and "LOCATION" in line and not {"DATE", "LOCATION"} <= fields.keys():
                    source = source.strip(" •·|–—,:;/-")
                new = substitute_placeholders(markdown_to_typst(source), updated)
                if self.colors.date_and_location is not None:
                    new = "\n".join(
                        f"#text(fill: {self.colors.date_and_location})[{part}]" if part else part
                        for part in new.splitlines()
                    )
                body = ("\n" + body + "\n").replace("\n" + old + "\n", "\n" + new + "\n")[1:-1]
            if updated.get("DATE") != fields.get("DATE"):
                body = body.replace(fields["DATE"], updated["DATE"])
            columns[column] = body
        return entry.model_copy(update=columns)

    @model_validator(mode="before")
    @classmethod
    def inline_dates(cls, value):
        # Use RenderCV's entry renderer, with dates in the body and no date column.
        defaults = {
            "entries": {
                "date_and_location_width": "0cm",
                "space_between_columns": "0cm",
                "side_space": "0cm",
            },
            "templates": {
                "experience_entry": {
                    "main_column": "**POSITION**, COMPANY\nDATE\nLOCATION\nSUMMARY\nHIGHLIGHTS\n*TAGS*",
                    "date_and_location_column": "",
                },
                "education_entry": {
                    "main_column": "**DEGREE, AREA**\nINSTITUTION\nDATE\nLOCATION\nSUMMARY\nHIGHLIGHTS",
                    "date_and_location_column": "",
                    "degree_column": "",
                },
                "normal_entry": {
                    "main_column": "**NAME**\nSUMMARY, DATE\nLOCATION\nHIGHLIGHTS\n*TAGS*",
                    "date_and_location_column": "",
                },
                "publication_entry": {
                    "main_column": "**TITLE**\nDATE\nSUMMARY\nAUTHORS\nURL (JOURNAL)",
                    "date_and_location_column": "",
                },
            },
        }
        return merge(defaults, value) if isinstance(value, dict) else value
