{% macro photo() %}
#pad(left: {{ design.header.photo_space_left }}, right: {{ design.header.photo_space_right }}, image("{{ cv.photo.name }}", width: {{ design.header.photo_width }}))
{% endmacro %}

#metadata((
  sidebarcv_header: true,
  render: extra => [
{% if cv.photo %}
    #grid(
      columns: {% if design.header.photo_position == "left" %}(auto, 1fr){% else %}(1fr, auto){% endif %},
      column-gutter: 0cm,
      align: {{ "horizon" if design.header.photo_vertical_alignment == "center" else design.header.photo_vertical_alignment }} + left,
{% if design.header.photo_position == "left" %}
      [{{ photo() }}],
{% endif %}
      [
{% endif %}
{% if cv.name %}
= {{ cv.name }}
{% endif %}

{% if cv.headline %}
#headline([{{ cv.headline }}])
{% endif %}
{% if design.header.connections.placement == "header" %}
#connections(
{% for connection in cv._connections %}
  [{{ connection }}],
{% endfor %}
)
{% endif %}
#extra
{% if cv.photo %}
      ],
{% if design.header.photo_position == "right" %}
      [{{ photo() }}],
{% endif %}
    )
{% endif %}
{% if cv.name or cv.headline or cv.photo or (design.header.connections.placement == "header" and cv._connections) %}
    #v({{ design.section_titles.space_above }})
{% else %}
    #if extra != [] { v({{ design.section_titles.space_above }}) }
{% endif %}
  ],
))

{% if design.header.connections.placement == "sidebar" and cv._connections %}
#sidebar-capture("sidebar", true,
  [#heading(level: 2, "{{ design.header.connections.sidebar_title|replace('\\', '\\\\')|replace('"', '\\"')|replace('\n', '\\n') }}")],
  [
    #set align({% if locale.is_rtl %}right{% else %}left{% endif %})
    #set par(spacing: 0pt, leading: {{ design.typography.line_spacing }} * 1.7, justify: false)
    #set text(
      fill: {{ design.colors.connections.as_rgb() }},
      font: "{{ design.typography.font_family.connections }}",
      size: {{ design.typography.font_size.connections }},
      weight: {% if design.typography.bold.connections %}700{% else %}400{% endif %},
    )
{% for connection in cv._connections %}
    {% if design.typography.small_caps.connections %}#smallcaps[{{ connection }}]{% else %}{{ connection }}{% endif %}
{% if not loop.last %}
    #linebreak()
{% endif %}
{% endfor %}
  ],
  text-based: true,
)
{% endif %}
