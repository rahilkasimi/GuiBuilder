# Tkinter Visual GUI Designer — SRP Modular Refactor

This package is a responsibility-oriented refactor of the original single-file GUI builder.

## Why this structure

The original application combined several unrelated responsibilities inside one `GUIBuilderApp` class:

- application/bootstrap state
- visual UI construction
- toolbox management
- canvas hit-testing, dragging and resizing
- widget hierarchy and notebook tabs
- property inspection and live property editing
- design persistence
- undo/redo
- generated Python source
- preview execution and EXE conversion
- code-editor parsing, syntax checking and custom-code preservation

The refactor keeps the same application-level object, but moves each responsibility into a focused module. The application class is now a composition root that inherits the responsibility-specific mixins.

## Project structure

```text
gui_builder.py                  # Launcher / entry point
requirements.txt

gui_builder/
├── __init__.py
├── app.py                      # GUIBuilderApp composition root + initialization
├── dependencies.py             # Shared imports and optional dependency detection
├── config.py                   # Constants, widget catalogue, property metadata, mappings
├── models.py                   # DesignElement domain model + serialization
├── renderer.py                 # Canvas rendering only
├── code_generator.py           # Generated application source-code generation
├── ui_mixin.py                 # Main window, toolbar, toolbox, zoom, tooltips, UI shell
├── canvas_mixin.py             # Canvas interaction, selection, drag/resize, hierarchy
├── properties_mixin.py         # Property inspector and live property updates
├── project_mixin.py            # Save/load, undo/redo, new design, project state
└── code_mixin.py               # Live code, code editor, syntax check, preview, EXE build
```

## SRP responsibilities

### `models.py`
Owns the `DesignElement` data model. It knows how an element represents itself and how it is serialized/deserialized, but does not know how the GUI is drawn or how code is generated.

### `renderer.py`
Owns visual rendering of elements on the design canvas. It does not decide what an element means, how a project is saved, or how Python source is produced.

### `code_generator.py`
Owns conversion of the current design model into executable Python/Tkinter source (plain `tkinter`/`ttk` -- see "CustomTkinter migration" below). The GUI itself delegates generation to this class.

### `canvas_mixin.py`
Owns interaction with the design canvas: hit testing, selection, drag/resize, parenting, notebook-tab placement, copy/paste, delete and canvas-related state transitions.

### `properties_mixin.py`
Owns the property inspector and the logic that translates property changes into model/canvas/code updates.

### `project_mixin.py`
Owns project persistence and history concerns: save/load, new design, undo and redo.

### `code_mixin.py`
Owns code synchronization and developer-facing execution workflows: incremental/full regeneration, code-editor synchronization, syntax validation, preview execution, and PyInstaller/EXE conversion.

### `ui_mixin.py`
Owns construction of the application shell and reusable UI behaviors such as toolbar/toolbox setup, view toggling, tooltip handling, and zoom controls.

### `app.py`
Owns application composition and initial state. It deliberately contains the original initialization flow rather than duplicating that logic across modules.

## Compatibility approach

This refactor deliberately uses mixins instead of introducing a deep service/event architecture.

That gives two useful properties:

1. Existing calls such as `self._update_code()`, `self._save_state()`, `self._show_properties()`, and `self._on_canvas_drag()` continue to work.
2. The application still behaves as one cohesive `GUIBuilderApp` from the UI's point of view.

The goal is separation of responsibilities without changing the application's interaction model.

## Entry point

Run:

```bash
python gui_builder.py
```

Install dependencies first:

```bash
pip install -r requirements.txt
```

## CustomTkinter migration

The builder's own UI and every app it generates now use plain `tkinter`/`ttk`
instead of CustomTkinter -- there is no `customtkinter` dependency anywhere
in this project any more. Notably:

- `config.py`'s old `CTK_WIDGET_MAP`/`CTK_PROP_MAP`/`CTK_UNSUPPORTED_PROPS`/
  `LEGACY_RAW_PROP_OVERRIDE` translation tables are gone -- every element
  type's `ELEMENT_TYPES[...]["widget"]` entry is already a real
  tkinter/ttk class name, and most property dict keys already match their
  real tkinter/ttk constructor keyword directly (see
  `SKIPPED_GENERIC_PROPS` for the small remaining exception list).
- `ui_mixin.py` adds a small `_VScrollFrame` helper (a Canvas + inner Frame
  + Scrollbar) as the one place plain tkinter needed genuinely new code --
  it has no built-in equivalent to `CTkScrollableFrame`.
- Generated apps no longer need `customtkinter` installed to run, and
  Convert-To-EXE no longer needs the `--collect-all customtkinter`
  PyInstaller flag.
- `CodeGenerator.generate()` and `CodeGenerator.generate_element_lines()`
  were also de-duplicated as part of this migration -- `generate()` now
  calls `generate_element_lines()` once per element instead of separately
  reimplementing the same per-element logic.

## Validation performed

- All extracted Python modules pass `py_compile` syntax validation.
- All 91 non-`__init__` methods originally belonging to `GUIBuilderApp` are present in the five responsibility mixins.
- The new `GUIBuilderApp` imports and launches successfully with only the packages in `requirements.txt` installed (no `customtkinter`).
- The original `BASE_DIR` behavior was preserved by anchoring it to the project root rather than the new package directory.

## Important note

This is an architectural refactor, not a feature rewrite. The intent is to preserve behavior while making future changes safer. In particular, the existing live-code synchronization and syntax-checking behavior remains in the code-editor responsibility module; the original implementation already performs AST-based syntax validation before offering the user the option to save code containing errors.
