#sidebar-capture(
  "{{ design.placement(snake_case_section_title) }}",
  {{ design.section_page_break(snake_case_section_title)|lower }},
  [#heading(level: 2)[{{ section_title }}]],
  entries-allow-page-break: {{ design.section_entries_page_break(snake_case_section_title)|lower }},
  text-based: {{ (entry_type in ["BulletEntry", "NumberedEntry", "ReversedNumberedEntry"])|lower }},
  reversed: {{ (entry_type == "ReversedNumberedEntry")|lower }},
  [
{% set options = design.sections.overrides.get(snake_case_section_title) %}
    #let sidebar-stacked-details = {{ (options.stacked_details if options else false)|lower }}
    #let sidebar-stacked-separator = "{{ options.stacked_separator if options else ',' }}"
    #let sidebar-strip-trailing-period = {{ (options.strip_trailing_period if options else false)|lower }}
{% set capitalize = options.capitalize_stacked_details if options else false %}
{% if capitalize is boolean %}
    #let sidebar-capitalize-stacked-details(label) = {{ capitalize|lower }}
{% else %}
    #let sidebar-capitalize-stacked-details(label) = label in (
{% for label in capitalize %}
      "{{ design.typst_label(label, settings.bold_keywords)|replace('\\', '\\\\')|replace('"', '\\"')|replace('\n', '\\n') }}",
{% endfor %}
    )
{% endif %}
    #let sidebar-entries-allow-page-break = {{ design.section_entries_page_break(snake_case_section_title)|lower }}
