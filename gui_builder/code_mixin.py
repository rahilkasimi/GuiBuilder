import traceback
"""Generated-code lifecycle, preview/build and code editor."""
from openpyxl.styles.builtins import accent_6

from .dependencies import *
from .config import *
from .models import DesignElement
from .code_generator import CodeGenerator


class CodeMixin:
        def _insert_code_for_new_elements(
                self, new_elems: List[DesignElement]
                ) -> bool:
            if not self.full_code:
                return False

            # Shared/generated helper blocks for Scrollbars and instrumentation
            # widgets are intentionally regenerated as a unit. This keeps
            # target bindings and embedded runtime helper classes consistent.
            special_runtime_types = {
                "Scrollbar", "PushButton", "RadioButton", "LEDDigit",
                "LEDDisplay", "LEDIndicator", "Gauge", "MeasurementDisplay",
            }
            if any(e.elem_type in special_runtime_types for e in new_elems):
                return False

            # If any of the new elements need a tooltip and the reusable
            # _ToolTip helper class isn't in the script yet, bail out to the
            # full regenerate path (CodeGenerator.generate()) instead of
            # trying to splice the class definition in here -- that keeps the
            # helper-injection logic in exactly one place.
            if any(e.props.get("tooltip") for e in new_elems) and "_ToolTip" not in self.full_code:
                return False

            lines = self.full_code.splitlines(True)

            class_start = None
            for i, line in enumerate(lines):
                if line.startswith("class MainApplication:"):
                    class_start = i
                    break
            if class_start is None:
                return False

            init_start = None
            for i in range(class_start, len(lines)):
                if lines[i].startswith("    def __init__(self, root):"):
                    init_start = i
                    break
            if init_start is None:
                return False

            main_guard_idx = None
            for i, line in enumerate(lines):
                if line.startswith("if __name__ == '__main__':"):
                    main_guard_idx = i
                    break
            if main_guard_idx is None:
                main_guard_idx = len(lines)

            init_end = None
            for i in range(init_start + 1, min(len(lines), main_guard_idx)):
                line = lines[i]
                if line.strip() and line.startswith(" " * 4) and not line.startswith(" " * 8):
                    init_end = i
                    break
            if init_end is None:
                init_end = main_guard_idx

            existing_vars = set()
            for line in lines[init_start:init_end]:
                match = re.match(r'        self\.(\w+) = (?:tk\.(?:IntVar|StringVar|DoubleVar|BooleanVar)|ttk\.\w+Var)\(', line)
                if match:
                    existing_vars.add(match.group(1))

            new_vars = {}
            for elem in new_elems:
                if elem.elem_type in ("Radiobutton", "Checkbutton"):
                    var_name = elem.props.get("variable")
                    if var_name:
                        if elem.elem_type == "Checkbutton":
                            new_vars[var_name] = "tk.IntVar(value=0)"
                        else:
                            new_vars.setdefault(var_name, "tk.StringVar(value='')")
                elif elem.elem_type == "Entry":
                    var_name = elem.props.get("textvariable")
                    if var_name:
                        new_vars.setdefault(var_name, "tk.StringVar(value='')")
            new_vars = {v: t for v, t in new_vars.items() if v not in existing_vars}

            init_lines = []
            for var, typ in new_vars.items():
                init_lines.append(f"        self.{var} = {typ}\n")

            for elem in new_elems:
                widget_line, place_line, extra_lines = CodeGenerator.generate_element_lines(
                    elem, self.elements
                    )
                init_lines.append(widget_line + "\n")
                for extra in extra_lines:
                    init_lines.append(extra + "\n")
                init_lines.append(place_line + "\n")

                event = DEFAULT_EVENT_MAP.get(elem.elem_type)
                if event and event != "command" and elem.handler_code.strip():
                    var_name = f"self._elem_{elem.elem_id}"
                    method_name = f"_on_{elem.elem_type}_{elem.elem_id}"
                    init_lines.append(
                        f"        {var_name}.bind('{event}', self.{method_name})\n"
                        )

            method_lines = []
            for elem in new_elems:
                if elem.handler_code.strip():
                    method_name = f"_on_{elem.elem_type}_{elem.elem_id}"
                    method_lines.append(f"    def {method_name}(self, event=None):\n")
                    code_lines = elem.handler_code.strip().splitlines() or ["pass"]
                    for cline in code_lines:
                        method_lines.append(f"        {cline}\n" if cline.strip() else "        \n")
                    method_lines.append("\n")

            required_imports = []
            if any(e.elem_type == "Table" for e in new_elems):
                required_imports.append("import pandas as pd")
            if any(e.elem_type == "Image" for e in new_elems):
                required_imports.append("import os")
                required_imports.append("from PIL import Image, ImageTk")
            if any(e.elem_type == "Calendar" for e in new_elems):
                required_imports.append("from tkcalendar import Calendar")
                required_imports.append("from datetime import date")
            last_import_idx = -1
            for i, line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    last_import_idx = i
            if last_import_idx != -1:
                existing_imports = [line.strip() for line in lines if line.startswith("import ") or line.startswith("from ")]
                for imp in required_imports:
                    if imp not in existing_imports:
                        lines.insert(last_import_idx + 1, imp + "\n")
                        last_import_idx += 1

            if init_lines:
                lines[init_end:init_end] = init_lines
                if main_guard_idx >= init_end:
                    main_guard_idx += len(init_lines)

            if method_lines:
                lines[main_guard_idx:main_guard_idx] = method_lines

            new_code = ''.join(lines)
            for elem in new_elems:
                if f"self._elem_{elem.elem_id} =" not in new_code:
                    return False

            self.full_code = new_code
            self._current_code = self.full_code
            self._update_code_display()
            return True

        def _remove_code_for_elements(self, elems: List[DesignElement]) -> bool:
            if not self.full_code or not elems:
                return False

            ids_to_remove = {e.elem_id for e in elems}
            lines = self.full_code.splitlines(True)
            indices_to_remove = set()

            i = 0
            while i < len(lines):
                line = lines[i]
                match = re.match(r'    def _on_(\w+)_(\d+)\(self, event=None\):', line)
                if match:
                    elem_id = int(match.group(2))
                    if elem_id in ids_to_remove:
                        start = i
                        i += 1
                        while i < len(lines) and (lines[i].startswith(" " * 8) or lines[i].strip() == ""):
                            i += 1
                        for j in range(start, i):
                            indices_to_remove.add(j)
                        continue
                i += 1

            for elem in elems:
                widget_pattern = rf'self\._elem_{elem.elem_id}\s*=\s*'
                widget_idx = None
                for i, line in enumerate(lines):
                    if re.search(widget_pattern, line):
                        widget_idx = i
                        break
                if widget_idx is None:
                    return False
                place_pattern = rf'self\._elem_{elem.elem_id}\s*\.place\s*\('
                place_idx = None
                for i in range(widget_idx + 1, len(lines)):
                    if re.search(place_pattern, lines[i]):
                        place_idx = i
                        break
                if place_idx is None:
                    return False
                for j in range(widget_idx, place_idx + 1):
                    indices_to_remove.add(j)
                bind_pattern = rf'self\._elem_{elem.elem_id}\s*\.bind\s*\('
                for i, line in enumerate(lines):
                    if re.search(bind_pattern, line):
                        indices_to_remove.add(i)

            if indices_to_remove:
                for idx in sorted(indices_to_remove, reverse=True):
                    del lines[idx]

            self.full_code = ''.join(lines)
            self._current_code = self.full_code
            self._update_code_display()
            return True

        def _update_code_display(self):
            """Refresh the read-only generated-code preview panel.

            This is called from many places (every keystroke while editing a
            property, every arrow-key nudge, every drag release, etc.), but the
            actual refresh is a full delete()+insert() of the whole generated
            script into a Tk Text widget, which triggers a full re-layout and
            gets slow once the script is a few hundred lines. self.full_code and
            self._current_code (the actual source of truth -- nothing reads the
            Text widget's content back out) are always updated synchronously by
            the caller before this runs, so debouncing the on-screen refresh
            never risks anyone seeing stale generated code -- it only delays how
            soon the *preview panel* catches up, by well under the time it takes
            to notice.
            """
            if getattr(self, "_code_display_timer", None):
                self.root.after_cancel(self._code_display_timer)
            self._code_display_timer = self.root.after(120,
                                                          self._apply_code_display
                                                          )

        def _apply_code_display(self):
            self._code_display_timer = None
            if self.full_code is None:
                return
            self.code_text.configure(state="normal")
            self.code_text.delete("1.0", tk.END)
            self.code_text.insert(tk.END, self.full_code)
            self.code_text.configure(state="disabled")

        def _regenerate_full_code(self):
            self.full_code = CodeGenerator.generate(
                self.elements, self.window_title, (self.CANVAS_W, self.CANVAS_H),
                self.CANVAS_BG, self.canvas_imports,
                self.custom_module_code, self.custom_class_code,
                getattr(self, "WINDOW_STATE", "Normal"),
                getattr(self, "WINDOW_LOCKED", False)
            )
            self._current_code = self.full_code
            self._update_code_display()

        def _invalidate_full_code(self):
            self.full_code = None

        def _ensure_header_imports(self, needed_imports: List[str]) -> None:
            """Make sure each given "import ..." line is present in
            self.full_code's header, inserting any that are missing right
            after the existing import block.

            The incremental code-patch paths (_update_code_for_element,
            _insert_code_for_new_elements) only splice in a single element's
            own body lines -- unlike a full CodeGenerator.generate()
            regenerate, they have no way to also update the imports section.
            An Image element's generated code needs "import os" and
            "from PIL import Image" in the header; if that element's first
            appearance in the script went through one of the incremental
            paths rather than a full regenerate, those lines would never get
            added and the generated script would fail with a NameError the
            moment it actually tried to load the image.
            """
            if not self.full_code:
                return
            missing = [imp for imp in needed_imports if imp not in self.full_code]
            if not missing:
                return
            lines = self.full_code.splitlines(True)
            insert_at = 0
            for i, line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    insert_at = i + 1
            for imp in reversed(missing):
                lines.insert(insert_at, imp + "\n")
            self.full_code = "".join(lines)
            self._current_code = self.full_code

        def _update_code(self):
            if self.full_code is not None:
                code = self.full_code
            else:
                code = CodeGenerator.generate(
                    self.elements, self.window_title,
                    (self.CANVAS_W, self.CANVAS_H),
                    self.CANVAS_BG, self.canvas_imports,
                    self.custom_module_code, self.custom_class_code,
                    getattr(self, "WINDOW_STATE", "Normal"),
                    getattr(self, "WINDOW_LOCKED", False)
                )
                self.full_code = code
            self._current_code = code
            self._update_code_display()

        def _window_title_changed(self):
            if hasattr(self, "title_var"):
                self.window_title = self.title_var.get()
                if self.full_code:
                    self.full_code = re.sub(
                        r'root\.title\([^\)]+\)',
                        f'root.title({json.dumps(self.window_title)})',
                        self.full_code
                    )
                    self._current_code = self.full_code
                    self._update_code_display()
                self._schedule_save()

        def _copy_code(self):
            code = self._current_code
            self.root.clipboard_clear()
            self.root.clipboard_append(code)
            self._update_status("Code copied to clipboard.")

        def _run_preview(self):
            """Run the generated application inside a child Toplevel.

            Preview deliberately runs in-process.  Calling
            ``subprocess.Popen([sys.executable, ...])`` is unsafe in a
            PyInstaller-frozen build because ``sys.executable`` becomes
            GuiBuilder.exe, which starts a second GuiBuilder instance.
            """
            try:
                code = CodeGenerator.generate(
                    self.elements, self.window_title,
                    (self.CANVAS_W, self.CANVAS_H),
                    self.CANVAS_BG, self.canvas_imports,
                    self.custom_module_code, self.custom_class_code,
                    getattr(self, "WINDOW_STATE", "Normal"),
                    getattr(self, "WINDOW_LOCKED", False)
                )
            except Exception as e:
                messagebox.showerror(
                    "Run Preview Error",
                    f"Failed to generate code:\n{e}"
                )
                return

            if not code or not code.strip():
                messagebox.showerror(
                    "Run Preview Error",
                    "Generated code is empty - nothing to run."
                )
                return

            missing = self._missing_packages_for_code(code)
            if missing:
                names = ", ".join(pip_name for pip_name, _ in missing)
                proceed = messagebox.askyesno(
                    "Missing Dependencies",
                    f"The generated app needs the following package(s), "
                    f"which aren't installed in this Python environment:\n\n"
                    f"  {names}\n\nInstall them now and continue?"
                )
                if not proceed:
                    self._update_status(
                        "Run Preview cancelled — missing dependencies."
                    )
                    return

                self._update_status(f"Installing {names}...")
                self.root.update_idletasks()
                for pip_name, _import_name in missing:
                    if not self._pip_install(pip_name):
                        messagebox.showerror(
                            "Run Preview Error",
                            f"Failed to install {pip_name}. Install it "
                            f"manually, e.g.:\n\n"
                            f"    {sys.executable} -m pip install {pip_name}"
                        )
                        return

            temp_dir = None
            try:
                # Keep a real file location for generated Image elements and
                # any user code that relies on __file__.
                temp_dir = tempfile.mkdtemp(prefix="gui_preview_")
                temp_path = os.path.join(temp_dir, "preview.py")
                with open(temp_path, "w", encoding="utf-8") as f:
                    f.write(code)

                src_resources = os.path.join(BASE_DIR, "resources")
                if os.path.isdir(src_resources):
                    shutil.copytree(
                        src_resources,
                        os.path.join(temp_dir, "resources")
                    )

                # Only one preview is needed at a time. Close any previous
                # preview before creating a fresh one from the current design.
                old_preview = getattr(self, "_preview_window", None)
                if old_preview is not None and old_preview.winfo_exists():
                    self._close_preview(remove_window=True)

                preview_window = tk.Toplevel(self.root)
                preview_window.transient(self.root)
                preview_window.geometry(f"{max(320, int(self.CANVAS_W))}x{max(240, int(self.CANVAS_H))}")
                preview_window.resizable(True, True)

                # Compile/execute with a private module namespace. The
                # generated __main__ guard therefore does not create a second
                # Tk root. MainApplication is instantiated against this
                # already-created Toplevel, which is important for custom
                # Canvas-backed instrumentation widgets.
                preview_ns = {
                    "__name__": "__gui_builder_preview__",
                    "__file__": temp_path,
                    "__package__": None,
                    "__cached__": None,
                }
                exec(compile(code, temp_path, "exec"), preview_ns, preview_ns)
                app_class = preview_ns.get("MainApplication")
                if not isinstance(app_class, type):
                    preview_window.destroy()
                    raise RuntimeError(
                        "Generated code does not define MainApplication."
                    )
                preview_window.protocol(
                    "WM_DELETE_WINDOW",
                    lambda: self._close_preview()
                )

                self._preview_window = preview_window
                self._preview_temp_dir = temp_dir
                self._preview_namespace = preview_ns
                self._preview_app = None

                try:
                    self._preview_app = app_class(preview_window)
                    # Custom instrumentation controls use an inner Canvas.
                    # Force geometry propagation and an idle redraw before
                    # the preview is shown so their design-time sizes and
                    # positions are reflected deterministically.
                    preview_window.update_idletasks()
                    preview_window.update()

                    def _refresh_preview_widget_tree(widget):
                        redraw = getattr(widget, "_redraw", None)
                        if callable(redraw):
                            try:
                                redraw()
                            except tk.TclError:
                                pass
                        try:
                            children = widget.winfo_children()
                        except tk.TclError:
                            children = ()
                        for child in children:
                            _refresh_preview_widget_tree(child)

                    _refresh_preview_widget_tree(preview_window)
                    preview_window.update_idletasks()
                    preview_window.update()
                except Exception:
                    self._close_preview(remove_window=True)
                    raise

                # Give the generated app a useful native child-window title
                # even if custom code changes it during initialization.
                try:
                    preview_window.lift()
                    preview_window.focus_force()
                except Exception:
                    pass

                self._update_status("Running Code Preview...")

            except Exception as e:
                if temp_dir:
                    try:
                        shutil.rmtree(temp_dir, ignore_errors=True)
                    except Exception:
                        pass
                messagebox.showerror(
                    "Run Preview Error",
                    f"The preview could not be started:\n\n{traceback.format_exc()}"
                )

        def _close_preview(self, remove_window: bool = True):
            """Destroy the current preview Toplevel and release its temp files."""
            window = getattr(self, "_preview_window", None)
            self._preview_window = None
            self._preview_app = None
            self._preview_namespace = None

            if remove_window and window is not None:
                try:
                    if window.winfo_exists():
                        window.destroy()
                except Exception:
                    pass

            temp_dir = getattr(self, "_preview_temp_dir", None)
            self._preview_temp_dir = None
            if temp_dir:
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception:
                    pass

            self._update_status("Preview closed.")

        def _extract_method_body(self, lines: List[str], method_name: str) -> Optional[str]:
            """Pull the body of a single "    def <method_name>(...):" block out
            of a full script's lines, dedented back to handler_code's own
            no-indent convention. Returns None if the method isn't present
            (e.g. it was deleted, or was never in the script to begin with) so
            callers can distinguish "not found" from an intentionally-empty
            body.
            """
            def_index = next(
                (i for i, line in enumerate(lines)
                 if line.startswith(f"    def {method_name}(")), None
                )
            if def_index is None:
                return None
            end_index = len(lines)
            for i in range(def_index + 1, len(lines)):
                if lines[i].startswith("    def ") or lines[i].startswith(
                        "if __name__ =="
                        ):
                    end_index = i
                    break
            body_lines = lines[def_index + 1:end_index]
            cleaned = []
            for line in body_lines:
                cleaned.append(
                    line[8:] if line.startswith("        ") else (
                        "" if not line.strip() else line.strip())
                    )
            return "\n".join(cleaned).strip() or "pass"

        def _sync_all_handler_codes_from_lines(self, lines: List[str]) -> None:
            """Update every element's handler_code from a full script's text.

            Only _open_code_editor(elem) for one specific element used to sync
            that element's edited handler body back into elem.handler_code --
            editing through the general "Code Editor" (elem=None) left every
            _on_<Type>_<id> body you typed sitting only in the displayed text
            (self.full_code), never in the elements' own handler_code. Since a
            full regenerate always rebuilds strictly from handler_code (never
            from the displayed text), that meant any full regenerate -- adding
            an element, an image path change, undo/redo, etc. -- would silently
            discard those edits and fall back to each element's last real
            handler_code (often still the original "pass" placeholder). This
            keeps both editor entry points equivalent by doing the same
            per-method extraction for every element, not just a single one.
            """
            for e in self.elements:
                method_name = f"_on_{e.elem_type}_{e.elem_id}"
                body = self._extract_method_body(lines, method_name)
                if body is not None:
                    e.handler_code = body

        def _extract_top_level_imports(self, lines: List[str]) -> List[str]:
            """Return top-level import statements from the module header.

            Imports are project-level source code and must survive a full code
            regeneration.  Older versions only tracked the two built-in Tk
            imports in ``canvas_imports`` and treated other imports as an
            incidental part of ``custom_module_code``.  That made import
            preservation dependent on where a user happened to place the
            import relative to auto-managed imports.

            ``ast`` gives us reliable statement boundaries, including
            parenthesized/multi-line imports.  When the edited code is not
            parseable (the editor explicitly allows saving with syntax errors),
            a conservative line-based fallback preserves ordinary one-line
            imports rather than deleting them.
            """
            source = "\n".join(lines)
            try:
                tree = ast.parse(source)
                imports = []
                for node in tree.body:
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        start = node.lineno - 1
                        end = getattr(node, "end_lineno", node.lineno)
                        statement = "\n".join(lines[start:end]).strip()
                        if statement:
                            imports.append(statement)
                return imports
            except (SyntaxError, ValueError, TypeError):
                return [
                    line.strip()
                    for line in lines
                    if line.strip().startswith(("import ", "from "))
                    and not line.startswith((" ", "\t"))
                ]

        def _sync_project_imports_from_code(self, code: Optional[str] = None) -> None:
            """Synchronize the persistent project-import block with source code.

            ``full_code`` is the authoritative source while the code editor is
            open.  Keeping all top-level imports in ``canvas_imports`` makes
            subsequent full regenerations deterministic, regardless of whether
            the preceding operation was an element add, delete, property edit,
            undo/redo, preview, or another regeneration trigger.
            """
            source = self.full_code if code is None else code
            if not source:
                return

            lines = source.splitlines()
            imports = self._extract_top_level_imports(lines)
            if not imports:
                return

            # Preserve the order in which imports appear in the source while
            # collapsing exact duplicates.  This also repairs older .tvd files
            # whose canvas_imports field was incomplete.
            deduped = []
            seen = set()
            for imp in imports:
                if imp not in seen:
                    seen.add(imp)
                    deduped.append(imp)
            self.canvas_imports = "\n".join(deduped)

        def _extract_custom_regions(self, lines: List[str]) -> Tuple[str, str]:
            """Extract non-boilerplate user code while keeping imports durable.

            All module-level imports are removed from ``custom_module_code``
            and are persisted in ``canvas_imports`` instead.  This removes the
            old positional dependency where a custom import could disappear if
            another auto-managed import was added after it.
            """
            module_code = ""
            class_code = ""

            class_idx = next(
                (i for i, l in enumerate(lines)
                 if l.startswith("class MainApplication:")), None
            )

            if class_idx is not None:
                module_region = list(lines[:class_idx])

                # The generated docstring is boilerplate, not user module code.
                if module_region and module_region[0].startswith('"""Generated by Tkinter Visual Designer."""'):
                    module_region = module_region[1:]

                # Remove all top-level import statements, regardless of their
                # position.  Keep comments/blank lines and all other module code.
                try:
                    region_source = "\n".join(module_region)
                    tree = ast.parse(region_source)
                    remove_ranges = []
                    for node in tree.body:
                        if isinstance(node, (ast.Import, ast.ImportFrom)):
                            remove_ranges.append((node.lineno - 1, getattr(node, "end_lineno", node.lineno)))
                    for start_line, end_line in reversed(remove_ranges):
                        del module_region[start_line:end_line]
                except (SyntaxError, ValueError, TypeError):
                    # Syntax-error saves are allowed.  In that case remove only
                    # ordinary, unindented one-line imports.
                    module_region = [
                        line for line in module_region
                        if not (line.startswith(("import ", "from ")) and line.strip())
                    ]

                # Exclude the auto-generated tooltip helper if present.
                tt_start = next(
                    (i for i, l in enumerate(module_region)
                     if l.startswith("class _ToolTip:")), None
                )
                if tt_start is not None:
                    tt_end = tt_start + 1
                    while tt_end < len(module_region) and (
                            module_region[tt_end].startswith((" ", "\t"))
                            or not module_region[tt_end].strip()
                    ):
                        tt_end += 1
                    module_region[tt_start:tt_end] = []

                module_code = "\n".join(module_region).strip("\n")

            main_guard_idx = next(
                (i for i, l in enumerate(lines) if l.startswith("if __name__")),
                len(lines)
            )
            if class_idx is not None:
                class_region = lines[class_idx + 1:main_guard_idx]
                recognized_re = re.compile(r'^    def (__init__|_on_\w+_\d+)\(')
                def_starts = [i for i, l in enumerate(class_region)
                              if l.startswith("    def ")]
                custom_blocks = []
                for idx, start in enumerate(def_starts):
                    end = (def_starts[idx + 1] if idx + 1 < len(def_starts)
                           else len(class_region))
                    if not recognized_re.match(class_region[start]):
                        custom_blocks.extend(class_region[start:end])
                class_code = "\n".join(custom_blocks).rstrip("\n")

            return module_code, class_code

        def _detect_required_packages(self, code: str) -> List[Tuple[str, str]]:
            """(pip_package_name, import_name) pairs the generated code needs
            beyond the standard library, based on what it actually imports.
            Used both to make sure each one is actually installed in this
            Python environment (PyInstaller can only bundle what it can
            successfully import from) and to decide which PyInstaller flags
            the build needs (tkcalendar's locale data in particular isn't
            picked up by default static analysis and needs an explicit
            --collect-all).
            """
            packages = []
            if "import pandas" in code:
                packages.append(("pandas", "pandas"))
                # pandas' .xlsx engine is picked dynamically by string name at
                # runtime (df.to_excel/read_excel), not a static top-level
                # import PyInstaller's analysis can see, so it needs calling
                # out explicitly or the frozen exe fails only when a Table
                # element actually tries to load a workbook.
                packages.append(("openpyxl", "openpyxl"))
            if "from PIL import" in code:
                packages.append(("Pillow", "PIL"))
            if "from tkcalendar import Calendar" in code:
                packages.append(("tkcalendar", "tkcalendar"))
            return packages

        def _missing_packages_for_code(self, code: str) -> List[Tuple[str, str]]:
            """(pip_package_name, import_name) pairs from
            _detect_required_packages that aren't importable in this
            Python environment right now. Used by Run Preview to catch a
            missing dependency (most commonly tkcalendar, added on demand
            when a Calendar element is used) before launching the preview
            subprocess, instead of surfacing it as a raw traceback in the
            preview's stderr.
            """
            return [
                (pip_name, import_name)
                for pip_name, import_name in self._detect_required_packages(code)
                if importlib.util.find_spec(import_name) is None
                ]

        def _is_frozen(self) -> bool:
            """Return True when GuiBuilder itself is running as a PyInstaller EXE."""
            return bool(getattr(sys, "frozen", False))

        def _external_python_command(self) -> Optional[List[str]]:
            """Return a command that invokes a real Python interpreter.

            In a normal source run, ``sys.executable`` is the Python interpreter
            and is safe to use. In a PyInstaller build, ``sys.executable`` is
            GuiBuilder.exe itself; launching it with ``-m pip`` or ``-m PyInstaller``
            simply starts another GuiBuilder process (often an empty GUI window).
            Therefore frozen builds must resolve an external Python launcher.
            """
            if not self._is_frozen():
                return [sys.executable]

            # Windows Python launcher is a reliable choice when available.
            py_launcher = shutil.which("py")
            if py_launcher:
                return [py_launcher]

            candidates = [
                shutil.which("python"),
                shutil.which("python3"),
            ]
            for candidate in candidates:
                if candidate:
                    return [candidate]
            return None

        def _python_module_command(self, module: str, *args: str) -> Optional[List[str]]:
            """Build a command for ``python -m <module>`` without relaunching GuiBuilder."""
            python_cmd = self._external_python_command()
            if not python_cmd:
                return None
            return [*python_cmd, "-m", module, *args]

        def _pyinstaller_command(self) -> Optional[List[str]]:
            """Return a command that invokes PyInstaller without launching GuiBuilder.exe."""
            if not self._is_frozen():
                return [sys.executable, "-m", "PyInstaller"]

            # Prefer the standalone PyInstaller launcher in PATH.
            pyinstaller_exe = shutil.which("pyinstaller")
            if pyinstaller_exe:
                return [pyinstaller_exe]

            # Fall back to an external Python launcher.
            return self._python_module_command("PyInstaller")

        def _pip_install(self, pip_name: str) -> bool:
            """Best-effort `pip install <pip_name>` in this same Python
            environment, retrying without --break-system-packages if the
            first attempt rejects that flag. Returns True on success.
            """
            cmd = self._python_module_command("pip", "install", pip_name,
                                             "--break-system-packages")
            if cmd is None:
                return False
            ret = subprocess.run(cmd, capture_output=True, text=True)
            if ret.returncode != 0:
                retry_cmd = self._python_module_command("pip", "install", pip_name)
                if retry_cmd is None:
                    return False
                ret = subprocess.run(retry_cmd, capture_output=True, text=True)
            return ret.returncode == 0

        def _convert_to_exe(self, top: "tk.Toplevel",
                             text_widget: tk.Text) -> None:
            code = text_widget.get("1.0", "end-1c")
            if not code.strip():
                messagebox.showerror("Convert To EXE",
                                      "There's no code to build.", parent=top)
                return

            default_name = re.sub(r'[^A-Za-z0-9_-]+', '_',
                                   self.window_title or "MyApp").strip('_') or "MyApp"
            app_name = simpledialog.askstring(
                "Convert To EXE", "Name for the application:",
                initialvalue=default_name, parent=top
                )
            if not app_name:
                return
            app_name = re.sub(r'[^A-Za-z0-9_-]+', '_', app_name).strip('_') or "MyApp"

            out_dir = filedialog.askdirectory(
                title="Choose a folder to save the .exe into", parent=top
                )
            if not out_dir:
                return

            packages = self._detect_required_packages(code)
            uses_resources = os.path.isdir(os.path.join(BASE_DIR, "resources"))

            log_top = tk.Toplevel(self.root)
            log_top.title("Convert To EXE - Build Log")
            log_top.geometry("760x520")
            log_top.configure(bg=self._panel_bg)
            log_top.transient(top)

            status_var = tk.StringVar(value="Starting build...")
            tk.Label(log_top, textvariable=status_var, anchor="w",
                     font=("Segoe UI", 11, "bold"), bg=self._panel_bg,
                     fg=self._panel_fg
                     ).pack(fill=tk.X, padx=10, pady=(10, 4))

            log_frame = tk.Frame(log_top, bg=self._panel_bg)
            log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
            log_text = tk.Text(log_frame, font=("Consolas", 9), bg="#1E1E1E",
                                fg="#D4D4D4", wrap=tk.WORD, state="disabled")
            log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL,
                                        command=log_text.yview)
            log_text.configure(yscrollcommand=log_scroll.set)
            log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

            btn_row = tk.Frame(log_top, bg=self._panel_bg)
            btn_row.pack(fill=tk.X, padx=10, pady=(4, 10))
            close_btn = self._flat_button(btn_row, "Close", log_top.destroy)
            close_btn.configure(state="disabled")
            close_btn.pack(side=tk.RIGHT)

            log_q: "queue.Queue" = queue.Queue()

            def log(line: str):
                log_q.put(("line", line))

            def _append_log(line: str):
                log_text.configure(state="normal")
                log_text.insert(tk.END, line.rstrip("\n") + "\n")
                log_text.see(tk.END)
                log_text.configure(state="disabled")

            def _poll_log():
                try:
                    while True:
                        kind, payload = log_q.get_nowait()
                        if kind == "line":
                            _append_log(payload)
                        elif kind == "status":
                            status_var.set(payload)
                        elif kind == "done":
                            success, final_path = payload
                            close_btn.configure(state="normal")
                            if success:
                                status_var.set("✓ Build complete")
                                _append_log(f"\nSaved to: {final_path}")
                                messagebox.showinfo(
                                    "Convert To EXE",
                                    f"Build complete.\n\nSaved to:\n{final_path}",
                                    parent=log_top
                                    )
                            else:
                                status_var.set("✗ Build failed")
                                messagebox.showerror(
                                    "Convert To EXE",
                                    "Build failed. See the log window for "
                                    "details.",
                                    parent=log_top
                                    )
                            return  # stop polling, worker thread is done
                except queue.Empty:
                    pass
                log_top.after(100, _poll_log)

            def _stream_process(cmd: List[str], cwd: Optional[str] = None) -> int:
                proc = subprocess.Popen(
                    cmd, cwd=cwd, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, text=True, bufsize=1
                    )
                for line in proc.stdout:
                    log(line)
                proc.wait()
                return proc.returncode

            def _worker():
                try:
                    # 1. Make sure every package the generated code imports is
                    # actually installed in this Python environment first --
                    # PyInstaller can only bundle a module it can successfully
                    # import from, so a missing dependency needs fixing before
                    # the build even starts, not discovered as a cryptic
                    # failure partway through.
                    for pip_name, import_name in packages:
                        if importlib.util.find_spec(import_name) is None:
                            log_q.put(("status", f"Installing {pip_name}..."))
                            log(f"$ pip install {pip_name}")
                            pip_cmd = self._python_module_command(
                                "pip", "install", pip_name, "--break-system-packages"
                                )
                            if pip_cmd is None:
                                log(
                                    "No external Python interpreter was found. "
                                    "A frozen GuiBuilder cannot use GuiBuilder.exe "
                                    "as its Python interpreter."
                                )
                                log_q.put(("done", (False, None)))
                                return
                            ret = _stream_process(pip_cmd)
                            if ret != 0:
                                # Some environments don't recognize
                                # --break-system-packages; retry without it
                                # rather than failing outright on that alone.
                                retry_pip_cmd = self._python_module_command(
                                    "pip", "install", pip_name
                                    )
                                if retry_pip_cmd is None:
                                    log_q.put(("done", (False, None)))
                                    return
                                ret = _stream_process(retry_pip_cmd)
                            if ret != 0:
                                log(f"Failed to install {pip_name}.")
                                log_q.put(("done", (False, None)))
                                return
                        else:
                            log(f"Found {pip_name} (already installed).")

                    if importlib.util.find_spec("PyInstaller") is None:
                        log_q.put(("status", "Installing PyInstaller..."))
                        log("$ pip install pyinstaller")
                        pip_cmd = self._python_module_command(
                            "pip", "install", "pyinstaller", "--break-system-packages"
                            )
                        if pip_cmd is None:
                            log(
                                "No external Python interpreter was found, so "
                                "PyInstaller cannot be installed from the frozen builder."
                            )
                            log_q.put(("done", (False, None)))
                            return
                        ret = _stream_process(pip_cmd)
                        if ret != 0:
                            retry_pip_cmd = self._python_module_command(
                                "pip", "install", "pyinstaller"
                                )
                            if retry_pip_cmd is None:
                                log_q.put(("done", (False, None)))
                                return
                            ret = _stream_process(retry_pip_cmd)
                        if ret != 0:
                            log("Failed to install PyInstaller.")
                            log_q.put(("done", (False, None)))
                            return
                    else:
                        log("Found PyInstaller (already installed).")

                    # 2. Stage a clean build directory: the script plus a copy
                    # of resources/ (images used by Image elements), so the
                    # bundled asset paths match what the running app expects
                    # regardless of where this builder itself lives.
                    build_dir = tempfile.mkdtemp(prefix="gui_exe_build_")
                    script_path = os.path.join(build_dir, f"{app_name}.py")
                    with open(script_path, "w", encoding="utf-8") as f:
                        f.write(code)
                    if uses_resources:
                        log("Bundling resources/ (images used by Image elements).")
                        shutil.copytree(
                            os.path.join(BASE_DIR, "resources"),
                            os.path.join(build_dir, "resources")
                            )

                    dist_dir = os.path.join(build_dir, "dist")
                    work_dir = os.path.join(build_dir, "build")

                    pyinstaller_cmd = self._pyinstaller_command()
                    if pyinstaller_cmd is None:
                        log(
                            "PyInstaller could not be found. In a frozen GuiBuilder "
                            "build, install PyInstaller in the external Python environment "
                            "or make pyinstaller.exe available on PATH."
                        )
                        log_q.put(("done", (False, None)))
                        return

                    cmd = [
                        *pyinstaller_cmd,
                        "--noconfirm", "--onefile", "--windowed",
                        "--name", app_name,
                        "--distpath", dist_dir,
                        "--workpath", work_dir,
                        "--specpath", build_dir,
                        ]
                    if any(pip_name == "tkcalendar" for pip_name, _ in packages):
                        # tkcalendar ships its own locale/translation data as
                        # package resources (for month/weekday names), which
                        # PyInstaller's static import analysis doesn't pick
                        # up on its own -- needs calling out explicitly or
                        # the frozen exe only fails once a Calendar element
                        # actually tries to render month/weekday names.
                        cmd += ["--collect-all", "tkcalendar"]
                    if uses_resources:
                        sep = ";" if platform.system() == "Windows" else ":"
                        cmd += ["--add-data",
                                f"{os.path.join(build_dir, 'resources')}{sep}resources"]
                    cmd.append(script_path)

                    log_q.put(("status", "Running PyInstaller..."))
                    log("$ " + " ".join(cmd))
                    ret = _stream_process(cmd, cwd=build_dir)
                    if ret != 0:
                        log(f"PyInstaller exited with code {ret}.")
                        log_q.put(("done", (False, None)))
                        return

                    # 3. Copy the finished binary out of the throwaway build
                    # dir into wherever the user actually asked to save it.
                    exe_name = (f"{app_name}.exe" if platform.system() == "Windows"
                                else app_name)
                    built_path = os.path.join(dist_dir, exe_name)
                    if not os.path.exists(built_path):
                        log(f"Expected output not found: {built_path}")
                        log_q.put(("done", (False, None)))
                        return
                    final_path = os.path.join(out_dir, exe_name)
                    shutil.copy2(built_path, final_path)
                    log_q.put(("done", (True, final_path)))
                except Exception as e:
                    log(f"Unexpected error: {e}")
                    log_q.put(("done", (False, None)))

            threading.Thread(target=_worker, daemon=True).start()
            log_top.after(100, _poll_log)

        def _open_code_editor(self, elem: Optional[DesignElement] = None):
            existing = getattr(self, "_code_editor_window", None)
            if existing is not None:
                try:
                    if existing.winfo_exists():
                        existing.deiconify()
                        existing.lift()
                        existing.focus_force()
                        return
                except tk.TclError:
                    pass
                self._code_editor_window = None

            top = tk.Toplevel(self.root)
            self._code_editor_window = top
            top.title(f"Code Editor - {elem.elem_type} (ID: {elem.elem_id})"
                      if elem is not None else "Code Editor")
            top.geometry("900x680")
            top.minsize(650, 450)
            top.configure(bg=self._panel_bg)

            def _close_code_editor():
                if getattr(self, "_code_editor_window", None) is top:
                    self._code_editor_window = None
                try:
                    top.destroy()
                except tk.TclError:
                    pass

            top.protocol("WM_DELETE_WINDOW", _close_code_editor)

            # Bring window to front and focus it
            top.lift()
            top.focus()

            # --------------------------------------------------------------
            # Find / Replace state
            # --------------------------------------------------------------
            find_var = tk.StringVar()
            replace_var = tk.StringVar()
            search_status_var = tk.StringVar(value="")
            search_matches = []
            current_match = [0]
            search_generation = [0]

            editor_frame = tk.Frame(top, bg=self._panel_bg)
            editor_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            editor_frame.grid_rowconfigure(1, weight=1)
            editor_frame.grid_columnconfigure(0, weight=1)

            # Compact editor search bar. It stays above the editor and can be
            # toggled with Ctrl+F / Ctrl+H so it does not permanently consume
            # vertical space when the user is simply editing code.
            search_frame = tk.Frame(editor_frame, bg=self._panel_bg)
            search_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
            search_frame.grid_columnconfigure(1, weight=1)
            search_frame.grid_columnconfigure(4, weight=1)

            tk.Label(search_frame, text="Find:", bg=self._panel_bg,
                     fg=self._panel_fg).grid(row=0, column=0, padx=(2, 4), sticky="w")
            find_entry = tk.Entry(search_frame, textvariable=find_var,
                                  relief="solid", bd=1)
            find_entry.grid(row=0, column=1, padx=(0, 6), sticky="ew")

            tk.Label(search_frame, text="Replace:", bg=self._panel_bg,
                     fg=self._panel_fg).grid(row=0, column=2, padx=(2, 4), sticky="w")
            replace_entry = tk.Entry(search_frame, textvariable=replace_var,
                                     relief="solid", bd=1)
            replace_entry.grid(row=0, column=3, padx=(0, 6), sticky="ew")

            search_actions = tk.Frame(search_frame, bg=self._panel_bg)
            search_actions.grid(row=0, column=5, sticky="e")

            text_widget = tk.Text(editor_frame, font=("Consolas", 10),
                                   bg="#E0FFFF", fg="black", wrap=tk.NONE,
                                   undo=True, padx=8, pady=6
                                   )
            y_scroll = ttk.Scrollbar(editor_frame, orient=tk.VERTICAL,
                                      command=text_widget.yview
                                      )
            x_scroll = ttk.Scrollbar(editor_frame, orient=tk.HORIZONTAL,
                                      command=text_widget.xview
                                      )
            text_widget.configure(yscrollcommand=y_scroll.set,
                                   xscrollcommand=x_scroll.set
                                   )
            text_widget.grid(row=1, column=0, sticky="nsew")
            y_scroll.grid(row=1, column=1, sticky="ns")
            x_scroll.grid(row=2, column=0, sticky="ew")
            text_widget.tag_config("syntax_error", background="#FF4444",
                                    foreground="white"
                                    )
            text_widget.tag_config("search_match", background="#FFF2CC",
                                    foreground="black")
            text_widget.tag_config("search_current", background="#FFD54F",
                                    foreground="black")

            full_code = self._current_code
            text_widget.insert("1.0", full_code)

            def _clear_search_tags():
                try:
                    text_widget.tag_remove("search_match", "1.0", tk.END)
                    text_widget.tag_remove("search_current", "1.0", tk.END)
                except tk.TclError:
                    pass

            def _collect_matches():
                """Return every occurrence of the current Find text."""
                query = find_var.get()
                matches = []
                if not query:
                    return matches
                pos = "1.0"
                while True:
                    found = text_widget.search(query, pos, stopindex=tk.END,
                                               nocase=False)
                    if not found:
                        break
                    end_pos = text_widget.index(f"{found} + {len(query)} chars")
                    matches.append((found, end_pos))
                    # Advance by one character to avoid missing overlapping
                    # matches while still guaranteeing forward progress.
                    next_pos = text_widget.index(f"{found} + 1 chars")
                    if text_widget.compare(next_pos, ">=", tk.END):
                        break
                    pos = next_pos
                return matches

            def _update_search_display(preserve_position=False):
                """Refresh result highlighting and the 'N of M' indicator."""
                nonlocal search_matches
                _clear_search_tags()
                query = find_var.get()
                if not query:
                    search_matches = []
                    current_match[0] = 0
                    search_status_var.set("")
                    return

                old_anchor = None
                if preserve_position and search_matches:
                    old_index = min(max(current_match[0], 0), len(search_matches) - 1)
                    old_anchor = search_matches[old_index][0]

                search_matches = _collect_matches()
                if not search_matches:
                    current_match[0] = 0
                    search_status_var.set("0 matches")
                    return

                # When the text changes, try to keep the same visible location;
                # otherwise use the first match as the natural starting point.
                new_index = 0
                if old_anchor:
                    for i, (start_idx, _) in enumerate(search_matches):
                        if text_widget.compare(start_idx, "==", old_anchor):
                            new_index = i
                            break
                current_match[0] = min(new_index, len(search_matches) - 1)

                for start_idx, end_idx in search_matches:
                    text_widget.tag_add("search_match", start_idx, end_idx)
                start_idx, end_idx = search_matches[current_match[0]]
                text_widget.tag_remove("search_match", start_idx, end_idx)
                text_widget.tag_add("search_current", start_idx, end_idx)
                text_widget.mark_set("insert", start_idx)
                text_widget.see(start_idx)
                search_status_var.set(
                    f"{current_match[0] + 1} of {len(search_matches)} matches"
                )

            def _find_next(event=None):
                if not search_matches and find_var.get():
                    _update_search_display()
                elif not find_var.get():
                    _update_search_display()
                    find_entry.focus_set()
                    return "break"
                if not search_matches:
                    find_entry.focus_set()
                    return "break"
                current_match[0] = (current_match[0] + 1) % len(search_matches)
                _update_search_display(preserve_position=True)
                find_entry.focus_set()
                return "break"

            def _find_previous(event=None):
                if not search_matches and find_var.get():
                    _update_search_display()
                elif not find_var.get():
                    _update_search_display()
                    find_entry.focus_set()
                    return "break"
                if not search_matches:
                    find_entry.focus_set()
                    return "break"
                current_match[0] = (current_match[0] - 1) % len(search_matches)
                _update_search_display(preserve_position=True)
                find_entry.focus_set()
                return "break"

            def _replace_current():
                if not find_var.get():
                    return
                if not search_matches:
                    _update_search_display()
                if not search_matches:
                    return
                start_idx, end_idx = search_matches[current_match[0]]
                text_widget.delete(start_idx, end_idx)
                text_widget.insert(start_idx, replace_var.get())
                # Rebuild result positions because replacement can change text
                # length. Stay on the next occurrence when one exists.
                old_index = current_match[0]
                _update_search_display()
                if search_matches:
                    current_match[0] = min(old_index, len(search_matches) - 1)
                    _clear_search_tags()
                    for s_idx, e_idx in search_matches:
                        text_widget.tag_add("search_match", s_idx, e_idx)
                    s_idx, e_idx = search_matches[current_match[0]]
                    text_widget.tag_remove("search_match", s_idx, e_idx)
                    text_widget.tag_add("search_current", s_idx, e_idx)
                    text_widget.mark_set("insert", s_idx)
                    text_widget.see(s_idx)
                    search_status_var.set(
                        f"{current_match[0] + 1} of {len(search_matches)} matches"
                    )

            def _replace_all():
                query = find_var.get()
                if not query:
                    return
                replacement = replace_var.get()
                matches = _collect_matches()
                if not matches:
                    _update_search_display()
                    return
                # Replace backwards so earlier positions remain valid.
                for start_idx, end_idx in reversed(matches):
                    text_widget.delete(start_idx, end_idx)
                    text_widget.insert(start_idx, replacement)
                _update_search_display()

            def _find_entry_changed(*args):
                search_generation[0] += 1
                _update_search_display()

            find_var.trace_add("write", _find_entry_changed)

            self._flat_button(search_actions, "Previous", _find_previous,
                              side=tk.LEFT, padx=2)
            self._flat_button(search_actions, "Next", _find_next,
                              side=tk.LEFT, padx=2)
            self._flat_button(search_actions, "Replace", _replace_current,
                              side=tk.LEFT, padx=2)
            self._flat_button(search_actions, "Replace All", _replace_all,
                              side=tk.LEFT, padx=2)
            tk.Label(search_frame, textvariable=search_status_var, width=18,
                     anchor="e", bg=self._panel_bg, fg=self._muted_fg).grid(
                         row=1, column=5, sticky="e", padx=(0, 3), pady=(3, 0))

            method_name = (f"_on_{elem.elem_type}_{elem.elem_id}"
                            if elem is not None else None)
            if elem is not None:
                target = text_widget.search(f"def {method_name}", "1.0", tk.END
                                             ) or text_widget.search(
                    f"self._elem_{elem.elem_id}", "1.0", tk.END
                    )
                if target:
                    target = text_widget.index(f"{target} linestart")
                    text_widget.mark_set("insert", target)
                    text_widget.see(target)
                    text_widget.xview_moveto(0.0)
                    text_widget.tag_add("highlight", target, f"{target} lineend")
                    text_widget.tag_config("highlight", background="#FFF2CC",
                                            foreground="black"
                                            )

            syntax_bar = tk.Frame(top, height=28, bg=self._panel_bg)
            syntax_bar.pack(fill=tk.X, padx=5, pady=(0, 2))
            syntax_bar.pack_propagate(False)
            syntax_status_var = tk.StringVar(value="Ready")
            line_col_var = tk.StringVar(value="Ln 1, Col 1")
            syntax_status_label = tk.Label(syntax_bar,
                                            textvariable=syntax_status_var,
                                            anchor="w", bg=self._panel_bg,
                                            fg=self._panel_fg
                                            )
            syntax_status_label.pack(side=tk.LEFT, padx=8)
            line_col_label = tk.Label(syntax_bar, textvariable=line_col_var,
                                       anchor="e", bg=self._panel_bg,
                                       fg=self._panel_fg
                                       )
            line_col_label.pack(side=tk.RIGHT, padx=8)

            _syntax_timer_id = [None]

            def _check_syntax():
                text_widget.tag_remove("syntax_error", "1.0", tk.END)
                code = text_widget.get("1.0", "end-1c")
                try:
                    ast.parse(code)
                    syntax_status_var.set("✓ No syntax errors")
                    syntax_status_label.configure(fg="#1B7F3B")
                    return True
                except SyntaxError as e:
                    lineno = e.lineno or 1
                    msg = e.msg or "invalid syntax"
                    syntax_status_var.set(
                        f"✗ Syntax error (line {lineno}): {msg}"
                        )
                    syntax_status_label.configure(fg="#C62828")
                    try:
                        text_widget.tag_add("syntax_error", f"{lineno}.0",
                                             f"{lineno}.end"
                                             )
                    except Exception:
                        pass
                    return False

            def _schedule_check(event=None):
                if _syntax_timer_id[0] is not None:
                    try:
                        top.after_cancel(_syntax_timer_id[0])
                    except Exception:
                        pass
                _syntax_timer_id[0] = top.after(400, _check_syntax)
                # Code edits can invalidate match offsets, so refresh the
                # search index as the editor contents change.
                if find_var.get():
                    top.after_idle(lambda: _update_search_display())

            def _update_line_col(event=None):
                try:
                    idx = text_widget.index("insert")
                    line, col = idx.split(".")
                    line_col_var.set(f"Ln {line}, Col {int(col) + 1}")
                except Exception:
                    pass

            btn_frame = tk.Frame(top, bg=self._panel_bg)
            btn_frame.pack(fill=tk.X, padx=5, pady=5)

            def save_code():
                if not _check_syntax():
                    proceed = messagebox.askyesno(
                        "Syntax Error",
                        "The code contains a syntax error. Save anyway?",
                        parent=top,
                    )
                    if not proceed:
                        self._update_status("Save cancelled due to syntax error.")
                        return
                edited_code = text_widget.get("1.0", "end-1c")
                # Tabs mixed with spaces cause Python's TabError, and even when
                # they don't, a Tk Text widget's own tab-stop rendering can make
                # inconsistent indentation look fine on screen while the actual
                # saved characters aren't. expandtabs() aligns to the nearest
                # tab stop rather than naively swapping in a fixed count, so
                # existing space indentation lines up correctly either way.
                if "\t" in edited_code:
                    edited_code = edited_code.expandtabs(4)
                    text_widget.delete("1.0", tk.END)
                    text_widget.insert("1.0", edited_code)
                self.full_code = edited_code
                lines = edited_code.splitlines()
                # Capture every top-level import before any future full
                # regeneration.  This is intentionally done on every code save
                # so legacy designs and imports added anywhere in the header are
                # repaired into a stable project-level import block.
                self._sync_project_imports_from_code(edited_code)
                if elem is not None:
                    body = self._extract_method_body(lines, method_name)
                    if body is not None:
                        elem.handler_code = body
                else:
                    self._sync_all_handler_codes_from_lines(lines)
                self.custom_module_code, self.custom_class_code = \
                    self._extract_custom_regions(lines)
                self._update_code()
                self._save_state()
                if elem is not None:
                    self._update_status(
                        f"Saved full code and handler for {elem.elem_type} ID {elem.elem_id}."
                        )
                else:
                    self._update_status("Saved code.")
                refreshed = self._current_code
                text_widget.delete("1.0", tk.END)
                text_widget.insert("1.0", refreshed)
                if elem is not None:
                    pos = text_widget.search(f"def {method_name}", "1.0", tk.END)
                    if pos:
                        pos = text_widget.index(f"{pos} linestart")
                        text_widget.mark_set("insert", pos)
                        text_widget.see(pos)
                        text_widget.xview_moveto(0.0)
                if find_var.get():
                    _update_search_display()

            def open_in_vscode():
                edited_code = text_widget.get("1.0", tk.END)
                fd, temp_path = tempfile.mkstemp(suffix=".py")
                os.close(fd)
                with open(temp_path, "w", encoding="utf-8") as f:
                    f.write(edited_code)
                try:
                    subprocess.Popen(["code", temp_path], shell=True)
                    self._update_status(
                        "Opened temporary generated code in VS Code."
                        )
                except Exception as e:
                    messagebox.showerror("Execution Error",
                                          f"Could not launch VS Code. Ensure 'code' is in PATH.\n\n{e}",
                                          parent=top
                                          )

            self._flat_button(btn_frame, "💾 Save", save_code,
                              accent=True, side=tk.LEFT, padx=2)
            self._flat_button(btn_frame, "💻 Open in VS Code", open_in_vscode,
                              side=tk.LEFT, padx=2, accent=True)

            self._flat_button(btn_frame, "📦 Convert To EXE",
                              lambda: self._convert_to_exe(top, text_widget),
                              side=tk.LEFT, padx=50, accent=True)
            self._flat_button(btn_frame, "Close", _close_code_editor,
                              side=tk.RIGHT, padx=2)

            # Conventional editor shortcuts:
            # Ctrl+F = focus Find, Ctrl+H = focus Replace, F3/Shift+F3 navigate.
            def _focus_find(event=None):
                find_entry.focus_set()
                find_entry.selection_range(0, tk.END)
                return "break"

            def _focus_replace(event=None):
                replace_entry.focus_set()
                replace_entry.selection_range(0, tk.END)
                return "break"

            text_widget.bind("<KeyRelease>",
                              lambda event: (_schedule_check(), _update_line_col()),
                              add="+"
                              )
            text_widget.bind("<ButtonRelease-1>", _update_line_col, add="+")
            text_widget.bind("<Control-s>",
                              lambda event: (save_code(), "break")[1]
                              )
            text_widget.bind("<Control-f>", _focus_find, add="+")
            text_widget.bind("<Control-h>", _focus_replace, add="+")
            find_entry.bind("<Return>", _find_next)
            replace_entry.bind("<Return>", _replace_current)
            top.bind("<F3>", _find_next)
            top.bind("<Shift-F3>", _find_previous)
            top.bind("<Escape>", lambda event: (_clear_search_tags(), search_status_var.set(""), text_widget.focus_set()))

            text_widget.focus_set()
            top.after(50, top.lift)  # Extra lift call after UI renders
            top.after(100, _check_syntax)

        def _select_all(self, event=None):
            all_visible = self._visible_elements()
            if not all_visible:
                return
            self._select_element(None, clear=True)
            for elem in all_visible:
                self._select_element(elem, clear=False)
            self._update_status(f"Selected {len(all_visible)} elements.")