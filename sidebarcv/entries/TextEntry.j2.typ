#sidebar-text-entry(sidebar-entries-allow-page-break)[
  #if sidebar-stacked-details [
    #sidebar-stacked-items(separator: sidebar-stacked-separator, capitalize: sidebar-capitalize-stacked-details(none))[#if sidebar-strip-trailing-period [{{ entry.removesuffix('.') }}] else [{{ entry }}]]
  ] else [
    {{ entry }}
  ]
]
