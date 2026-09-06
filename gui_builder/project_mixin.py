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
            state = {
                "elements": [e.to_dict() for e in self.elements],
                "next_id": self.next_id,
                "reusable_ids": list(self.reusable_ids),
                "window_title": self.window_title,
                "canvas_w": self.CANVAS_W,
                "canvas_h": self.CANVAS_H,
                "canvas_bg": self.CANVAS_BG,
                "canvas_bg_image": getattr(self,"CANVAS_BG_IMAGE",""),
                "canvas_bg_image_mode": getattr(self,"CANVAS_BG_IMAGE_MODE","Fit"),
                "canvas_bg_image_anchor": getattr(self,"CANVAS_BG_IMAGE_ANCHOR","Center"),
                "window_state": getattr(self, "WINDOW_STATE", "Normal"),
                "window_locked": bool(getattr(self, "WINDOW_LOCKED", False)),
                "canvas_imports": self.canvas_imports,
                # designer_code is intentionally NOT persisted -- it's 100%
                # derived from elements/window metadata and gets rebuilt by
                # _regenerate_designer_code() on load, the same way it's
                # rebuilt after every other model change. Persisting it
                # would just be a second copy of the same information that
                # could drift out of sync with the model it came from.
                # user_code is the only piece of generated-code state that
                # actually needs saving, because it's the one file nothing
                # else can reconstruct.
                "user_code": self.user_code,
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
            self.CANVAS_BG_IMAGE = data.get("canvas_bg_image", "")
            self.CANVAS_BG_IMAGE_MODE = data.get("canvas_bg_image_mode", "Fit")
            self.CANVAS_BG_IMAGE_ANCHOR = data.get("canvas_bg_image_anchor", "Center")
            self.WINDOW_STATE = data.get("window_state", "Normal")
            self.WINDOW_LOCKED = bool(data.get("window_locked", False))
            self.canvas_imports = data.get("canvas_imports",
                                            "import tkinter as tk\nfrom tkinter import ttk")
            self.user_code = data.get("user_code")

            self.canvas.config(width=self.CANVAS_W, height=self.CANVAS_H,
                                bg=self._get_theme_colors()["panel_bg"],
                                scrollregion=(0, 0, self.CANVAS_W, self.CANVAS_H)
                                )

            for elem_data in data.get("elements", []):
                elem = DesignElement.from_dict(elem_data)
                self.elements.append(elem)
            self._rebuild_index()

            self.renderer.draw_canvas_surface(self.CANVAS_W, self.CANVAS_H, self.CANVAS_BG)
            self.renderer.draw_canvas_background(self.CANVAS_BG_IMAGE,self.CANVAS_BG_IMAGE_MODE,self.CANVAS_BG_IMAGE_ANCHOR,self.CANVAS_W,self.CANVAS_H)
            self.renderer.draw_canvas_border(self.CANVAS_W, self.CANVAS_H)
            self._redraw_all_elements()
            self._reorder_elements()
            self._show_properties(None)
            self._regenerate_designer_code()
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
            self.CANVAS_BG_IMAGE = ""
            self.CANVAS_BG_IMAGE_MODE = "Fit"
            self.CANVAS_BG_IMAGE_ANCHOR = "Center"
            self.WINDOW_STATE = "Normal"
            self.canvas_imports = "import tkinter as tk\nfrom tkinter import ttk"
            # user_code (event handlers, extra methods, extra imports typed
            # into the code editor) belongs to whatever design was open
            # before. A new design starts from a blank slate, the same as
            # a freshly launched builder -- it gets its own scaffold
            # generated fresh the first time it needs one (see
            # _ensure_user_code_scaffold), not a previous project's
            # hand-written functions tagging along.
            self.user_code = None
            self.designer_code = None
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.canvas.delete("all")
            self.renderer.draw_canvas_surface(self.CANVAS_W, self.CANVAS_H, self.CANVAS_BG)
            self.renderer.draw_canvas_background(self.CANVAS_BG_IMAGE,self.CANVAS_BG_IMAGE_MODE,self.CANVAS_BG_IMAGE_ANCHOR,self.CANVAS_W,self.CANVAS_H)
            self.renderer.draw_canvas_border(self.CANVAS_W, self.CANVAS_H)
            self._show_properties(None)
            self._regenerate_designer_code()
            self._update_code()
            self._update_element_count()
            self._save_state()
            self._update_window_title_display()
            self._update_status("Created new design.")
