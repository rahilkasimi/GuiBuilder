"""Application constants, widget catalogue, property definitions, and mappings."""
from typing import Dict, List, Tuple, Any
import os

MIN_W = 40
MIN_H = 20
HANDLE_HALF = 6
GRID_SIZE = 10
# Anchor for anything stored as a path relative to the builder itself (the
# "resources" folder images get copied into). Using this instead of
# os.getcwd() matters because tkinter.filedialog's native file picker is
# well known to silently change the process's current working directory
# as a side effect of browsing (especially on Windows) -- resolving
# relative to os.getcwd() meant an image could fail to load on the canvas
# immediately after picking it, every time, depending on where the dialog
# last left the cwd. The exported/generated app anchors the same way,
# using its own os.path.dirname(__file__) at export time.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTAINER_TYPES = {"Frame", "LabelFrame", "PanedWindow", "Notebook"}

TOOLTIP_HELPER_CODE = '''class _ToolTip:
    """Small hover tooltip for the generated app (Enter/Leave shows and
    hides a borderless popup near the widget)."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self._win = None
        try:
            # Defensive: every widget this ships on (plain tkinter/ttk)
            # implements bind(), but keep the guard cheap and harmless in
            # case a future widget type doesn't.
            widget.bind("<Enter>", self._show, add="+")
            widget.bind("<Leave>", self._hide, add="+")
        except tk.TclError:
            pass

    def _show(self, event=None):
        if self._win is not None or not self.text:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        self._win = tk.Toplevel(self.widget)
        self._win.wm_overrideredirect(True)
        self._win.wm_geometry(f"+{x}+{y}")
        tk.Label(self._win, text=self.text, justify="left",
                 background="#FFFFE0", relief="solid", borderwidth=1,
                 font=("Segoe UI", 9)).pack(ipadx=4, ipady=2)

    def _hide(self, event=None):
        if self._win is not None:
            self._win.destroy()
            self._win = None
'''

# ─── Toolbox item colors ────
# The builder's own UI is single-theme (light) plain tkinter/ttk, so these
# are plain color strings -- no dark-mode variant to ever fall back to.
TOOLBOX_NORMAL_COLOR = "#FFFFFF"
TOOLBOX_HOVER_COLOR = "#E3F2FD"
TOOLBOX_ACTIVE_COLOR = "#FF6B35"

ELEMENT_TYPES: Dict[str, Dict[str, Any]] = {
    "Label": {
        "display": "🏷️ Label",
        "widget": "tk.Label",
        "default_size": (120, 30),
        "defaults": {"text": "Label", "font": ("Segoe UI", 9), "fg": "#212121",
                      "bg": "#F5F5F5",
                      "justify": "center",
                      "corner_radius": "", "border_width": ""},
        "tile_bg": "#E3F2FD", "tile_fg": "#1565C0",
        "category": "Input",
    },
    "Entry": {
        "display": "✍️ Entry",
        "widget": "tk.Entry",
        "default_size": (160, 30),
        "defaults": {"textvariable": "", "show": "", "width": 20,
                      "font": ("Segoe UI", 9),
                      "fg": "#212121", "bg": "white",
                      "justify": "left", "default_value": "",
                      "corner_radius": "", "border_width": ""},
        "tile_bg": "#FFFFFF", "tile_fg": "#212121",
        "category": "Input",
    },
    "Button": {
        "display": "🔘 Button",
        "widget": "tk.Button",
        "default_size": (100, 34),
        "defaults": {"text": "Button", "font": ("Segoe UI", 9, "bold"),
                      "fg": "#FFFFFF", "bg": "#1976D2",
                      "command": "",
                      "corner_radius": "", "border_width": ""},
        "tile_bg": "#1976D2", "tile_fg": "#FFFFFF",
        "category": "Input",
    },
    "Radiobutton": {
        "display": "◉ Radiobutton",
        "widget": "tk.Radiobutton",
        "default_size": (130, 30),
        "defaults": {"text": "Option", "variable": "", "value": 1,
                      "font": ("Segoe UI", 9),
                      "fg": "#212121", "bg": "#F5F5F5",
                      "corner_radius": ""},
        "tile_bg": "#F3E5F5", "tile_fg": "#6A1B9A",
        "category": "Input",
    },
    "Checkbutton": {
        "display": "☑ Checkbutton",
        "widget": "tk.Checkbutton",
        "default_size": (130, 30),
        "defaults": {"text": "Checkbox", "variable": "", "onvalue": 1,
                      "offvalue": 0,
                      "font": ("Segoe UI", 9), "fg": "#212121", "bg": "#F5F5F5",
                      "default_value": 0, "corner_radius": "",
                      "border_width": ""},
        "tile_bg": "#E8F5E9", "tile_fg": "#2E7D32",
        "category": "Input",
    },
    "Scale": {
        "display": "🎚️ Scale (Slider)",
        "widget": "tk.Scale",
        "default_size": (180, 40),
        "defaults": {"from_": 0, "to": 100, "orient": "horizontal",
                      "length": 150,
                      "tickinterval": 0, "resolution": 1,
                      "font": ("Segoe UI", 9),
                      "fg": "#212121", "bg": "#F5F5F5", "default_value": 0,
                      "corner_radius": "", "border_width": ""},
        "tile_bg": "#FCE4EC", "tile_fg": "#AD1457",
        "category": "Input",
    },
    "Combobox": {
        "display": "🔽 Combobox",
        "widget": "ttk.Combobox",
        "default_size": (150, 30),
        "defaults": {"values": ["Option 1", "Option 2", "Option 3"],
                      "state": "readonly",
                      "font": ("Segoe UI", 9), "width": 18,
                      "default_value": "", "corner_radius": "", "border_width": "",
                      "sorted": "No", "maxdropdown": "", "maxlength": ""},
        "tile_bg": "#FFF3E0", "tile_fg": "#E65100",
        "category": "Input",
    },
    "Spinbox": {
        "display": "🔢 Spinbox",
        "widget": "tk.Spinbox",
        "default_size": (80, 30),
        "defaults": {"from_": 0, "to": 100, "width": 5,
                      "font": ("Segoe UI", 9),
                      "fg": "#212121", "bg": "white", "relief": "sunken",
                      "default_value": 0},
        "tile_bg": "#FFF8E1", "tile_fg": "#E65100",
        "category": "Input",
    },
    "Listbox": {
        "display": "📋 Listbox",
        "widget": "tk.Listbox",
        "default_size": (150, 80),
        "defaults": {"listvariable": "", "items": ["Item 1", "Item 2"],
                      "height": 4, "width": 18,
                      "font": ("Segoe UI", 9), "fg": "#212121", "bg": "white",
                      "relief": "sunken", "selectmode": "single",
                      "sorted": "No"},
        "tile_bg": "#E3F2FD", "tile_fg": "#0D47A1",
        "category": "Input",
    },
    "Text": {
        "display": "📝 Text (Multiline)",
        "widget": "tk.Text",
        "default_size": (200, 90),
        "defaults": {"height": 5, "width": 30, "font": ("Segoe UI", 9),
                      "fg": "#212121", "bg": "white",
                      "wrap": "word", "corner_radius": "", "border_width": ""},
        "tile_bg": "#FFFDE7", "tile_fg": "#F57F17",
        "category": "Input",
    },
    "Canvas": {
        "display": "🎨 Canvas (Drawing)",
        "widget": "tk.Canvas",
        "default_size": (200, 120),
        "defaults": {"width": 200, "height": 120, "bg": "white",
                      "relief": "sunken", "bd": 2},
        "tile_bg": "#FFF8E1", "tile_fg": "#F57F17",
        "category": "Display",
    },
    "Progressbar": {
        "display": "⏳ Progressbar (ttk)",
        "widget": "ttk.Progressbar",
        "default_size": (180, 30),
        "defaults": {"maximum": 100, "value": 40, "orient": "horizontal",
                      "length": 180, "corner_radius": "", "border_width": ""},
        "tile_bg": "#E8F5E9", "tile_fg": "#1B5E20",
        "category": "Input",
    },
    "Scrollbar": {
        "display": "↕️ Scrollbar",
        "widget": "tk.Scrollbar",
        "default_size": (20, 120),
        "defaults": {"orient": "vertical", "width": 16, "bg": "#E0E0E0"},
        "tile_bg": "#CFD8DC", "tile_fg": "#37474F",
        "category": "Display",
    },
    "Frame": {
        "display": "🖼️ Frame (Container)",
        "widget": "tk.Frame",
        "default_size": (200, 120),
        "defaults": {"bd": 2, "bg": "#F5F5F5",
                      "corner_radius": ""},
        "tile_bg": "#ECEFF1", "tile_fg": "#263238",
        "category": "Containers",
    },
    "LabelFrame": {
        "display": "🗂️ LabelFrame",
        "widget": "tk.LabelFrame",
        "default_size": (200, 120),
        "defaults": {"text": "LabelFrame", "bd": 2,
                      "bg": "#F5F5F5", "font": ("Segoe UI", 9),
                      "corner_radius": ""},
        "tile_bg": "#E0F2F1", "tile_fg": "#004D40",
        "category": "Containers",
    },
    "Notebook": {
        "display": "📑 Notebook (Tabs)",
        "widget": "ttk.Notebook",
        "default_size": (260, 160),
        "defaults": {"tabs": ["Tab 1", "Tab 2"], "active_tab": 0,
                      "corner_radius": "", "border_width": ""},
        "tile_bg": "#EDE7F6", "tile_fg": "#311B92",
        "category": "Containers",
    },
    "PanedWindow": {
        "display": "🪟 PanedWindow",
        "widget": "tk.PanedWindow",
        "default_size": (200, 120),
        "defaults": {"orient": "horizontal", "bg": "#F5F5F5",
                      "sashrelief": "raised"},
        "tile_bg": "#D7CCC8", "tile_fg": "#4E342E",
        "category": "Containers",
    },
    "Separator": {
        "display": "➖ Separator",
        "widget": "ttk.Separator",
        "default_size": (150, 4),
        "defaults": {"orient": "horizontal"},
        "tile_bg": "#B0BEC5", "tile_fg": "#263238",
        "category": "Display",
    },
    "Table": {
        "display": "📊 Table (Excel/CSV)",
        "widget": "ttk.Treeview",
        "default_size": (320, 200),
        "defaults": {"file": "", "sheet": 0, "columns": "", "height": 8},
        "tile_bg": "#E0F7FA", "tile_fg": "#004D40",
        "category": "Display",
    },
    "Image": {
        "display": "🖼️ Image",
        "widget": "tk.Label",
        "default_size": (160, 160),
        "defaults": {"image_path": "", "keep_aspect": 1, "bg": "#F5F5F5",
                      "corner_radius": ""},
        "tile_bg": "#F3E5F5", "tile_fg": "#6A1B9A",
        "category": "Display",
    },
    "Calendar": {
        "display": "📅 Calendar",
        "widget": "Calendar",
        "default_size": (230, 200),
        "defaults": {"initial_date": "", "date_pattern": "yyyy-mm-dd",
                      "selectmode": "day", "bg": "#FFFFFF", "fg": "#212121",
                      "firstweekday": "monday", "showweeknumbers": "Yes",
                      "mindate": "", "maxdate": "",
                      "selectbackground": "#1976D2",
                      "normalbackground": "#FFFFFF"},
        "tile_bg": "#FFEBEE", "tile_fg": "#B71C1C",
        "category": "Display",
    },
}

PROPERTY_FIELDS: Dict[str, List[Tuple]] = {
    "Label": [
        ("text", "Text", "entry"), ("font", "Font", "font"),
        ("fg", "Foreground", "color"), ("bg", "Background", "color"),
        ("justify", "Justify", "combobox", ["left", "center", "right"]),
        ("border_width", "Border Width", "entry"),
    ],
    "Entry": [
        ("textvariable", "Variable", "entry"),
        ("show", "Password char", "entry"), ("width", "Width", "entry"),
        ("font", "Font", "font"), ("fg", "Foreground", "color"),
        ("bg", "Background", "color"),
        ("justify", "Justify", "combobox", ["left", "center", "right"]),
        ("default_value", "Default Value", "entry"),
        ("border_width", "Border Width", "entry"),
    ],
    "Button": [
        ("text", "Text", "entry"), ("font", "Font", "font"),
        ("fg", "Foreground", "color"), ("bg", "Background", "color"),
        ("command", "Command", "text"),
        ("border_width", "Border Width", "entry"),
    ],
    "Radiobutton": [
        ("text", "Text", "entry"), ("variable", "Variable", "entry"),
        ("value", "Value", "entry"),
        ("font", "Font", "font"), ("fg", "Foreground", "color"),
        ("bg", "Background", "color"),
    ],
    "Checkbutton": [
        ("text", "Text", "entry"), ("variable", "Variable", "entry"),
        ("onvalue", "On Value", "entry"), ("offvalue", "Off Value", "entry"),
        ("font", "Font", "font"), ("fg", "Foreground", "color"),
        ("bg", "Background", "color"),
        ("default_value", "Default Value", "entry"),
        ("border_width", "Border Width", "entry"),
    ],
    "Scale": [
        ("from_", "From", "entry"), ("to", "To", "entry"),
        ("orient", "Orientation", "combobox", ["horizontal", "vertical"]),
        ("length", "Length", "entry"),
        ("tickinterval", "Tick interval", "entry"),
        ("resolution", "Resolution", "entry"),
        ("font", "Font", "font"), ("fg", "Foreground", "color"),
        ("bg", "Background", "color"),
        ("default_value", "Default Value", "entry"),
        ("border_width", "Border Width", "entry"),
    ],
    "Listbox": [
        ("listvariable", "Variable", "entry"),
        ("items", "Items", "entry"), ("height", "Height (rows)", "entry"),
        ("width", "Width (chars)", "entry"),
        ("font", "Font", "font"), ("fg", "Foreground", "color"),
        ("bg", "Background", "color"),
        ("relief", "Relief", "combobox",
         ["flat", "raised", "sunken", "groove", "ridge"]),
        ("selectmode", "Select mode", "combobox",
         ["single", "browse", "multiple", "extended"]),
        ("sorted", "Sorted", "combobox", ["Yes", "No"]),
    ],
    "Text": [
        ("height", "Height (rows)", "entry"),
        ("width", "Width (chars)", "entry"), ("font", "Font", "font"),
        ("fg", "Foreground", "color"), ("bg", "Background", "color"),
        ("wrap", "Wrap", "combobox", ["none", "char", "word"]),
        ("border_width", "Border Width", "entry"),
    ],
    "Frame": [
        ("bd", "Border width", "entry"), ("bg", "Background", "color"),
    ],
    "LabelFrame": [
        ("text", "Text", "entry"), ("font", "Font", "font"),
        ("bd", "Border width", "entry"), ("bg", "Background", "color"),
    ],
    "Notebook": [
        ("tabs", "Tabs", "entry"),
        ("active_tab", "Active Tab", "combobox", []),
        ("border_width", "Border Width", "entry"),
    ],
    "PanedWindow": [
        ("orient", "Orientation", "combobox", ["horizontal", "vertical"]),
        ("bg", "Background", "color"), ("sashrelief", "Sash relief", "combobox",
                                        ["flat", "raised", "sunken", "groove",
                                         "ridge"]),
    ],
    "Separator": [
        ("orient", "Orientation", "combobox", ["horizontal", "vertical"]),
        ("canvas_w", "Width (px)", "entry"),
        ("canvas_h", "Height (px)", "entry")
    ],
    "Canvas": [
        ("width", "Width", "entry"), ("height", "Height", "entry"),
        ("bg", "Background", "color"),
        ("relief", "Relief", "combobox",
         ["flat", "raised", "sunken", "groove", "ridge"]),
        ("bd", "Border width", "entry"),
    ],
    "Scrollbar": [
        ("orient", "Orientation", "combobox", ["horizontal", "vertical"]),
        ("width", "Width", "entry"), ("bg", "Background", "color"),
    ],
    "Combobox": [
        ("values", "Values", "entry"),
        ("state", "State", "combobox", ["normal", "readonly", "disabled"]),
        ("font", "Font", "font"), ("width", "Width (chars)", "entry"),
        ("default_value", "Default Value", "entry"),
        ("border_width", "Border Width", "entry"),
        ("sorted", "Sorted", "combobox", ["Yes", "No"]),
        ("maxdropdown", "Max Dropdown Rows", "entry"),
        ("maxlength", "Max Length", "entry"),
    ],
    "Spinbox": [
        ("from_", "From", "entry"), ("to", "To", "entry"),
        ("width", "Width (chars)", "entry"),
        ("font", "Font", "font"), ("fg", "Foreground", "color"),
        ("bg", "Background", "color"), ("relief", "Relief", "combobox",
                                        ["flat", "raised", "sunken", "groove",
                                         "ridge"]),
        ("default_value", "Default Value", "entry"),
    ],
    "Progressbar": [
        ("maximum", "Maximum", "entry"), ("value", "Current value", "entry"),
        ("orient", "Orientation", "combobox", ["horizontal", "vertical"]),
        ("length", "Length", "entry"),
        ("border_width", "Border Width", "entry"),
    ],
    "Table": [
        ("file", "Excel/CSV File", "file"),
        ("sheet", "Sheet Name", "entry"),
        ("columns", "Columns (csv)", "entry"),
        ("height", "Rows visible", "entry"),
    ],
    "Image": [
        ("image_path", "Image File", "file_image"),
        ("keep_aspect", "Keep Aspect Ratio", "combobox", ["1", "0"]),
        ("bg", "Background", "color"),
    ],
    "Calendar": [
        ("initial_date", "Initial Date (YYYY-MM-DD)", "entry"),
        ("date_pattern", "Date Format", "combobox",
         ["yyyy-mm-dd", "mm/dd/yyyy", "dd/mm/yyyy", "dd-mm-yyyy"]),
        ("selectmode", "Select Mode", "combobox", ["day", "none"]),
        ("firstweekday", "First Weekday", "combobox", ["monday", "sunday"]),
        ("showweeknumbers", "Show Week Numbers", "combobox", ["Yes", "No"]),
        ("mindate", "Min Date (YYYY-MM-DD)", "entry"),
        ("maxdate", "Max Date (YYYY-MM-DD)", "entry"),
        ("bg", "Background", "color"),
        ("fg", "Foreground", "color"),
        ("selectbackground", "Selected Day Background", "color"),
        ("normalbackground", "Normal Day Background", "color"),
    ],
}

DEFAULT_EVENT_MAP = {
    "Button": "command", "Entry": "<KeyRelease>", "Radiobutton": "command",
    "Checkbutton": "command",
    "Scale": "command", "Listbox": "<<ListboxSelect>>", "Text": "<KeyRelease>",
    "Combobox": "<<ComboboxSelected>>",
    "Spinbox": "<KeyRelease>", "Progressbar": None, "Label": None,
    "Frame": None, "LabelFrame": None,
    "Notebook": None, "PanedWindow": None, "Separator": None,
    "Canvas": None, "Scrollbar": None, "Table": None,
    "Image": None, "Calendar": "<<CalendarSelected>>",
}

# ─── Generated-code property handling ──────────────────────────────────────
# Every element type's ELEMENT_TYPES["widget"] entry (defined above) is
# already a plain tkinter/ttk class name -- CodeGenerator uses it directly,
# so (unlike the old CustomTkinter-targeting generator) there is no
# per-widget-toolkit property-name translation table needed any more: a
# prop dict key like "bg", "font", "from_", "orient", or "values" already
# *is* the real constructor keyword argument for every plain tkinter/ttk
# widget in ELEMENT_TYPES.
#
# SKIPPED_GENERIC_PROPS is the (much smaller) set of prop keys that must
# still be excluded from that generic "k=v" pass-through, because they are
# not real widget constructor kwargs at all -- either they're a design-time-
# only control (visible, tooltip), or they're consumed by one of
# CodeGenerator's dedicated per-element-type code blocks instead (Table,
# Image, Calendar, Combobox, Notebook tabs, Listbox items, default_value).
# corner_radius has no plain-tkinter equivalent (square corners only).
# It is retained in the defaults/serialization for backwards compatibility,
# but is intentionally not exposed by any property-panel field.
SKIPPED_GENERIC_PROPS = {
    "width", "height", "corner_radius", "default_value", "tooltip", "visible",
    "file", "sheet", "columns",
    "tabs", "active_tab",
    "items", "sorted",
    "maxdropdown", "maxlength",
    "image_path", "keep_aspect",
    "initial_date", "date_pattern", "firstweekday", "showweeknumbers",
    "mindate", "maxdate", "selectbackground", "normalbackground",
    # Listbox's selectmode currently has no generated-code effect (it was
    # never wired up even before this element type touched CustomTkinter);
    # left skipped here to keep this migration's behavior change strictly
    # scoped to "replace CustomTkinter", not "also fix unrelated gaps".
    "selectmode",
}

# ─── Fix 6 & 7: ensure every element type exposes pixel Width/Height and a Tooltip field
for _etype in ELEMENT_TYPES:
    _fields = PROPERTY_FIELDS.setdefault(_etype, [])
    _keys = {f[0] for f in _fields}
    if "canvas_w" not in _keys:
        _fields.append(("canvas_w", "Width (px)", "entry"))
    if "canvas_h" not in _keys:
        _fields.append(("canvas_h", "Height (px)", "entry"))
    if "tooltip" not in _keys:
        _fields.append(("tooltip", "Tooltip", "entry"))
    if "visible" not in _keys:
        # Whether the widget is shown when the exported app starts (it's
        # still created either way, so its own event handlers and any
        # code elsewhere that calls self._elem_N.place(...) later still
        # work -- see CodeGenerator._place_line). The design canvas always
        # shows the element regardless, with a dashed outline + "HIDDEN"
        # badge as a reminder (see CanvasRenderer.draw_element).
        _fields.append(("visible", "Visible", "combobox", ["Yes", "No"]))
