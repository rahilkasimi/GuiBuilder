# Contributing to GuiBuilder

Thanks for considering a contribution. This file summarizes the workflow
described in the main [README](README.md#contributing) — see that section
for the full recommended workflow and the PR checklist.

## Quick start

1. Fork the repository and create a feature branch.
2. Set up a virtual environment and install `requirements.txt`.
3. Make the smallest coherent change that solves the problem; preserve
   existing behavior unless the change explicitly intends to modify it.
4. Update `gui_builder/help_mixin.py`'s `ELEMENT_HELP` / `PROPERTY_HELP` /
   `TOOLTIP_HELP` tables for any new widget or property — the in-app Help
   Guide and Context Help Mode are generated from that same metadata.
5. Update `README.md` for any user-facing change.
6. Validate generated Python source with syntax checking, and run through
   the manual test pass in the README's [Testing and Validation](README.md#testing-and-validation)
   section for anything you touched.
7. Open a pull request describing the problem, the solution, regression
   considerations, and the validation you performed.

## Licensing of contributions

By submitting a pull request, you agree that your contribution is licensed
under this project's [MIT License](LICENSE).

Do not submit code, assets, or third-party snippets you don't have the
right to license under MIT. If your change adds a new dependency, add it to
`requirements.txt` **and** to [`THIRD-PARTY-NOTICES.md`](THIRD-PARTY-NOTICES.md)
with its license, and flag in your PR description if it's copyleft (GPL/LGPL/etc.)
so it gets the same scrutiny `tkcalendar` got.
