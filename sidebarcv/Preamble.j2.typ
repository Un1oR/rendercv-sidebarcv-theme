{# Sections are routed inside a grid, so enforce their break policy here instead
   of letting RenderCV treat the assembled document as one unbreakable section. #}
{% set design = design.model_copy(update={"sections": design.sections.model_copy(update={"allow_page_break": true})}) %}
{% include "typst/Preamble.j2.typ" %}

// Keep the heading with its content. Refuse impossible unbreakable sections
// instead of letting Typst silently place content outside the printable page.
#let sidebar-section(allow-page-break, body) = context {
  if not allow-page-break {
    v({{ design.section_titles.space_above }}, weak: true)
    layout(size => {
      assert(measure(block(body), width: size.width).height <= size.height,
        message: "sidebarcv: a section with allow_page_break: false is taller than the printable page; allow it to break.")
      block(breakable: false, body)
    })
  } else {
    body
  }
}

// Use RenderCV's own entry renderer with a section-local policy.
#let sidebar-entry-policy(allow-page-break, body) = {
  rendercv-config.update(config => config + (entries-allow-page-break: allow-page-break))
  body
  rendercv-config.update(config => config + (entries-allow-page-break: {{ design.entries.allow_page_break|lower }}))
}

// Typst pagebreak cannot appear inside a grid cell. Fill the current region
// instead; the zero-height frame anchors here() before its own vertical space.
#let sidebar-next-page(height) = context {
  block(height: 0pt, above: 0pt, below: 0pt)[]
  let top = {{ design.page.top_margin }}
  let y = here().position().y
  if y > top + 0.1pt { v(top + height - y) }
}

#let sidebar-regular-entry(body) = {
  [#metadata(none)<sidebarcv-entry-start>]
  context {
    let config = rendercv-config.get()
    if config.at("entries-allow-page-break") {
      body
    } else {
      layout(size => {
        let actual = measure(body, width: size.width).height
        if actual > size.height {
          context {
            let section = query(selector(<sidebarcv-section-start>).before(here())).last()
            let entries = query(selector(<sidebarcv-entry-start>).after(section.location()).before(here()))
            let empty-header-gap = calc.max(0pt, {{ design.header.space_below_connections }} - {{ design.section_titles.space_above }})
            let first-on-page = entries.len() == 1 and section.location().page() == here().page() and section.location().position().y <= {{ design.page.top_margin }} + empty-header-gap + 0.1pt
            if not first-on-page { sidebar-next-page(size.height) }
          }
          rendercv-config.update(c => c + (entries-allow-page-break: true))
          body
          rendercv-config.update(c => c + (entries-allow-page-break: false))
          sidebar-next-page(size.height)
        } else {
          body
        }
      })
      v(config.at("sections-space-between-regular-entries") + config.at("typography-line-spacing"), weak: true)
    }
  }
}

#let original-regular-entry = regular-entry
#let regular-entry(main-column, date-and-location-column, ..args) = sidebar-regular-entry(
  original-regular-entry(main-column, date-and-location-column, ..args),
)
#let original-education-entry = education-entry
#let education-entry(main-column, date-and-location-column, ..args) = sidebar-regular-entry(
  original-education-entry(main-column, date-and-location-column, ..args),
)

#let sidebar-text-entry(allow-page-break, body) = {
  let rendered = content-area(body)
  if allow-page-break {
    rendered
  } else {
    layout(size => {
      assert(measure(rendered, width: size.width).height <= size.height,
        message: "sidebarcv: an entry with allow_page_break: false is taller than the printable page; allow it to break.")
      rendered
    })
    // layout consumes content-area's trailing spacing; restore its native gap.
    v({{ design.sections.space_between_text_based_entries }} + {{ design.typography.line_spacing }}, weak: true)
  }
}

#let sidebar-stacked-items(body, capitalize: false, separator: ",") = {
  let first = state("sidebarcv-first-stacked-word", true)
  first.update(true)
  show regex("[^\\s" + separator + "][^" + separator + "]*|" + separator + "\\s*"): item => context {
    if item.text.starts-with(separator) {
      first.update(true)
      linebreak()
    } else {
      let capitalize-first = capitalize and first.get()
      first.update(false)
      if capitalize-first {
        upper(item.text.first()) + item.text.slice(item.text.first().len())
      } else {
        item
      }
    }
  }
  body
}

#let sidebar-capture(placement, allow-page-break, title, entries, entries-allow-page-break: true, text-based: false, reversed: false) = {
  let children = entries.fields().at("children", default: (entries,))
  // Check actual content, not section names: distinct YAML keys may format alike.
  if children.any(it => it != [] and it != [ ] and it.func() != parbreak) {
    let body = if reversed { reversed-numbered-entries(entries) } else { entries }
    if text-based { body = content-area(body) }
    body = sidebar-entry-policy(entries-allow-page-break, body)
    metadata((
      sidebarcv: true,
      placement: placement,
      body: sidebar-section(allow-page-break, [#metadata(none)<sidebarcv-section-start>] + title + body),
      header-body: body,
    ))
  }
}

#let sidebar-columns(main, sidebar) = {
  if main == [] or sidebar == [] {
    main + sidebar
  } else {
    grid(
      columns: ({{ 1 - design.sidebar_width }}fr, {{ design.sidebar_width }}fr),
      column-gutter: {{ design.column_gap }},
      grid.cell(breakable: true, main),
      grid.cell(breakable: true, sidebar),
    )
  }
}

#show: doc => {
  set strong(delta: {{ design.typography.bold_weight - 400 }})
  let sidebar = []
  let header-extra = []
  let header-render = extra => extra
  let flow = ()
  for child in doc.children {
    if child.func() == metadata and type(child.value) == dictionary {
      if child.value.at("sidebarcv_header", default: false) {
        header-render = child.value.render
      } else if child.value.at("sidebarcv", default: false) {
        if child.value.placement == "sidebar" {
          sidebar += child.value.body
        } else if child.value.placement == "header" {
          header-extra += child.value.header-body
        } else {
          flow.push(child.value)
        }
      } else {
        child
      }
    } else {
      child
    }
  }
  header-render(header-extra)
  // Prevent RenderCV's outer content-area from making the entire grid unbreakable.
  metadata("skip-content-area")
  let main = []
  let ended = false
  for section in flow {
    if not ended and section.placement == "main" {
      main += section.body
    } else {
      if main != [] {
        sidebar-columns(main, sidebar)
        main = []
        sidebar = []
        ended = true
      }
      section.body
    }
  }
  sidebar-columns(main, sidebar)
}
