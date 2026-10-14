#sidebar-text-entry(sidebar-entries-allow-page-break)[
  #if sidebar-stacked-details [
    #strong[{{ entry.label }}] \
    #sidebar-stacked-items(separator: sidebar-stacked-separator, capitalize: sidebar-capitalize-stacked-details("{{ entry.label|replace('\\', '\\\\')|replace('"', '\\"')|replace('\n', '\\n') }}"))[
      {{ entry.details }}
    ]
  ] else [
    {{ entry.main_column }}
  ]
]
