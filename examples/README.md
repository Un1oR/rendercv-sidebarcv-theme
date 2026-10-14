# Example CVs

Choose a complete CV to edit, or compare layouts using the same content.

| File | What it demonstrates |
| --- | --- |
| `starter.yaml` | The original RenderCV starter content in SidebarCV's default layout. |
| `john.yaml` | A complete CV using only `design.theme: sidebarcv`. Inline skill groups follow the default keep-together policy; Research Areas starts intact on page two. |
| `alice.yaml` | A blue portrait, a compact header summary and sidebar contacts. The whole Skills section stays together on page two. Copy `alice-portrait.png` beside the input YAML. |
| `bob.yaml` | A wider green sidebar and centered header. Method details can flow across pages; Tools begins on page one and continues on page two. |
| `comparison.yaml` + `comparison-design.yaml` | The same content with changes to section placement, contacts, stacked lists and date formatting. |
| `pagination.yaml` + `pagination-flow.yaml` | A long sidebar whose skill groups can split across pages. |
| `pagination.yaml` + `pagination-section.yaml` | The entire Skills section kept on one page. |
| `pagination.yaml` + `pagination-groups.yaml` | Each skill group kept together, with page breaks between groups. |

From the repository root, copy a sample beside the theme and render it:

```sh
cp examples/alice.yaml my_cv.yaml
cp examples/alice-portrait.png .
rendercv render my_cv.yaml
```

In PowerShell, use `Copy-Item` for the two copy commands. The `sidebarcv/`
directory and portrait belong beside the input YAML. Outputs appear in
`rendercv_output/`.

Compare page-break policies with the same CV:

```sh
cp examples/pagination.yaml my_cv.yaml
rendercv render my_cv.yaml --design examples/pagination-flow.yaml --output-folder rendercv_output/pagination-flow
rendercv render my_cv.yaml --design examples/pagination-section.yaml --output-folder rendercv_output/pagination-section
rendercv render my_cv.yaml --design examples/pagination-groups.yaml --output-folder rendercv_output/pagination-groups
```

Each design file contains the complete `design:` block: RenderCV's `--design`
option replaces that block. By default, sections can break across pages and
individual entries stay together. The flow example explicitly allows entries
to break; the groups example applies the default policy to stacked skill groups.

For the compact before/after comparison:

```sh
cp examples/comparison.yaml my_cv.yaml
rendercv render my_cv.yaml --output-folder rendercv_output/comparison-before
rendercv render my_cv.yaml --design examples/comparison-design.yaml --output-folder rendercv_output/comparison-after
```

The examples use `settings.current_date: 2026-10-14` for reproducible previews.
Set it to `today` in your own CV.

Rebuild the public gallery using the development environment from the main README:

```sh
python docs/build_gallery.py
```

Review the rendered pages before updating gallery assets or visual regression
baselines. The gallery includes complete PDFs, page images and downloadable YAML
files. The gallery switches between all three pages of John and both pages
of Alice and Bob; the original starter is linked separately.
