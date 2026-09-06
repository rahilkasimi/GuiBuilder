"""Application constants, widget catalogue, property definitions, and mappings."""
from typing import Dict, List, Tuple, Any
import os

MIN_W = 40
MIN_H = 20
HANDLE_HALF = 5
# Cross-platform Tk cursor names for each resize-handle direction, used to
# swap the mouse cursor to match the handle currently under the pointer
# (diagonal handles get a diagonal resize cursor, edge handles get the
# matching horizontal/vertical one).
HANDLE_CURSOR_MAP = {
    "NW": "size_nw_se", "SE": "size_nw_se",
    "NE": "size_ne_sw", "SW": "size_ne_sw",
    "N": "sb_v_double_arrow", "S": "sb_v_double_arrow",
    "E": "sb_h_double_arrow", "W": "sb_h_double_arrow",
}
GRID_SIZE = 10
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTAINER_TYPES = {"Frame", "LabelFrame", "PanedWindow", "Notebook"}

# ----- Theme definitions -----
THEMES = {
    "Light": {
        "panel_bg": "#F5F5F5",
        "panel_fg": "#212121",
        "muted_fg": "#757575",
        "accent": "#1976D2",
        "accent_hover": "#1560AC",
        "accent_fg": "#FFFFFF",
        "hover_bg": "#E3F2FD",
        "button_bg": "#FFFFFF",
        "button_fg": "#212121",
        "button_hover_bg": "#E8E8E8",
        "button_active_bg": "#D6EAF8",
        "separator": "#D0D0D0",
        "entry_bg": "#FFFFFF",
        "entry_fg": "#212121",
        "entry_insert": "#212121",
        "entry_border": "#BDBDBD",
        "tooltip_bg": "#2b2b2b",
        "tooltip_fg": "#ffffff",
        "editor_bg": "#FFFFFF",
        "editor_fg": "#000000",
        "line_numbers_bg": "#F0F0F0",
        "line_numbers_fg": "#808080",
        "search_frame_bg": "#F5F5F5",
        "search_entry_bg": "#FFFFFF",
        "search_entry_fg": "#212121",
        "syntax_status_ok": "#2E7D32",
        "syntax_status_err": "#C62828",
        "syntax_error_bg": "#FFD9D9",
        "syntax_error_fg": "#8B0000",
        "search_match_bg": "#FFF3CD",
        "search_match_fg": "#212121",
        "search_current_bg": "#D6EAF8",
        "search_current_fg": "#212121",
        "highlight_bg": "#FFF3CD",
        "highlight_fg": "#000000",
        "selection_bg": "#264F78",
        "selection_fg": "#FFFFFF",
        "insert_bg": "#212121",
        "scroll_trough": "#EDEDED",
        "scroll_hover": "#D5D5D5",
        "scroll_pressed": "#C0C0C0",
        "log_bg": "#1E1E1E",
        "log_fg": "#D4D4D4",
        "log_status_bg": "#F5F5F5",
        "log_status_fg": "#212121",
    },
    "Dark": {
        "panel_bg": "#2D2D2D",
        "panel_fg": "#D4D4D4",
        "muted_fg": "#9E9E9E",
        "accent": "#1976D2",
        "accent_hover": "#0D47A1",
        "accent_fg": "#FFFFFF",
        "hover_bg": "#3C3C3C",
        "button_bg": "#333333",
        "button_fg": "#D4D4D4",
        "button_hover_bg": "#454545",
        "button_active_bg": "#505050",
        "separator": "#4A4A4A",
        "entry_bg": "#3C3C3C",
        "entry_fg": "#D4D4D4",
        "entry_insert": "#FFFFFF",
        "entry_border": "#666666",
        "tooltip_bg": "#3C3C3C",
        "tooltip_fg": "#FFFFFF",
        "editor_bg": "#1E1E1E",
        "editor_fg": "#D4D4D4",
        "line_numbers_bg": "#252526",
        "line_numbers_fg": "#858585",
        "search_frame_bg": "#2D2D2D",
        "search_entry_bg": "#3C3C3C",
        "search_entry_fg": "#D4D4D4",
        "syntax_status_ok": "#4EC9B0",
        "syntax_status_err": "#FC9A94",
        "syntax_error_bg": "#5A1D1D",
        "syntax_error_fg": "#F85149",
        "search_match_bg": "#484323",
        "search_match_fg": "#D4D4D4",
        "search_current_bg": "#684610",
        "search_current_fg": "#FFFFFF",
        "highlight_bg": "#484323",
        "highlight_fg": "#D4D4D4",
        "selection_bg": "#264F78",
        "selection_fg": "#FFFFFF",
        "insert_bg": "#FFFFFF",
        "scroll_trough": "#202020",
        "scroll_hover": "#505050",
        "scroll_pressed": "#606060",
        "log_bg": "#1E1E1E",
        "log_fg": "#D4D4D4",
        "log_status_bg": "#2D2D2D",
        "log_status_fg": "#D4D4D4",
    }
}

DEFAULT_THEME = "Light"

# ----- TOOLTIP helper (unchanged) -----
TOOLTIP_HELPER_CODE = '''class _ToolTip:
    """Small hover tooltip for the generated app (Enter/Leave shows and
    hides a borderless popup near the widget)."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self._win = None
        try:
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

# ----- Toolbox item colors (still used for active selection) -----
TOOLBOX_NORMAL_COLOR = "#FFFFFF"
TOOLBOX_HOVER_COLOR = "#E3F2FD"
TOOLBOX_ACTIVE_COLOR = "#FF6B35"

# ----- ELEMENT_TYPES, PROPERTY_FIELDS, DEFAULT_EVENT_MAP, SKIPPED_GENERIC_PROPS -----
# (the rest is exactly as in the original config.py; omitted for brevity but must remain)

# ----- Element catalogue -----
ELEMENT_TYPES: Dict[str, Dict[str, Any]] = {
    "Label": {
        "display": "🏷️ Label",
        "widget": "tk.Label",
        "default_size": (120, 30),
        "defaults": {"text": "Label", "font": ("Segoe UI", 9), "fg": "#212121",
                      "bg": "#F5F5F5", "relief": "flat",
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
        "display": "⬛ Button",
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
        "display": "⇳ Spinbox",
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
        "defaults": {"orient": "vertical", "width": 16, "bg": "#E0E0E0",
                      "target_widget": ""},
        "tile_bg": "#CFD8DC", "tile_fg": "#37474F",
        "category": "Display",
    },
    "PushButton": {
        "display": "⏹ Push Button",
        "widget": "BuilderPushButton",
        "default_size": (120, 44),
        "defaults": {"text": "Push Button", "shape": "Square",
                      "style": "Mechanical", "behavior": "Momentary",
                      "default_state": "Off", "font": ("Segoe UI", 9, "bold"),
                      "fg": "#FFFFFF",
                      "bg": "#1976D2", "active_bg": "#0D47A1",
                      "border_width": 2, "command": ""},
        "tile_bg": "#E3F2FD", "tile_fg": "#0D47A1",
        "category": "Input",
    },
    "RadioButton": {
        "display": "💿 Radio Option",
        "widget": "BuilderRadioButton",
        "default_size": (150, 32),
        "defaults": {"text": "Option", "variable": "", "value": "1",
                      "shape": "Round", "selected": "No",
                      "font": ("Segoe UI", 9),
                      "fg": "#212121", "bg": "#F5F5F5",
                      "active_fg": "#1976D2", "active_bg": "#1976D2",
                      "command": ""},
        "tile_bg": "#F3E5F5", "tile_fg": "#6A1B9A",
        "category": "Input",
    },
    "LEDDigit": {
        "display": "🔢 LED Digit",
        "widget": "BuilderLEDDisplay",
        "default_size": (48, 70),
        "defaults": {"value": "0", "color": "#00FF66",
                      "off_color": "#16351F", "brightness": 100,
                      "glow": "Yes", "segment_width": 4, "digit_gap": 12, "bg": "#101010"},
        "tile_bg": "#263238", "tile_fg": "#00FF66",
        "category": "Instrumentation",
    },
    "LEDDisplay": {
        "display": "📟 LED Display",
        "widget": "BuilderLEDDisplay",
        "default_size": (180, 80),
        "defaults": {"value": "120", "digits": 3,
                      "color": "#00FF66", "off_color": "#16351F",
                      "brightness": 100, "glow": "Yes",
                      "leading_zeros": "No", "segment_width": 4, "digit_gap": 12,
                      "decimal_places": 0, "bg": "#101010"},
        "tile_bg": "#263238", "tile_fg": "#00FF66",
        "category": "Instrumentation",
    },
    "LEDIndicator": {
        "display": "💡 LED Indicator",
        "widget": "BuilderLEDIndicator",
        "default_size": (34, 34),
        "defaults": {"state": "Off", "on_color": "#00FF66",
                      "off_color": "#16351F", "shape": "Round",
                      "brightness": 100, "glow": "Yes", "border_width": 1,
                      "bg": "#E0E0E0", "source_widget": "",
                      "source_mode": "Mirror"},
        "tile_bg": "#ECEFF1", "tile_fg": "#00A844",
        "category": "Instrumentation",
    },
    "Gauge": {
        "display": "⏱️ Gauge / Meter",
        "widget": "BuilderGauge",
        "default_size": (180, 150),
        "defaults": {"value": 50, "min_value": 0, "max_value": 100,
                      "start_angle": 225, "end_angle": -45,
                      "needle_color": "#E53935", "arc_color": "#1976D2",
                      "track_color": "#D9D9D9", "tick_color": "#555555",
                      "ticks": 10, "show_value": "Yes", "unit": "",
                      "thickness": 8, "bg": "#FFFFFF"},
        "tile_bg": "#E8EAF6", "tile_fg": "#3949AB",
        "category": "Instrumentation",
    },
    "MeasurementDisplay": {
        "display": "🖳 Measurement Display",
        "widget": "BuilderMeasurementDisplay",
        "default_size": (230, 120),
        "defaults": {"label": "Temperature", "value": "24", "unit": "°C",
                      "style": "Modern", "color": "#1976D2",
                      "bg": "#FFFFFF", "decimal_places": 0,
                      "prefix": "", "suffix": "", "secondary_text": "",
                      "secondary_color": "#666666", "align": "center",
                      "led_digits": 3,
                      "label_font": ("Segoe UI", 9, "bold"), "label_color": "#666666",
                      "value_font": ("Segoe UI", 34, "bold"), "value_color": "#1976D2",
                      "unit_font": ("Segoe UI", 12), "unit_color": "#666666",
                      "secondary_font": ("Segoe UI", 10), "secondary_text_color": "#666666"},
        "tile_bg": "#E8F5E9", "tile_fg": "#1B5E20",
        "category": "Instrumentation",
    },
    "Frame": {
        "display": "🖼️ Frame (Container)",
        "widget": "tk.Frame",
        "default_size": (200, 120),
        "defaults": {"bd": 2, "bg": "#F5F5F5", "relief": "flat",
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
    "DateTimePicker": {
        "display": "🗓️ DateTime Picker",
        "widget": "DateTimePicker",
        "default_size": (250, 32),
        "defaults": {"initial_datetime": "", "display_format": "Date & Time",
                      "custom_format": "", "date_pattern": "yyyy-mm-dd",
                      "time_format": "24h", "font": ("Segoe UI", 9),
                      "bg": "#FFFFFF", "fg": "#212121"},
        "tile_bg": "#E8EAF6", "tile_fg": "#283593",
        "category": "Input",
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
    "LinkLabel": {
        "display": "🔗 LinkLabel",
        "widget": "tk.Label",
        "default_size": (120, 26),
        "defaults": {"text": "LinkLabel", "font": ("Segoe UI", 9, "underline"),
                      "fg": "#0563C1", "bg": "#F5F5F5", "cursor": "hand2",
                      "url": "", "corner_radius": ""},
        "tile_bg": "#E3F2FD", "tile_fg": "#0563C1",
        "category": "Input",
    },
    "StatusBar": {
        "display": "▭ Status Bar",
        "widget": "tk.Label",
        "default_size": (760, 24),
        "defaults": {"text": "Ready", "font": ("Segoe UI", 9),
                      "fg": "#212121", "bg": "#F0F0F0",
                      "relief": "sunken", "anchor": "w",
                      "border_width": 1},
        "tile_bg": "#ECEFF1", "tile_fg": "#37474F",
        "category": "Display",
    },
}

# ----- Property fields per element -----
PROPERTY_FIELDS: Dict[str, List[Tuple]] = {
    "Label": [
        ("text", "Text", "entry"), ("font", "Font", "font"),
        ("fg", "Foreground", "color"), ("bg", "Background", "color"),
        ("justify", "Justify", "combobox", ["left", "center", "right"]),
        ("relief", "Relief", "combobox", ["flat", "raised", "sunken", "groove", "ridge", "solid"]),
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
    "PushButton": [
        ("text", "Text", "entry"),
        ("shape", "Shape", "combobox", ["Square", "Round"]),
        ("style", "Style", "combobox", ["Mechanical", "Flat"]),
        ("behavior", "Behavior", "combobox", ["Momentary", "Toggle"]),
        ("default_state", "Default State", "combobox", ["On", "Off"]),
        ("font", "Font", "font"),
        ("fg", "Foreground", "color"), ("bg", "Background", "color"),
        ("active_bg", "Active Color", "color"),
        ("border_width", "Border Width", "entry"),
        ("command", "Command", "text"),
    ],
    "RadioButton": [
        ("text", "Text", "entry"), ("variable", "Variable", "entry"),
        ("value", "Value", "entry"),
        ("shape", "Shape", "combobox", ["Round", "Square"]),
        ("selected", "Selected", "combobox", ["Yes", "No"]),
        ("font", "Font", "font"),
        ("fg", "Foreground", "color"), ("bg", "Background", "color"),
        ("active_fg", "Selected Color", "color"),
        ("active_bg", "Indicator Color", "color"),
        ("command", "Command", "text"),
    ],
    "LEDDigit": [
        ("value", "Digit Value", "entry"),
        ("color", "LED Color", "color"),
        ("off_color", "Off Segment Color", "color"),
        ("brightness", "Brightness", "entry"),
        ("glow", "Glow", "combobox", ["Yes", "No"]),
        ("segment_width", "Segment Width", "entry"),
        ("digit_gap", "Digit Gap (px)", "entry"),
        ("bg", "Background", "color"),
    ],
    "LEDDisplay": [
        ("value", "Value", "entry"), ("digits", "Digits", "entry"),
        ("decimal_places", "Decimal Places", "entry"),
        ("color", "LED Color", "color"),
        ("off_color", "Off Segment Color", "color"),
        ("brightness", "Brightness", "entry"),
        ("glow", "Glow", "combobox", ["Yes", "No"]),
        ("leading_zeros", "Leading Zeros", "combobox", ["Yes", "No"]),
        ("segment_width", "Segment Width", "entry"),
        ("digit_gap", "Digit Gap (px)", "entry"),
        ("bg", "Background", "color"),
    ],
    "LEDIndicator": [
        ("state", "State", "combobox", ["On", "Off"]),
        ("on_color", "On Color", "color"),
        ("off_color", "Off Color", "color"),
        ("shape", "Shape", "combobox", ["Round", "Square"]),
        ("brightness", "Brightness", "entry"),
        ("glow", "Glow", "combobox", ["Yes", "No"]),
        ("border_width", "Border Width", "entry"),
        ("bg", "Background", "color"),
        ("source_widget", "Source Widget", "instrumentation_source"),
        ("source_mode", "Source Mode", "combobox", ["Mirror", "Toggle", "Momentary"]),
    ],
    "Gauge": [
        ("value", "Value", "entry"), ("min_value", "Minimum", "entry"),
        ("max_value", "Maximum", "entry"),
        ("start_angle", "Start Angle", "entry"),
        ("end_angle", "End Angle", "entry"),
        ("needle_color", "Needle Color", "color"),
        ("arc_color", "Arc Color", "color"),
        ("track_color", "Track Color", "color"),
        ("tick_color", "Tick Color", "color"),
        ("ticks", "Tick Count", "entry"),
        ("show_value", "Show Value", "combobox", ["Yes", "No"]),
        ("unit", "Unit", "entry"), ("thickness", "Thickness", "entry"),
        ("bg", "Background", "color"),
    ],
    "MeasurementDisplay": [
        ("label", "Label", "entry"), ("label_font", "Label Font", "font"),
        ("label_color", "Label Color", "color"),
        ("value", "Value", "entry"), ("value_font", "Value Font", "font"),
        ("value_color", "Value Color", "color"),
        ("unit", "Unit", "entry"), ("unit_font", "Unit Font", "font"),
        ("unit_color", "Unit Color", "color"),
        ("style", "Style", "combobox", ["Modern", "LED"]),
        ("bg", "Background", "color"),
        ("decimal_places", "Decimal Places", "entry"),
        ("prefix", "Prefix", "entry"), ("suffix", "Suffix", "entry"),
        ("secondary_text", "Secondary Text", "entry"),
        ("secondary_font", "Secondary Font", "font"),
        ("secondary_text_color", "Secondary Text Color", "color"),
        ("align", "Alignment", "combobox", ["left", "center", "right"]),
        ("led_digits", "LED Digits", "entry"),
        ("unit_gap", "Unit Gap (px)", "entry"),
    ],
    "Frame": [
        ("bd", "Border width", "entry"),
        ("relief", "Relief", "combobox", ["flat", "raised", "sunken", "groove", "ridge", "solid"]),
        ("bg", "Background", "color"),
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
        ("target_widget", "Target Widget", "target_widget"),
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
        ("image_mode", "Image Mode", "combobox", ["Stretch", "Fill", "Fit", "Center", "Tile", "None"]),
        ("image_anchor", "Image Alignment", "combobox", ["Top-Left", "Top", "Top-Right", "Left", "Center", "Right", "Bottom-Left", "Bottom", "Bottom-Right"]),
        ("bg", "Background", "color"),
    ],
    "DateTimePicker": [
        ("initial_datetime", "Initial Value", "entry"),
        ("display_format", "Display Format", "combobox", [
            "Date", "Date & Time", "Time", "Custom"
        ]),
        ("custom_format", "Custom Format", "entry"),
        ("font", "Font", "font"),
        ("date_pattern", "Calendar Date Format", "combobox", [
            "yyyy-mm-dd", "dd/mm/yyyy", "dd-mm-yyyy", "mm/dd/yyyy",
            "dd.mm.yyyy", "yyyy/mm/dd"
        ]),
        ("time_format", "Time Format", "combobox", ["24h", "12h"]),
        ("bg", "Background", "color"),
        ("fg", "Foreground", "color"),
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
    "LinkLabel": [
        ("text", "Text", "entry"), ("font", "Font", "font"),
        ("fg", "Foreground", "color"), ("bg", "Background", "color"),
        ("url", "URL", "entry"),
    ],
    "StatusBar": [
        ("text", "Text", "entry"), ("font", "Font", "font"),
        ("fg", "Foreground", "color"), ("bg", "Background", "color"),
        ("relief", "Relief", "combobox",
         ["flat", "raised", "sunken", "groove", "ridge", "solid"]),
        ("border_width", "Border Width", "entry"),
    ],
}

# ----- Event map -----
DEFAULT_EVENT_MAP = {
    "Button": "command", "Entry": "<KeyRelease>", "Radiobutton": "command",
    "Checkbutton": "command",
    "Scale": "command", "Listbox": "<<ListboxSelect>>", "Text": "<KeyRelease>",
    "Combobox": "<<ComboboxSelected>>",
    "Spinbox": "<KeyRelease>", "Progressbar": None, "Label": None,
    "Frame": None, "LabelFrame": None,
    "Notebook": None, "PanedWindow": None, "Separator": None,
    "Canvas": None, "Scrollbar": None, "Table": None,
    "Image": None, "Calendar": "<<CalendarSelected>>", "DateTimePicker": "<<DateTimeChanged>>",
    "PushButton": "command", "RadioButton": "command",
    "LEDDigit": None, "LEDDisplay": None, "LEDIndicator": None,
    "Gauge": None, "MeasurementDisplay": None,
    "LinkLabel": "<Button-1>", "StatusBar": None,
}

# ----- Generated-code property handling -----
SKIPPED_GENERIC_PROPS = {
    "width", "height", "corner_radius", "default_value", "tooltip", "visible",
    "file", "sheet", "columns",
    "tabs", "active_tab",
    "items", "sorted",
    "maxdropdown", "maxlength",
    "image_path", "keep_aspect", "image_mode", "image_anchor", "content_anchor", "compound",
    "initial_date", "date_pattern", "firstweekday", "showweeknumbers",
    "mindate", "maxdate", "selectbackground", "normalbackground",
    "selectmode", "initial_datetime", "display_format", "custom_format", "time_format",
    "target_widget", "source_widget", "source_mode", "group_id",
    "url",
}

# ----- Fix 6 & 7: ensure every element type exposes pixel Width/Height and a Tooltip field
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
        _fields.append(("visible", "Visible", "combobox", ["Yes", "No"]))
    if "image_path" not in _keys and _etype not in ("Image", "StatusBar"):
        _fields.append(("image_path", "Background Image", "file_image"))
    if "image_mode" not in _keys and _etype not in ("Image", "StatusBar"):
        _fields.append(("image_mode", "Image Mode", "combobox", ["Stretch", "Fill", "Fit", "Center", "Tile", "None"]))
    if "image_anchor" not in _keys and _etype not in ("Image", "StatusBar"):
        _fields.append(("image_anchor", "Image Alignment", "combobox", ["Top-Left", "Top", "Top-Right", "Left", "Center", "Right", "Bottom-Left", "Bottom", "Bottom-Right"]))
    if _etype in ("Label", "Button", "Checkbutton", "Radiobutton", "LinkLabel"):
        if "content_anchor" not in _keys:
            _fields.append(("content_anchor", "Content Alignment", "combobox", ["nw", "n", "ne", "w", "center", "e", "sw", "s", "se"]))
        if "compound" not in _keys:
            _fields.append(("compound", "Image + Text", "combobox", ["none", "left", "right", "top", "bottom", "center"]))
