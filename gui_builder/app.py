"""Composition root for the modular visual GUI designer."""
from .dependencies import *
from .config import *
from .models import DesignElement
from .ui_mixin import UIMixin
from .canvas_mixin import CanvasMixin
from .properties_mixin import PropertiesMixin
from .code_mixin import CodeMixin
from .project_mixin import ProjectMixin
from .help_mixin import HelpMixin


class GUIBuilderApp(ProjectMixin, CodeMixin, PropertiesMixin, CanvasMixin, HelpMixin, UIMixin):
        def __init__(self, root: tk.Tk):
            self.root = root
            self._setup_styles()
            self.window_title = "My Application"
            self.current_file_path: Optional[str] = None
            self._is_modified = False
            self.full_code: Optional[str] = None
            self._current_code: str = ""
            # Custom code the user typed into the code editor outside any
            # recognized boilerplate/handler region (constants, dicts, extra
            # imports, standalone functions, extra class methods). Kept
            # separately from self.full_code so a later full regenerate doesn't
            # silently drop it -- see CodeGenerator.generate() and
            # _extract_custom_regions().
            self.custom_module_code: str = ""
            self.custom_class_code: str = ""

            self._update_window_title_display()
            self.root.geometry("1400x800")
            self.root.minsize(1000, 600)

            self._zoom = 1.0

            self.root.update()
            try:
                if platform.system() in ("Windows", "Darwin"):
                    self.root.state('zoomed')
                else:
                    self.root.attributes('-zoomed', True)
            except tk.TclError:
                try:
                    self.root.state('zoomed')
                except tk.TclError:
                    pass

            self.CANVAS_W = 800
            self.CANVAS_H = 600
            self.CANVAS_BG = "#FFFFFF"
            # Initial window state (Normal/Maximized/Minimized) for the
            # *exported* app's window -- unrelated to the builder's own
            # window, which is maximized a few lines up regardless of this.
            self.WINDOW_STATE = "Normal"
            # Whether exported/preview windows are fixed-size at runtime.
            # Kept separate from WINDOW_STATE so existing projects remain
            # fully backward-compatible.
            self.WINDOW_LOCKED = False

            self.canvas_imports = "import tkinter as tk\nfrom tkinter import ttk"

            self.elements: List[DesignElement] = []
            self.selected_elems: List[DesignElement] = []
            self.clipboard: List[DesignElement] = []
            # id -> element and parent_id -> [children] indexes, kept in sync by
            # _rebuild_index() (called after any add/remove/clear of self.elements).
            # These replace O(n) linear scans of self.elements that previously
            # happened inside per-element loops (O(n^2) on redraw/reorder/etc).
            self._by_id: Dict[int, DesignElement] = {}
            self._children_by_parent: Dict[int, List[DesignElement]] = {}

            self.next_id = 1
            self.reusable_ids = set()

            self.undo_stack = []
            self.redo_stack = []

            self.pending_type: Optional[str] = None
            self.code_visible = False
            self._code_display_timer = None
            self._code_editor_window = None
            self.prop_context_var = tk.StringVar(value="Container: None")
            self._tooltip_win = None
            self._toolbox_compact = False
            self._init_help_system()

            self.drag_mode = "none"
            self.drag_elem = None
            self.mouse_down_pos = None
            self.elem_origs = {}
            self.active_handle = None
            self.selection_box_id = None
            self.selection_scope_id = None
            self.active_container_id = None
            self._last_move_delta = (0, 0)
            self._right_click_start = None
            self._next_group_id_hint = 1

            self._build_ui()
            self.renderer.draw_grid(self.CANVAS_W, self.CANVAS_H)

            self.root.bind("<Control-c>", self._copy_elements)
            self.root.bind("<Control-v>", self._paste_elements)
            self.root.bind("<Delete>", self._delete_selected)
            self.root.bind("<Control-z>", self._undo)
            self.root.bind("<Control-y>", self._redo)
            self.root.bind("<Control-Z>", self._redo)

            self.root.bind("<Control-s>", lambda e: self._save_design())
            self.root.bind("<Control-Shift-S>", lambda e: self._save_design_as())
            self.root.bind("<Control-o>", lambda e: self._load_design())
            self.root.bind("<Control-n>", lambda e: self._new_design())

            self.root.bind("<Up>", self._move_with_keys)
            self.root.bind("<Down>", self._move_with_keys)
            self.root.bind("<Left>", self._move_with_keys)
            self.root.bind("<Right>", self._move_with_keys)

            self.root.bind("<Control-a>", self._select_all)
            self.root.bind("<Control-A>", self._select_all)
            self.root.bind("<Control-Shift-a>", self._select_all_scoped)
            self.root.bind("<Control-Shift-A>", self._select_all_scoped)

            # Tooltip on canvas hover
            self.canvas.bind("<Motion>", self._on_canvas_motion)
            self.canvas.bind("<Leave>", self._on_canvas_leave)

            self._update_code()
            self._update_element_count()
            self._update_status(
                "Ready — pick a tool and click canvas, or double-click elements to edit code."
                )
            self._show_properties(None)

            self._save_state()
