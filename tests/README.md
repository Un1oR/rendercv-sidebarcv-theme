# Tests

Run from the repository root after installing the pinned development dependencies:

```sh
python -m unittest discover -s tests -v
```

The integration checks also need Poppler's `pdftotext` and `pdftohtml` (`poppler-utils`
on Debian/Ubuntu, `poppler` with Homebrew). Test output stays in `tests/output/`.

| Module | Contract |
| --- | --- |
| `test_schema.py` | Invalid geometry and unknown options are rejected; opt-in text transformations |
| `test_layout.py` | Independent columns, full-width barriers, empty columns, section routing and custom widths |
| `test_pagination.py` | Section and entry keep rules, oversized entries, spacing, no lost or duplicated rows |
| `test_stacked.py` | Lists, inline formatting, casing, punctuation, comma and bullet separators |
| `test_dates.py` | Localized dates, date precision, compact ranges and inline metadata |
| `test_header.py` | Contact placement and heading-free summaries |
| `test_entries.py` | Every RenderCV entry type and classic-theme fallback |
| `test_pagination_examples.py` | Three sidebar page-break policies with identical content, an unchanged main column and visible section/group context in the previews |
| `test_gallery.py` | Page-image selection and temporary hero inputs |
| `test_gallery_pagination.py` | Real gallery CV page boundaries: John's default kept entries, Alice's whole section and Bob's flowing group |
| `test_visual.py` | Public CLI, Markdown/HTML content, example screenshots and comparator self-check |

`support.py` owns the tiny synthetic fixtures and native Typst coordinate probes.
These structural tests explain failures precisely, while `visual.py` catches changes
to the complete CVs that coordinate assertions cannot cover.
The compact semibold spacing fixture explicitly uses `extras/fonts`; other structural
fixtures and all public example screenshots use only RenderCV's bundled fonts.

## Visual regression

The four complete examples (`starter`, `john`, `alice`, `bob`) are copied into
independent consumer directories next
to the `sidebarcv/` folder. The tests invoke `python -m rendercv render` there and
check its PDF, Typst, Markdown and HTML outputs. No personal CV paths, optional fonts,
or installed theme package are needed. Screenshots use bundled RenderCV fonts only;
system fonts are disabled in the screenshot compiler.

Baselines live in `tests/baselines/<example>/page-<number>.png`. RenderCV 2.8,
Typst 0.15.0, rendercv-fonts 0.5.1, 144 dpi, and `current_date: 2026-10-14` are fixed.
Page count and dimensions must match exactly. Every RGB channel of every pixel must
be within 2/255 of its reference; there is no permitted percentage of changed pixels,
alignment, blur, resizing, or automatic baseline replacement. A one-pixel shift fails.
Failures retain actual PNGs, PDF, CLI log and enhanced difference images in
`tests/output/visual/<example>/`. A baseline missing from a checkout is a failure.

```sh
# Check only the complete examples.
python -m unittest tests.test_visual -v

# Inspect actual output, then explicitly replace only the approved example.
python -m tests.visual --update alice

# Explicitly update all examples after reviewing the intended change.
python -m tests.visual --update
```

Review baseline PNG changes together with the source diff. Do not update a baseline
merely to silence a failing test. The maintainer's private default CV is checked in
its owning repository; it is intentionally absent from these public fixtures.

HTML is checked for content preservation, not PDF-like styling: RenderCV's HTML
comes from its separate Markdown pipeline. These checks cover standard body fields;
custom entry fields such as `tags` are not exported by that pipeline. HTML visual
parity is outside this suite.
