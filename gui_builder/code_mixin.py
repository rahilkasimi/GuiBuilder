import traceback
import types
"""Generated-code lifecycle, preview/build and code editor."""
from openpyxl.styles.builtins import accent_6

from .dependencies import *
from .config import *
from .models import DesignElement
from .code_generator import (
    CodeGenerator, INSTRUMENTATION_MODULE_NAME,
    DESIGNER_MODULE_NAME, DESIGNER_CLASS_NAME,
    USER_MODULE_NAME, USER_CLASS_NAME,
)


class CodeMixin:
    # ─── Designer / user module lifecycle ───────────────────────────────────
    #
    # Two-file model: self.designer_code (main_app_designer.py) is fully
    # auto-managed and regenerated wholesale on every model change --
    # unconditionally, with no diffing, splicing, or bail-out logic of any
    # kind, because by construction nothing hand-written can ever live in
    # it. self.user_code (main_app.py) is scaffolded exactly once and then
    # never auto-touched again except to append a new handler stub method
    # (and only when one of that name doesn't already exist). This
    # replaces the old single-file self.full_code plus the machinery that
    # used to exist purely to work around generated and hand-written code
    # sharing one file: _insert_code_for_new_elements,
    # _remove_code_for_elements, _synchronize_code_model_before_regenerate,
    # _strip_builder_instrumentation_runtime, _regenerate_full_code,
    # _invalidate_full_code, _ensure_header_imports, _extract_method_body,
    # _sync_all_handler_codes_from_lines, _extract_top_level_imports,
    # _sync_project_imports_from_code, and _extract_custom_regions are all
    # gone -- ownership is now a file boundary, not something inferred
    # from text, so there's nothing left for any of them to reconstruct.

    def _regenerate_designer_code(self) -> None:
        """Rebuild main_app_designer.py from the current element model.

        Call this after ANY model mutation -- add, remove, move, resize,
        property edit, paste, reparent, undo/redo, all of it. There is no
        cheaper "just patch this one element" path anymore because there's
        no need for one: regenerating the whole file is already O(number
        of elements) and always safe, since the file can never contain
        anything this function didn't just put there.
        """
        self.designer_code = CodeGenerator.generate_designer_module(
            self.elements, self.window_title,
            (self.CANVAS_W, self.CANVAS_H), self.CANVAS_BG,
            self.canvas_imports,
            getattr(self, "WINDOW_STATE", "Normal"),
            getattr(self, "WINDOW_LOCKED", False),
            canvas_bg_image=getattr(self,"CANVAS_BG_IMAGE",""),
            canvas_bg_image_mode=getattr(self,"CANVAS_BG_IMAGE_MODE","Fit"),
            canvas_bg_image_anchor=getattr(self,"CANVAS_BG_IMAGE_ANCHOR","Center"),
        )
        self._update_code()

    def _ensure_user_code_scaffold(self) -> None:
        """Create main_app.py's starter content the first time this
        project needs one. A no-op every time after that -- self.user_code
        is never regenerated once it exists, only ever appended to (see
        _ensure_handler_stub) or hand-edited via the code editor.
        """
        if self.user_code:
            return
        self.user_code = CodeGenerator.generate_user_module_scaffold(
            self.elements
        )

    def _ensure_handler_stub(self, elem: DesignElement) -> None:
        """Append a placeholder handler method for elem to self.user_code,
        but only if a method of that name isn't already there.

        Mirrors what a WinForms designer does the moment you drop a new
        control: it adds a stub to the code-behind file once, and never
        touches it again -- including never removing it later if the
        control itself is deleted (deletion never edits self.user_code at
        all; see CanvasMixin._delete_selected). An orphaned handler is
        left in place rather than risking any user code being silently
        discarded.
        """
        event = DEFAULT_EVENT_MAP.get(elem.elem_type)
        if not event:
            return
        self._ensure_user_code_scaffold()
        method_name = f"_on_{elem.elem_type}_{elem.elem_id}"
        if f"def {method_name}(" in self.user_code:
            return

        var_name = f"self._elem_{elem.elem_id}"
        stub_lines = [f"    def {method_name}(self, event=None):"]
        stub_lines.extend(CodeGenerator._handler_stub_body(
            elem.elem_type, elem.elem_id, event, var_name
        ))

        lines = self.user_code.splitlines(True)
        main_guard_idx = next(
            (i for i, l in enumerate(lines) if l.startswith("if __name__")),
            len(lines)
        )
        # Insert right before the __main__ guard (or at EOF if there isn't
        # one), so every appended stub lands in a predictable place at the
        # end of the class regardless of how much other code the user has
        # added above it in the meantime.
        insertion = [""] + [line + "\n" for line in stub_lines]
        lines[main_guard_idx:main_guard_idx] = insertion
        self.user_code = "".join(lines)

    def _update_code_display(self):
        """Refresh the read-only generated-code preview panel.

        This is called from many places (every keystroke while editing a
        property, every arrow-key nudge, every drag release, etc.), but the
        actual refresh is a full delete()+insert() of the whole preview
        text into a Tk Text widget, which triggers a full re-layout and
        gets slow once the script is a few hundred lines. self.designer_code,
        self.user_code and self._current_code (the actual sources of
        truth -- nothing reads the Text widget's content back out) are
        always updated synchronously by the caller before this runs, so
        debouncing the on-screen refresh never risks anyone seeing stale
        generated code -- it only delays how soon the *preview panel*
        catches up, by well under the time it takes to notice.
        """
        if getattr(self, "_code_display_timer", None):
            self.root.after_cancel(self._code_display_timer)
        self._code_display_timer = self.root.after(120,
                                                      self._apply_code_display
                                                      )

    def _apply_code_display(self):
        self._code_display_timer = None
        if self._current_code is None:
            return
        self.code_text.configure(state="normal")
        self.code_text.delete("1.0", tk.END)
        self.code_text.insert(tk.END, self._current_code)
        self.code_text.configure(state="disabled")

    def _update_code(self) -> None:
        """Ensure both files exist and refresh the combined read-only
        preview panel. Does NOT regenerate the designer module itself --
        call _regenerate_designer_code() for that; this only assembles
        self._current_code from whatever self.designer_code and
        self.user_code currently hold, which keeps this safe to call after
        an edit to *either* file without accidentally clobbering the one
        that didn't change.
        """
        self._ensure_user_code_scaffold()
        self._current_code = (
            f"# ===== {DESIGNER_MODULE_NAME}.py "
            f"(auto-generated -- do not edit) =====\n"
            f"{self.designer_code or ''}\n\n"
            f"# ===== {USER_MODULE_NAME}.py (yours -- edit freely) =====\n"
            f"{self.user_code or ''}"
        )
        self._update_code_display()

    def _window_title_changed(self):
        if hasattr(self, "title_var"):
            self.window_title = self.title_var.get()
            # No regex patching needed -- the designer module is always
            # safe to regenerate wholesale, title change or not.
            self._regenerate_designer_code()
            self._schedule_save()

    def _copy_code(self):
        code = self._current_code
        self.root.clipboard_clear()
        self.root.clipboard_append(code)
        self._update_status("Code copied to clipboard.")

    def _needs_instrumentation_module(self, code: str) -> bool:
        """True when generated ``code`` imports the instrumentation
        runtime module rather than embedding it inline."""
        return (
            f"from {INSTRUMENTATION_MODULE_NAME} import" in code
            or f"import {INSTRUMENTATION_MODULE_NAME}" in code
        )

    def _write_instrumentation_module(self, directory: str) -> str:
        """Write builder_instrumentation_widgets.py into ``directory`` so
        a generated script's ``from builder_instrumentation_widgets
        import ...`` line resolves next to it on disk (needed for
        PyInstaller's static analysis and for opening in an external
        editor). Returns the written path."""
        path = os.path.join(directory, f"{INSTRUMENTATION_MODULE_NAME}.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(CodeGenerator.instrumentation_module_source())
        return path

    def _run_preview(self):
        """Run the generated application inside a child Toplevel.

        Preview deliberately runs in-process.  Calling
        ``subprocess.Popen([sys.executable, ...])`` is unsafe in a
        PyInstaller-frozen build because ``sys.executable`` becomes
        GuiBuilder.exe, which starts a second GuiBuilder instance.
        """
        try:
            self._regenerate_designer_code()
            self._ensure_user_code_scaffold()
        except Exception as e:
            messagebox.showerror(
                "Run Preview Error",
                f"Failed to generate code:\n{e}"
            )
            return

        designer_code = self.designer_code
        user_code = self.user_code
        if not designer_code or not user_code or not user_code.strip():
            messagebox.showerror(
                "Run Preview Error",
                "Generated code is empty - nothing to run."
            )
            return

        combined_for_deps = f"{designer_code}\n{user_code}"
        missing = self._missing_packages_for_code(combined_for_deps)
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
            designer_path = os.path.join(
                temp_dir, f"{DESIGNER_MODULE_NAME}.py"
            )
            user_path = os.path.join(temp_dir, f"{USER_MODULE_NAME}.py")
            with open(designer_path, "w", encoding="utf-8") as f:
                f.write(designer_code)
            with open(user_path, "w", encoding="utf-8") as f:
                f.write(user_code)

            shutil.copy2(os.path.join(BASE_DIR, "gui_builder", "image_support.py"), os.path.join(temp_dir, "builder_image_support.py"))

            if self._needs_instrumentation_module(designer_code):
                # Write the real file for parity with what an exported
                # app looks like on disk, and also register it directly
                # in sys.modules so the in-process exec() below resolves
                # "from builder_instrumentation_widgets import ..."
                # immediately -- independent of sys.path/import-cache
                # ordering across repeated Run Preview calls.
                mod_path = self._write_instrumentation_module(temp_dir)
                instr_mod = types.ModuleType(INSTRUMENTATION_MODULE_NAME)
                instr_mod.__file__ = mod_path
                exec(
                    compile(
                        CodeGenerator.instrumentation_module_source(),
                        mod_path, "exec"
                        ),
                    instr_mod.__dict__
                    )
                sys.modules[INSTRUMENTATION_MODULE_NAME] = instr_mod

            helper_path = os.path.join(temp_dir, "builder_image_support.py")
            helper_mod = types.ModuleType("builder_image_support")
            helper_mod.__file__ = helper_path
            with open(helper_path, "r", encoding="utf-8") as _hf:
                exec(compile(_hf.read(), helper_path, "exec"), helper_mod.__dict__)
            sys.modules["builder_image_support"] = helper_mod

            # Same trick for the designer module: registering it in
            # sys.modules means main_app.py's
            # "from main_app_designer import _MainApplicationDesigner"
            # resolves in-process without needing temp_dir on sys.path.
            designer_mod = types.ModuleType(DESIGNER_MODULE_NAME)
            designer_mod.__file__ = designer_path
            exec(
                compile(designer_code, designer_path, "exec"),
                designer_mod.__dict__
            )
            sys.modules[DESIGNER_MODULE_NAME] = designer_mod

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
            preview_window.geometry(
                f"{max(320, int(self.CANVAS_W))}x"
                f"{max(240, int(self.CANVAS_H))}"
            )
            preview_window.resizable(True, True)

            # Compile/execute main_app.py with a private module namespace.
            # The generated __main__ guard therefore does not create a
            # second Tk root. MainApplication is instantiated against this
            # already-created Toplevel, which is important for custom
            # Canvas-backed instrumentation widgets.
            preview_ns = {
                "__name__": "__gui_builder_preview__",
                "__file__": user_path,
                "__package__": None,
                "__cached__": None,
            }
            exec(compile(user_code, user_path, "exec"), preview_ns, preview_ns)
            app_class = preview_ns.get(USER_CLASS_NAME)
            if not isinstance(app_class, type):
                preview_window.destroy()
                raise RuntimeError(
                    f"Generated code does not define {USER_CLASS_NAME}."
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
        sys.modules.pop(INSTRUMENTATION_MODULE_NAME, None)
        sys.modules.pop(DESIGNER_MODULE_NAME, None)

        self._update_status("Preview closed.")

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

    def _open_containing_folder(self, path: str) -> None:
        """Reveal path's containing folder in the OS file browser."""
        folder = path if os.path.isdir(path) else os.path.dirname(path)
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Open Folder",
                                  f"Folder not found:\n{folder}")
            return
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(folder)  # noqa: this branch is Windows-only
            elif system == "Darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            messagebox.showerror(
                "Open Folder", f"Could not open folder:\n{folder}\n\n{e}"
                )

    def _show_build_complete_dialog(self, final_path: str) -> None:
        """Small standalone completion notice shown after the build-log
        window has already been closed, with a direct way to reveal the
        output instead of making the user hunt for it manually.
        """
        colors = self._get_theme_colors()
        dlg = tk.Toplevel(self.root)
        dlg.title("Convert To EXE")
        dlg.configure(bg=colors["panel_bg"])
        dlg.transient(self.root)
        dlg.resizable(False, False)

        tk.Label(dlg, text="✓ Build complete",
                 font=("Segoe UI", 12, "bold"), bg=colors["panel_bg"],
                 fg=colors["panel_fg"]
                 ).pack(padx=24, pady=(18, 6), anchor="w")
        tk.Label(dlg, text=f"Saved to:\n{final_path}",
                 font=("Segoe UI", 9), bg=colors["panel_bg"],
                 fg=colors["panel_fg"], justify="left"
                 ).pack(padx=24, pady=(0, 16), anchor="w")

        btn_row = tk.Frame(dlg, bg=colors["panel_bg"])
        btn_row.pack(padx=24, pady=(0, 18), fill=tk.X)
        self._flat_button(
            btn_row, "📁 Open Folder",
            lambda: self._open_containing_folder(final_path)
            ).pack(side=tk.LEFT)
        self._flat_button(btn_row, "Close", dlg.destroy).pack(side=tk.RIGHT)

        dlg.update_idletasks()
        dlg.geometry(f"+{self.root.winfo_x() + 80}+{self.root.winfo_y() + 80}")
        try:
            dlg.grab_set()
        except tk.TclError:
            pass

    def _convert_to_exe(self, top: "tk.Toplevel",
                         text_widget: tk.Text) -> None:
        # Build from the authoritative two-file model, not from whatever
        # happens to be showing in a Text widget -- text_widget now only
        # ever displays main_app.py (the user-owned file; see
        # _open_code_editor), and a build needs both files regardless of
        # which one is currently open for editing.
        self._regenerate_designer_code()
        self._ensure_user_code_scaffold()
        designer_code = self.designer_code
        user_code = self.user_code
        combined_for_deps = f"{designer_code}\n{user_code}"
        if not user_code.strip():
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

        packages = self._detect_required_packages(combined_for_deps)
        uses_resources = os.path.isdir(os.path.join(BASE_DIR, "resources"))

        colors = self._get_theme_colors()
        log_top = tk.Toplevel(self.root)
        log_top.title("Convert To EXE - Build Log")
        log_top.geometry("760x520")
        log_top.configure(bg=colors["panel_bg"])
        log_top.transient(top)

        status_var = tk.StringVar(value="Starting build...")
        tk.Label(log_top, textvariable=status_var, anchor="w",
                 font=("Segoe UI", 11, "bold"), bg=colors["panel_bg"],
                 fg=colors["panel_fg"]
                 ).pack(fill=tk.X, padx=10, pady=(10, 4))

        log_frame = tk.Frame(log_top, bg=colors["panel_bg"])
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)
        log_text = tk.Text(log_frame, font=("Consolas", 9), bg=colors["log_bg"],
                            fg=colors["log_fg"], wrap=tk.WORD, state="disabled")
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL,
                                    command=log_text.yview)
        log_text.configure(yscrollcommand=log_scroll.set)
        log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        btn_row = tk.Frame(log_top, bg=colors["panel_bg"])
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
                            # Close the build-log window automatically --
                            # the user doesn't need to click through a
                            # wall of PyInstaller output once the build
                            # has actually finished successfully.
                            log_top.destroy()
                            self._show_build_complete_dialog(final_path)
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
                designer_path = os.path.join(
                    build_dir, f"{DESIGNER_MODULE_NAME}.py"
                )
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(user_code)
                with open(designer_path, "w", encoding="utf-8") as f:
                    f.write(designer_code)
                shutil.copy2(os.path.join(BASE_DIR, "gui_builder", "image_support.py"), os.path.join(build_dir, "builder_image_support.py"))
                if self._needs_instrumentation_module(designer_code):
                    log(
                        "Bundling builder_instrumentation_widgets.py "
                        "(instrumentation widget runtime)."
                    )
                    self._write_instrumentation_module(build_dir)
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
        # Store references for theme updates
        self._exe_log_window = log_top
        log_top._theme_widgets = {"log_text": log_text, "status_var": status_var, "log_frame": log_frame}
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

        top = Toplevel = tk.Toplevel(self.root)
        self._code_editor_window = top
        top.title(
            f"Code Editor - main_app.py (jump: {elem.elem_type} ID {elem.elem_id})"
            if elem is not None else "Code Editor - main_app.py"
        )
        top.geometry("900x680")
        top.minsize(650, 450)

        # Get theme colors
        colors = self._get_theme_colors()
        dark_bg = colors["panel_bg"]
        editor_bg = colors["editor_bg"]
        editor_fg = colors["editor_fg"]
        gutter_bg = colors["line_numbers_bg"]
        gutter_fg = colors["line_numbers_fg"]
        entry_bg = colors["search_entry_bg"]
        entry_fg = colors["search_entry_fg"]

        top.configure(bg=dark_bg)

        def _close_code_editor():
            if getattr(self, "_code_editor_window", None) is top:
                self._code_editor_window = None
            if getattr(self, "_code_editor_text_widget", None) is text_widget:
                self._code_editor_text_widget = None
            try:
                top.destroy()
            except tk.TclError:
                pass

        top.protocol("WM_DELETE_WINDOW", _close_code_editor)

        # Bring window to front and focus it
        top.lift()
        top.focus()

        # --------------------------------------------------------------
        # 1. Top Portion: Button Frame (Save, VS Code, EXE, Close)
        # --------------------------------------------------------------
        btn_frame = tk.Frame(top, bg=dark_bg)
        btn_frame.pack(fill=tk.X, padx=5, pady=5, side=tk.TOP)

        # --------------------------------------------------------------
        # Syntax Status Bar (Top/Middle)
        # --------------------------------------------------------------
        syntax_bar = tk.Frame(top, height=28, bg=dark_bg)
        syntax_bar.pack(fill=tk.X, padx=5, pady=(0, 2), side=tk.TOP)
        syntax_bar.pack_propagate(False)
        syntax_status_var = tk.StringVar(value="Ready")
        line_col_var = tk.StringVar(value="Ln 1, Col 1")
        syntax_status_label = tk.Label(syntax_bar,
                                        textvariable=syntax_status_var,
                                        anchor="w", bg=dark_bg,
                                        fg=editor_fg
                                        )
        syntax_status_label.pack(side=tk.LEFT, padx=8)
        line_col_label = tk.Label(syntax_bar, textvariable=line_col_var,
                                   anchor="e", bg=dark_bg,
                                   fg=editor_fg
                                   )
        line_col_label.pack(side=tk.RIGHT, padx=8)

        # --------------------------------------------------------------
        # Find / Replace state
        # --------------------------------------------------------------
        find_var = tk.StringVar()
        replace_var = tk.StringVar()
        search_status_var = tk.StringVar(value="")
        search_matches = []
        current_match = [0]
        search_generation = [0]

        editor_frame = tk.Frame(top, bg=dark_bg)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5, side=tk.TOP)
        editor_frame.grid_rowconfigure(0, weight=1)
        editor_frame.grid_rowconfigure(1, weight=0)
        editor_frame.grid_rowconfigure(2, weight=0)
        editor_frame.grid_columnconfigure(1, weight=1)

        text_widget = tk.Text(editor_frame, font=("Consolas", 10),
                               bg=editor_bg, fg=editor_fg, wrap=tk.NONE,
                               undo=True, padx=8, pady=6,
                               insertbackground=colors.get("insert_bg", editor_fg),
                               selectbackground=colors["selection_bg"],
                               selectforeground=colors.get("selection_fg", colors["accent_fg"])
                               )

        # Line-number gutter with dark theme colors
        linenumbers = tk.Canvas(editor_frame, width=44, bg=gutter_bg,
                                 highlightthickness=0, bd=0)

        def _redraw_linenumbers(*_args):
            try:
                linenumbers.delete("all")
                total_lines = int(text_widget.index("end-1c").split(".")[0])
                gutter_w = max(44, 14 + 8 * len(str(max(total_lines, 1))))
                if int(linenumbers["width"]) != gutter_w:
                    linenumbers.configure(width=gutter_w)
                i = text_widget.index("@0,0")
                while True:
                    dline = text_widget.dlineinfo(i)
                    if dline is None:
                        break
                    y = dline[1]
                    linenum = str(i).split(".")[0]
                    linenumbers.create_text(
                        gutter_w - 6, y, anchor="ne", text=linenum,
                        font=("Consolas", 10), fill=gutter_fg
                        )
                    i = text_widget.index(f"{i}+1line")
            except tk.TclError:
                pass

        def _on_text_yscroll(*args):
            y_scroll.set(*args)
            _redraw_linenumbers()

        def _on_yscroll_command(*args):
            text_widget.yview(*args)
            _redraw_linenumbers()

        y_scroll = ttk.Scrollbar(editor_frame, orient=tk.VERTICAL,
                                  command=_on_yscroll_command
                                  )
        x_scroll = ttk.Scrollbar(editor_frame, orient=tk.HORIZONTAL,
                                  command=text_widget.xview
                                  )
        text_widget.configure(yscrollcommand=_on_text_yscroll,
                               xscrollcommand=x_scroll.set
                               )

        # Grid layout for editor area
        linenumbers.grid(row=0, column=0, sticky="ns")
        text_widget.grid(row=0, column=1, sticky="nsew")
        y_scroll.grid(row=0, column=2, sticky="ns")
        x_scroll.grid(row=1, column=1, sticky="ew")

        # Tag configuration for dark theme
        text_widget.tag_config("syntax_error", background="#5A1D1D",
                                foreground="#F85149"
                                )
        text_widget.tag_config("search_match", background="#484323",
                                foreground=editor_fg)
        text_widget.tag_config("search_current", background=colors.get("search_current_bg", colors["accent"]),
                                foreground=colors.get("search_current_fg", colors["accent_fg"]))

        self._ensure_user_code_scaffold()
        text_widget.insert("1.0", self.user_code)
        self._code_editor_text_widget = text_widget
        text_widget.bind("<Configure>", _redraw_linenumbers, add="+")
        text_widget.bind("<MouseWheel>",
                          lambda event: top.after_idle(_redraw_linenumbers),
                          add="+")
        top.after_idle(_redraw_linenumbers)

        # --------------------------------------------------------------
        # 3. Bottom Portion: Full Search & Replace Bar
        # --------------------------------------------------------------
        search_frame = tk.Frame(editor_frame, bg=colors["search_frame_bg"])
        search_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(5, 0))
        search_frame.grid_columnconfigure(1, weight=1)
        search_frame.grid_columnconfigure(3, weight=1)

        tk.Label(search_frame, text="Find:", bg=colors["search_frame_bg"],
                 fg=editor_fg).grid(row=0, column=0, padx=(2, 4), sticky="w")
        find_entry = tk.Entry(search_frame, textvariable=find_var,
                              bg=entry_bg, fg=entry_fg, insertbackground=colors.get("entry_insert", entry_fg),
                              relief="solid", bd=1, highlightthickness=1,
                              highlightbackground=colors.get("entry_border", colors["panel_bg"]),
                              highlightcolor=colors["accent"])
        find_entry.grid(row=0, column=1, padx=(0, 6), sticky="ew")

        tk.Label(search_frame, text="Replace:", bg=colors["search_frame_bg"],
                 fg=editor_fg).grid(row=0, column=2, padx=(2, 4), sticky="w")
        replace_entry = tk.Entry(search_frame, textvariable=replace_var,
                                 bg=entry_bg, fg=entry_fg, insertbackground=colors.get("entry_insert", entry_fg),
                                 relief="solid", bd=1, highlightthickness=1,
                                 highlightbackground=colors.get("entry_border", colors["panel_bg"]),
                                 highlightcolor=colors["accent"])
        replace_entry.grid(row=0, column=3, padx=(0, 6), sticky="ew")

        search_actions = tk.Frame(search_frame, bg=colors["search_frame_bg"])
        search_actions.grid(row=0, column=5, sticky="e")

        def _clear_search_tags():
            try:
                text_widget.tag_remove("search_match", "1.0", tk.END)
                text_widget.tag_remove("search_current", "1.0", tk.END)
            except tk.TclError:
                pass

        def _collect_matches():
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
                next_pos = text_widget.index(f"{found} + 1 chars")
                if text_widget.compare(next_pos, ">=", tk.END):
                    break
                pos = next_pos
            return matches

        def _update_search_display(preserve_position=False, move_cursor=True):
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
            if move_cursor:
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
            _redraw_linenumbers()
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
            for start_idx, end_idx in reversed(matches):
                text_widget.delete(start_idx, end_idx)
                text_widget.insert(start_idx, replacement)
            _redraw_linenumbers()
            _update_search_display()

        def _find_entry_changed(*args):
            search_generation[0] += 1
            _update_search_display()

        find_var.trace_add("write", _find_entry_changed)

        # Create search action buttons
        self._flat_button(search_actions, "Previous", _find_previous,
                          side=tk.LEFT, padx=2)
        self._flat_button(search_actions, "Next", _find_next,
                          side=tk.LEFT, padx=2)
        self._flat_button(search_actions, "Replace", _replace_current,
                          side=tk.LEFT, padx=2)
        self._flat_button(search_actions, "Replace All", _replace_all,
                          side=tk.LEFT, padx=2)
        search_status_label = tk.Label(
            search_frame, textvariable=search_status_var, width=18,
            anchor="e", bg=colors["search_frame_bg"], fg=colors["muted_fg"]
        )
        search_status_label.grid(row=1, column=5, sticky="e", padx=(0, 3), pady=(3, 0))

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
                text_widget.tag_config("highlight", background=colors["highlight_bg"],
                                        foreground=colors["highlight_fg"]
                                        )

        _syntax_timer_id = [None]

        def _check_syntax():
            text_widget.tag_remove("syntax_error", "1.0", tk.END)
            code = text_widget.get("1.0", "end-1c")
            try:
                ast.parse(code)
                syntax_status_var.set("✓ No syntax errors")
                syntax_status_label.configure(fg=colors["syntax_status_ok"])
                return True
            except SyntaxError as e:
                lineno = e.lineno or 1
                msg = e.msg or "invalid syntax"
                syntax_status_var.set(
                    f"✗ Syntax error (line {lineno}): {msg}"
                    )
                syntax_status_label.configure(fg=colors["syntax_status_err"])
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
            if find_var.get():
                top.after_idle(lambda: _update_search_display(move_cursor=False))

        def _update_line_col(event=None):
            try:
                idx = text_widget.index("insert")
                line, col = idx.split(".")
                line_col_var.set(f"Ln {line}, Col {int(col) + 1}")
            except Exception:
                pass

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
            try:
                saved_insert = text_widget.index("insert")
                saved_yview = text_widget.yview()[0]
            except Exception:
                saved_insert = None
                saved_yview = None

            edited_code = text_widget.get("1.0", "end-1c")
            if "\t" in edited_code:
                edited_code = edited_code.expandtabs(4)
                text_widget.delete("1.0", tk.END)
                text_widget.insert("1.0", edited_code)

            # main_app.py is 100% user-owned: save it back verbatim, no
            # extraction, no synchronization step, nothing to silently
            # discard. The designer module is a completely separate file
            # this editor never shows or touches.
            self.user_code = edited_code
            self._update_code()
            self._save_state()
            if elem is not None:
                self._update_status(
                    f"Saved main_app.py (jumped from "
                    f"{elem.elem_type} ID {elem.elem_id})."
                    )
            else:
                self._update_status("Saved main_app.py.")
            refreshed = self.user_code
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", refreshed)
            _redraw_linenumbers()
            restored = False
            if saved_insert is not None:
                try:
                    line = int(saved_insert.split(".")[0])
                    col = int(saved_insert.split(".")[1])
                    total_lines = int(
                        text_widget.index("end-1c").split(".")[0]
                        )
                    line = max(1, min(line, total_lines))
                    line_end_col = int(
                        text_widget.index(f"{line}.end").split(".")[1]
                        )
                    col = max(0, min(col, line_end_col))
                    new_pos = f"{line}.{col}"
                    text_widget.mark_set("insert", new_pos)
                    text_widget.see(new_pos)
                    if saved_yview is not None:
                        text_widget.yview_moveto(saved_yview)
                    restored = True
                except Exception:
                    restored = False
            if not restored and elem is not None:
                pos = text_widget.search(f"def {method_name}", "1.0", tk.END)
                if pos:
                    pos = text_widget.index(f"{pos} linestart")
                    text_widget.mark_set("insert", pos)
                    text_widget.see(pos)
                    text_widget.xview_moveto(0.0)
            if find_var.get():
                _update_search_display(move_cursor=False)

        def open_in_vscode():
            # main_app.py's "from main_app_designer import
            # _MainApplicationDesigner" needs that module to actually
            # exist next to it on disk -- text_widget only ever holds
            # main_app.py's content now (see the loading code above), so
            # the designer module has to be written out separately here,
            # the same way _run_preview and _convert_to_exe both already
            # do it.
            self._regenerate_designer_code()
            edited_code = text_widget.get("1.0", tk.END)
            tvd_root = os.path.join(tempfile.gettempdir(), "tvd")
            os.makedirs(tvd_root, exist_ok=True)
            temp_dir = tempfile.mkdtemp(prefix="gui_vscode_", dir=tvd_root)
            temp_path = os.path.join(temp_dir, f"{USER_MODULE_NAME}.py")
            designer_path = os.path.join(
                temp_dir, f"{DESIGNER_MODULE_NAME}.py"
            )
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(edited_code)
            with open(designer_path, "w", encoding="utf-8") as f:
                f.write(self.designer_code)
            shutil.copy2(os.path.join(BASE_DIR, "gui_builder", "image_support.py"), os.path.join(temp_dir, "builder_image_support.py"))
            if self._needs_instrumentation_module(self.designer_code):
                self._write_instrumentation_module(temp_dir)
            src_resources = os.path.join(BASE_DIR, "resources")
            if os.path.isdir(src_resources):
                shutil.copytree(
                    src_resources, os.path.join(temp_dir, "resources")
                )
            try:
                # Open the *folder*, not just the one file -- VS Code's
                # Python extension resolves local imports (and Pylance's
                # "quick fix"/run button) relative to the open workspace,
                # not to a single loose file, so opening just
                # main_app.py by itself is what left main_app_designer
                # unresolved before.
                subprocess.Popen(["code", temp_dir, temp_path], shell=True)
                self._update_status(
                    "Opened temporary generated project folder in VS Code."
                    )
            except Exception as e:
                messagebox.showerror("Execution Error",
                                      f"Could not launch VS Code. Ensure 'code' is in PATH.\n\n{e}",
                                      parent=top
                                      )

        # Pack buttons inside the top btn_frame
        self._flat_button(btn_frame, "💾 Save", save_code,
                          accent=True, side=tk.LEFT, padx=2)
        self._flat_button(btn_frame, "💻 Open in VS Code", open_in_vscode,
                          side=tk.LEFT, padx=2, accent=True)

        self._flat_button(btn_frame, "📦 Convert To EXE",
                          lambda: self._convert_to_exe(top, text_widget),
                          side=tk.LEFT, padx=50, accent=True)
        self._flat_button(btn_frame, "Close", _close_code_editor,
                          side=tk.RIGHT, padx=2)

        # Editor keybindings and typing logic
        _CLOSERS = {"(": ")", "[": "]", "{": "}"}
        _QUOTES = {'"', "'"}

        def _handle_return(event=None):
            try:
                line_start = text_widget.index("insert linestart")
                line_text = text_widget.get(line_start, "insert")
                indent = re.match(r'[ \t]*', line_text).group(0)
                stripped = line_text.strip()
                extra = "    " if stripped.endswith(":") else ""
                text_widget.insert("insert", "\n" + indent + extra)
                _redraw_linenumbers()
                return "break"
            except Exception:
                return None

        def _handle_tab(event=None):
            try:
                if text_widget.tag_ranges("sel"):
                    start = text_widget.index("sel.first linestart")
                    end = text_widget.index("sel.last lineend")
                    n_lines = int(end.split(".")[0]) - int(start.split(".")[0]) + 1
                    line_no = int(start.split(".")[0])
                    for _ in range(n_lines):
                        text_widget.insert(f"{line_no}.0", "    ")
                        line_no += 1
                else:
                    text_widget.insert("insert", "    ")
                return "break"
            except Exception:
                return None

        def _handle_shift_tab(event=None):
            try:
                line_start = text_widget.index("insert linestart")
                line_text = text_widget.get(line_start, f"{line_start} lineend")
                remove = len(line_text) - len(line_text.lstrip(" "))
                remove = min(4, remove)
                if remove:
                    text_widget.delete(line_start, f"{line_start}+{remove}c")
                return "break"
            except Exception:
                return None

        def _handle_open_bracket_or_quote(char):
            def handler(event=None):
                try:
                    next_char = text_widget.get("insert", "insert+1c")
                    if char in _QUOTES and next_char == char:
                        text_widget.mark_set("insert", "insert+1c")
                        return "break"
                    text_widget.insert("insert", char)
                    if char in _QUOTES:
                        if not next_char.isalnum():
                            text_widget.insert("insert", char)
                            text_widget.mark_set("insert", "insert-1c")
                    else:
                        text_widget.insert("insert", _CLOSERS[char])
                        text_widget.mark_set("insert", "insert-1c")
                    return "break"
                except Exception:
                    return None
            return handler

        def _handle_close_bracket(char):
            def handler(event=None):
                try:
                    if text_widget.get("insert", "insert+1c") == char:
                        text_widget.mark_set("insert", "insert+1c")
                        return "break"
                except Exception:
                    pass
                return None
            return handler

        def _handle_backspace(event=None):
            try:
                prev_char = text_widget.get("insert-1c", "insert")
                next_char = text_widget.get("insert", "insert+1c")
                pair_close = _CLOSERS.get(prev_char)
                if (pair_close and next_char == pair_close) or (
                        prev_char in _QUOTES and next_char == prev_char):
                    text_widget.delete("insert-1c", "insert+1c")
                    return "break"
            except Exception:
                pass
            return None

        text_widget.bind("<Return>", _handle_return, add=False)
        text_widget.bind("<Tab>", _handle_tab, add=False)
        text_widget.bind("<Shift-Tab>", _handle_shift_tab, add=False)
        text_widget.bind("<BackSpace>", _handle_backspace, add="+")
        for _open in ("(", "[", "{"):
            text_widget.bind(_open, _handle_open_bracket_or_quote(_open), add=False)
        for _close in (")", "]", "}"):
            text_widget.bind(_close, _handle_close_bracket(_close), add=False)
        for _q in ('"', "'"):
            text_widget.bind(_q, _handle_open_bracket_or_quote(_q), add=False)

        def _focus_find(event=None):
            find_entry.focus_set()
            find_entry.selection_range(0, tk.END)
            return "break"

        def _focus_replace(event=None):
            replace_entry.focus_set()
            replace_entry.selection_range(0, tk.END)
            return "break"

        text_widget.bind("<KeyRelease>",
                          lambda event: (
                              _schedule_check(), _update_line_col(),
                              _redraw_linenumbers()
                              ),
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
        top.after(50, top.lift)
        top.after(100, _check_syntax)

        # Store theme widgets for later updates
        top._theme_widgets = {
            "text_widget": text_widget,
            "linenumbers": linenumbers,
            "redraw_linenumbers": _redraw_linenumbers,
            "syntax_bar": syntax_bar,
            "syntax_status_label": syntax_status_label,
            "line_col_label": line_col_label,
            "search_frame": search_frame,
            "find_entry": find_entry,
            "replace_entry": replace_entry,
            "search_status_label": search_status_label,
        }

    def _select_all(self, event=None):
        all_visible = self._visible_elements()
        if not all_visible:
            return
        self._select_element(None, clear=True)
        for elem in all_visible:
            self._select_element(elem, clear=False)
