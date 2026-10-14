{% set entry = design.prepare_entry(entry) %}
{% if entry.tags is defined %}
{% set tag_line = "#emph[" ~ entry.tags ~ "]" %}
{% set lines = [] %}
{% for line in entry.main_column.splitlines() %}
{% set styled = "#text(fill: " ~ design.colors.tags ~ ")[" ~ line ~ "]" if design.colors.tags is not none else line %}
{% set _ = lines.append("#summary[" ~ styled ~ "]" if line == tag_line else line) %}
{% endfor %}
{% set entry = entry.model_copy(update={"main_column": lines|join('\n')}) %}
{% endif %}
{% include "typst/entries/ExperienceEntry.j2.typ" %}
