# Third-party notices

SidebarCV is an independent theme for [RenderCV](https://github.com/rendercv/rendercv),
tested with version 2.8. Its header template and theme model derive from RenderCV's
classic theme; remaining built-in templates and the RenderCV Typst library are used
through the installed RenderCV dependency. This is not an official RenderCV theme.

## RenderCV

[Upstream license, v2.8](https://github.com/rendercv/rendercv/blob/v2.8/LICENSE):

MIT License

Copyright (c) 2023 to present Sina Atalay and individual contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Optional Source Sans 3 fonts

`extras/fonts/` contains unmodified Semibold and Semibold Italic TTF files from
[Adobe Source Sans 3.052R](https://github.com/adobe-fonts/source-sans/releases/tag/3.052R).
Their license is SIL Open Font License 1.1, **not** this repository's MIT license.
The complete copyright and license accompany the files in
[`extras/fonts/LICENSE.md`](extras/fonts/LICENSE.md).

Original Git blob identifiers, checked against the release:

- `SourceSans3-Semibold.ttf`: `4aff9a3aea9b5f1e746f03ed40e1b293740dc8a2`
- `SourceSans3-SemiboldIt.ttf`: `74c566168c2ba07db9c88647738bfc4565998910`

The default theme and gallery use RenderCV's bundled fonts and do not require
these additional faces. For optional installation, see the font recipe in the guide.
