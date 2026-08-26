"""Design persistence, undo/redo and project commands."""
from .dependencies import *
from .config import *
from .models import DesignElement


class ProjectMixin:
        def _schedule_save(self, delay_ms: int = 500):
            """Debounce a _save_state() call: rapid-fire callers (live
            property edits, arrow-key nudges, title typing, etc.) each
            reset the same pending timer instead of pushing an undo-stack
            entry per keystroke.
            """
            if getattr(self, "_save_timer", None):
                self.root.after_cancel(self._save_timer)
            self._save_timer = self.root.after(delay_ms, self._save_state)

        def _save_state(self, clear_redo=True):
            # ``full_code`` may have been updated incrementally (for example
            # when a new Image/Calendar/Table element is added).  Before the
            # design snapshot is serialized, make the persistent import block
            # agree with the actual generated source.  This prevents a later
            # full regeneration from rebuilding the project from stale
            # ``canvas_imports`` and silently dropping user-added imports.
            try:
                if getattr(self, "full_code", None):
                    self._sync_project_imports_from_code(self.full_code)
            except Exception:
                # Saving the design itself must remain fail-safe; the code
                # synchronization is a consistency repair, not a reason to
                # block persistence of the user's canvas.
                pass

            state = {
                "elements": [e.to_dict() for e in self.elements],
                "next_id": self.next_id,
                "reusable_ids": list(self.reusable_ids),
                "window_title": self.window_title,
                "canvas_w": self.CANVAS_W,
                "canvas_h": self.CANVAS_H,
                "canvas_bg": self.CANVAS_BG,
                "window_state": getattr(self, "WINDOW_STATE", "Normal"),
                "canvas_imports": self.canvas_imports,
                "full_code": self.full_code,
                "custom_module_code": self.custom_module_code,
                "custom_class_code": self.custom_class_code,
            }
            state_str = json.dumps(state)
            if not self.undo_stack or self.undo_stack[-1] != state_str:
                self.undo_stack.append(state_str)
                if clear_redo:
                    self.redo_stack.clear()
            self._is_modified = True
            self._update_window_title_display()

        def _load_state(self, state_str: str):
            data = json.loads(state_str)

            self.canvas.delete("all")
            self.elements.clear()
            self.selected_elems.clear()

            self.next_id = data.get("next_id", 1)
            self.reusable_ids = set(data.get("reusable_ids", []))
            self.window_title = data.get("window_title", "My Application")
            if hasattr(self, "title_var"):
                self.title_var.set(self.window_title)

            self.CANVAS_W = data.get("canvas_w", 800)
            self.CANVAS_H = data.get("canvas_h", 600)
            self.CANVAS_BG = data.get("canvas_bg", "#FAFAFA")
            self.WINDOW_STATE = data.get("window_state", "Normal")
            self.canvas_imports = data.get("canvas_imports",
                                            "import tkinter as tk\nfrom tkinter import ttk")
            self.full_code = data.get("full_code")
            self.custom_module_code = data.get("custom_module_code", "")
            self.custom_class_code = data.get("custom_class_code", "")

            # Repair older designs that stored extra top-level imports only in
            # ``full_code`` while ``canvas_imports`` contained just the base Tk
            # imports.  The repair is non-destructive: it only adds imports that
            # already exist in the saved source.
            try:
                if self.full_code:
                    self._sync_project_imports_from_code(self.full_code)
            except Exception:
                pass

            self.canvas.config(width=self.CANVAS_W, height=self.CANVAS_H,
                                bg=self.CANVAS_BG,
                                scrollregion=(0, 0, self.CANVAS_W, self.CANVAS_H)
                                )

            for elem_data in data.get("elements", []):
                elem = DesignElement.from_dict(elem_data)
                self.elements.append(elem)
            self._rebuild_index()

            self.renderer.draw_grid(self.CANVAS_W, self.CANVAS_H)
            self._redraw_all_elements()
            self._reorder_elements()
            self._show_properties(None)
            self._update_code()
            self._update_element_count()

        def _undo(self, event=None):
            if event and hasattr(event, "widget") and event.widget.winfo_class() in ("Entry",
                                                                                     "TEntry",
                                                                                     "Text"):
                return

            if len(self.undo_stack) > 1:
                curr = self.undo_stack.pop()
                self.redo_stack.append(curr)
                prev = self.undo_stack[-1]
                self._load_state(prev)
                self._update_status("Undo successful.")

        def _redo(self, event=None):
            if event and hasattr(event, "widget") and event.widget.winfo_class() in ("Entry",
                                                                                     "TEntry",
                                                                                     "Text"):
                return

            if self.redo_stack:
                next_state = self.redo_stack.pop()
                self.undo_stack.append(next_state)
                self._load_state(next_state)
                self._update_status("Redo successful.")

        def _update_element_count(self):
            self.count_var.set(f"Elements: {len(self.elements)}")

        def _update_status(self, msg: str):
            self.status_var.set(msg)

        def _save_to_path(self, path: str):
            try:
                self._save_state()
                state_str = self.undo_stack[-1] if self.undo_stack else "{}"
                with open(path, "w", encoding="utf-8") as f:
                    f.write(state_str)
                self.current_file_path = path
                self._is_modified = False
                self._update_window_title_display()
                self._update_status(f"Saved design to {os.path.basename(path)}")
            except Exception as e:
                messagebox.showerror("Save Error", str(e))

        def _save_design(self):
            if self.current_file_path:
                self._save_to_path(self.current_file_path)
            else:
                self._save_design_as()

        def _save_design_as(self):
            path = filedialog.asksaveasfilename(
                title="Save Design As",
                defaultextension=".tvd",
                filetypes=[("Tkinter Visual Design", "*.tvd"),
                           ("All Files", "*.*")]
            )
            if path:
                self._save_to_path(path)
                return "break"
            return "break"

        def _load_design(self):
            path = filedialog.askopenfilename(
                filetypes=[("Tkinter Visual Design", "*.tvd"),
                           ("All Files", "*.*")]
            )
            if path:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        state_str = f.read()
                    self.undo_stack.clear()
                    self.redo_stack.clear()
                    self.undo_stack.append(state_str)
                    self._load_state(state_str)
                    self.current_file_path = path
                    self._is_modified = False
                    self._update_window_title_display()
                    self._update_status(
                        f"Loaded design from {os.path.basename(path)}"
                        )
                except Exception as e:
                    messagebox.showerror("Load Error", str(e))

        def _new_design(self):
            if self._is_modified:
                if not messagebox.askyesno("Confirm New",
                                            "You have unsaved changes. Create new design anyway?"
                                            ):
                    return
            self.current_file_path = None
            self._is_modified = False
            self.elements.clear()
            self._rebuild_index()
            self.selected_elems.clear()
            self.reusable_ids.clear()
            self.next_id = 1
            self.window_title = "My Application"
            self.CANVAS_W = 800
            self.CANVAS_H = 600
            self.CANVAS_BG = "#FAFAFA"
            self.WINDOW_STATE = "Normal"
            self.canvas_imports = "import tkinter as tk\nfrom tkinter import ttk"
            # Custom code typed into the Code Editor (module-level helpers
            # and extra class methods, kept outside the regenerated
            # boilerplate -- see code_mixin.py) belongs to whatever design
            # was open before. A new design starts from a blank slate, the
            # same as a freshly launched builder, not with a previous
            # project's hand-written functions still tagging along.
            self.custom_module_code = ""
            self.custom_class_code = ""
            self.full_code = None
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.canvas.delete("all")
            self.renderer.draw_grid(self.CANVAS_W, self.CANVAS_H)
            self._show_properties(None)
            self._update_code()
            self._update_element_count()
            self._save_state()
            self._update_window_title_display()
            self._update_status("Created new design.")
