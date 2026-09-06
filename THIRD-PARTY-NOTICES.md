# Third-Party Notices

GuiBuilder itself is © 2026 Rahil Kasimi and is distributed under the MIT
License (see `LICENSE`). GuiBuilder is **not** redistributing the source code
of any of the packages below — they are ordinary `pip` dependencies declared
in `requirements.txt`/`setup.cfg`/`pyproject.toml` and installed separately by
each user. This file exists so that anyone packaging, forking, or
redistributing GuiBuilder (including as a built `.exe`) understands what
they're also pulling in, and what obligations — if any — come with it.

Nothing below is legal advice. If you plan a commercial redistribution at
scale, especially of PyInstaller-built executables, have counsel confirm this
analysis against the exact dependency versions you ship.

---

## 1. Runtime / build dependencies (installed via `pip`, not vendored)

| Package | License | Copyleft? | Notes |
|---|---|---|---|
| [Pillow](https://github.com/python-pillow/Pillow) | HPND ("PIL Software License") | No | Permissive, MIT/BSD-like. Requires preserving the copyright/permission notice if you redistribute Pillow's own files (you normally don't — pip does). |
| [pandas](https://github.com/pandas-dev/pandas) | BSD-3-Clause | No | Permissive. |
| [openpyxl](https://foss.heptapod.net/openpyxl/openpyxl) | MIT | No | Permissive. |
| [tkcalendar](https://github.com/j4321/tkcalendar) | **GPL-3.0-or-later** | **Yes** | See §2 below — this is the one dependency that needs a deliberate decision, not just a notice. |
| [PyInstaller](https://github.com/pyinstaller/pyinstaller) | GPL-2.0-or-later, **with a Bootloader Exception** | Only if you modify PyInstaller itself | See §3 below. Used only as a build tool invoked by GuiBuilder's "Convert to EXE" feature; PyInstaller's own source is not vendored into this repository. |
| Python `tkinter` / `ttk` / standard library | Python Software Foundation License 2.0 | No | Ships with the CPython distribution; not vendored here. |

Run `pip-licenses` (or an equivalent SBOM tool) against your actual locked
environment before shipping, since transitive dependencies of pandas/Pillow
etc. can change between versions.

---

## 2. tkcalendar (GPL-3.0-or-later) — read this before shipping a `.exe`

`tkcalendar` is licensed under the **GNU GPL v3 or later**, a copyleft
license. This matters in two different ways for two different artifacts:

**a) GuiBuilder the application (the code in this repository).**
GuiBuilder imports `tkcalendar` at runtime as an ordinary installed library
(`pip install tkcalendar`), the same way it imports Pillow or pandas. It does
not copy, modify, or statically bundle `tkcalendar`'s source into this
repository. Treating an interpreter-level `import` of a separately-installed
GPL library as a "mere aggregation" (not a combined/derivative work for
distribution purposes) is the common practice for MIT-licensed Python
front-ends, and is why GuiBuilder's own MIT license on its own source code is
not automatically overridden here. This is the standard interpretation, not
a settled point of law — if your risk tolerance is low, see the "safer
alternative" note at the end of this section.

**b) The Python applications GuiBuilder *generates* for end users, once
packaged into a `.exe`.**
This is the case that actually needs attention. If a user's generated
application uses the **Calendar** or **DateTimePicker** widgets, the
generated Python source contains `from tkcalendar import Calendar`. When that
generated application is packaged with **Convert to EXE**, GuiBuilder invokes
PyInstaller with `--collect-all tkcalendar`, which copies tkcalendar's
compiled code and locale data directly *into* the resulting single
executable. At that point the `.exe` is no longer "aggregation" — it's a
combined binary that statically incorporates GPL-3.0 code, so **that specific
executable is subject to GPLv3's copyleft terms**: whoever distributes it
must also make the corresponding complete source (including their own
generated application code) available under GPL-compatible terms, along with
a copy of the GPLv3 license text.

This obligation attaches to **the generated `.exe`, not to GuiBuilder
itself** — GuiBuilder's own MIT license is unaffected — but it will surprise
a user who expected to ship a closed-source commercial executable.

**What to do about it:**
- Document this clearly in GuiBuilder's own README/Help Guide wherever
  Calendar/DateTimePicker and "Convert to EXE" are mentioned (a short pointer
  to this section is enough).
- Users who need a closed-source `.exe` should avoid the Calendar/
  DateTimePicker widgets, or replace `tkcalendar` in their generated project
  with a permissively-licensed date-picker before building.
- Users who are fine with GPLv3 obligations for that one generated
  executable can proceed as-is.

A copy of the GPL-3.0 license text should be included in any distribution
that bundles `tkcalendar` (source or compiled): <https://www.gnu.org/licenses/gpl-3.0.txt>

---

## 3. PyInstaller (GPL-2.0-or-later, with Bootloader Exception)

PyInstaller is GPL-licensed, but its **Bootloader Exception** specifically
permits linking/embedding its compiled bootloader into other programs and
distributing the result "with whatever license you want" — that's precisely
what the "Convert to EXE" feature does. Using PyInstaller unmodified, as
GuiBuilder does, does not impose GPL terms on the executables it produces (the
tkcalendar situation in §2 is a separate, unrelated concern about
*tkcalendar's* license, not PyInstaller's). GPL only re-attaches if someone
modifies PyInstaller's own source and redistributes that modified copy.

---

## 4. Bundled image asset — `resources/wp1909426_4.jpg`

The archive supplied for this project contains a stock/desktop-wallpaper-style
space image at `resources/wp1909426_4.jpg`. The filename follows the naming
convention used by wallpaper-aggregator sites, and **no license, attribution,
or proof of ownership was included with the project**. Its actual license is
unknown.

**Recommendation: do not publish this file in the public repository under the
MIT license**, and do not represent it as covered by GuiBuilder's MIT grant.
Concretely, do one of the following before making the repo public:

- Remove `resources/wp1909426_4.jpg` entirely (simplest, safest — nothing in
  the codebase requires this specific image to function; it's sample/demo
  content), or
- Replace it with an image you personally created, or one under a verified
  permissive/public-domain license (e.g. CC0 from a site that clearly grants
  it), and record that source in this file, or
- If you can verify the original source and license (e.g. you purchased a
  license or it's your own photo/render), add an accurate entry here with
  the license terms and required attribution instead of this placeholder.

Until one of those is done, this file should be treated as **excluded** from
the MIT grant described in `LICENSE`, and it is *not* covered by the
"free for personal and commercial use" statement in the README.

---

## 5. GuiBuilder's own embedded runtime code

`gui_builder/instrumentation_widgets.py` and `gui_builder/image_support.py`
contain original GuiBuilder code (the instrumentation-widget runtime, the
`apply_background`/`apply_content` helpers, and `BuilderDateTimePicker`) that
GuiBuilder copies verbatim into the Python source it generates for users.
This code is authored as part of this project and is covered by the same MIT
license as the rest of the repository — the generated copies remain MIT-licensed
along with whatever license the user chooses for the rest of their generated
application. This is unrelated to the tkcalendar concern in §2, which is
about a genuine third-party GPL dependency, not GuiBuilder's own code.

---

## Regenerating this file

If dependencies change, regenerate the table in §1 (e.g. with
`pip-licenses --format=markdown` in a clean virtual environment built from
the current `requirements.txt`) and re-check any newly added packages against
their upstream `LICENSE`/`COPYING` files — package metadata license
classifiers are sometimes wrong or missing.
