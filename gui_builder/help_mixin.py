"""Help system: full user guide and hover-based contextual help."""
from .dependencies import *
from .config import ELEMENT_TYPES, PROPERTY_FIELDS, CONTAINER_TYPES


ELEMENT_HELP = {
    "Label": "Displays non-editable text or captions. Use Text for the content, Font for typography, colors for appearance, and Justify for text alignment.",
    "Entry": "A single-line text input. Use Variable for an optional Tkinter variable name, Password char to mask input, Default Value for initial content, and Width/Justify to control the field.",
    "Button": "A clickable command button. Text is the caption and Command is the handler/function name generated for the button's event.",
    "Radiobutton": "One option in a mutually exclusive selection group. Give related radio buttons the same Variable and a unique Value for each option.",
    "Checkbutton": "A boolean/toggle control. Variable identifies the associated state variable; On Value and Off Value define the stored values.",
    "Scale": "A slider used to choose a numeric value. From/To define the range; Resolution controls the increment; Tick interval adds scale markings.",
    "Combobox": "A drop-down selection/input control. Values supplies the options, State controls whether the user can type, and Default Value sets the initial selection.",
    "Spinbox": "A compact numeric/text selector with increment/decrement arrows. From/To define the numeric range and Width controls the visible character width.",
    "Listbox": "A list of selectable items. Items defines the entries, Height/Width affect its visible size, Select mode controls selection behavior, and Sorted optionally orders the entries.",
    "Text": "A multiline text editor. Height/Width are character dimensions and Wrap controls how long lines are displayed.",
    "Canvas": "A drawing/custom-content surface. Width/Height define the widget dimensions while Background, Relief, and Border width control its appearance.",
    "Progressbar": "Displays progress toward a maximum value. Maximum is the upper bound, Current value is the current progress, and Orientation determines its direction.",
    "Scrollbar": "Provides scrolling for a Text (multiline) or Canvas widget. Set Target Widget to the intended control; Orientation automatically wires command/xview/yview and the target xscrollcommand/yscrollcommand.",
    "Frame": "A simple container used to group and organize other widgets. Child elements can be placed inside it and moved with the container.",
    "LabelFrame": "A bordered container with a caption. Use Text to name the group and Font/colors/Border width to style it.",
    "Notebook": "A tabbed container. Tabs defines tab names and Active Tab selects the currently visible page. Elements placed over the active page become associated with that tab.",
    "PanedWindow": "A resizable container split by a movable sash. Orientation controls whether the panes are arranged horizontally or vertically.",
    "Separator": "A visual divider between sections. Orientation controls its direction; Width/Height set its design-canvas size.",
    "Table": "A Treeview-based spreadsheet-style display that can load Excel/CSV data. File selects the source, Sheet selects a worksheet, Columns filters fields, and Rows visible controls the viewport height.",
    "Image": "Displays an image file in the generated application. Image File selects the resource; Keep Aspect Ratio controls proportional scaling; Background fills unused space.",
    "Calendar": "A calendar/date picker. Initial Date controls the starting date, Date Format controls the displayed format, and Min/Max Date constrain navigation/selection.",
    "PushButton": "A richer push button for instrument/control-panel interfaces. Shape can be Square or Round; Behavior chooses Momentary or Toggle and Default State sets the startup state.",
    "RadioButton": "A custom radio option (toolbox name: Radio Option) with Round or Square indicator shapes. Share the same Variable across related options and use Value to identify the selected choice.",
    "LEDDigit": "A single seven-segment LED digit. Digit Value controls 0-9, while LED Color, brightness and glow control the appearance.",
    "LEDDisplay": "A multi-digit seven-segment display. Value and Digits define the number shown; Leading Zeros, brightness, glow and colors control the presentation.",
    "LEDIndicator": "A compact status LED. State controls the standalone indicator; Source Widget can mirror or react to buttons/radio/check controls as visual feedback.",
    "Gauge": "An analog-style gauge/meter with configurable range, sweep angles, tick count, needle, track and value display.",
    "MeasurementDisplay": "A composite dashboard readout combining a label, value and unit with Modern or LED-style presentation and optional secondary text.",
}

PROPERTY_HELP = {
    "text": "Text displayed by the widget.",
    "font": "Font family and size used for widget text.",
    "fg": "Foreground/text color.",
    "bg": "Background/fill color.",
    "justify": "Horizontal alignment of text: left, center, or right.",
    "border_width": "Width of the widget border in pixels.",
    "bd": "Short form of border width in pixels.",
    "textvariable": "Name of a Tkinter variable associated with the control's text/value.",
    "show": "Character used to mask Entry contents, commonly for password-style input.",
    "width": "Widget width. Depending on the control this may be pixels or character units; see the property label.",
    "height": "Widget height. Depending on the control this may be pixels or character rows; see the property label.",
    "canvas_w": "Design-canvas width in pixels. This is the visual/layout width of the element in the builder.",
    "canvas_h": "Design-canvas height in pixels. This is the visual/layout height of the element in the builder.",
    "command": "Python handler/function associated with a command event.",
    "variable": "Name of the Tkinter variable used by a selection/input control.",
    "value": "Value assigned to a Radiobutton option when it is selected.",
    "onvalue": "Value stored when a Checkbutton is checked.",
    "offvalue": "Value stored when a Checkbutton is unchecked.",
    "from_": "Lower numeric bound of a Scale or Spinbox.",
    "to": "Upper numeric bound of a Scale or Spinbox.",
    "orient": "Widget direction: horizontal or vertical.",
    "length": "Requested linear length of controls such as Scale and Progressbar.",
    "tickinterval": "Distance between numeric tick labels/marks on a Scale.",
    "resolution": "Step size used when changing a Scale value.",
    "default_value": "Initial value shown/selected when the generated application starts.",
    "items": "Listbox entries. Enter a list or a comma-separated set of values.",
    "listvariable": "Name of the variable used to provide/update Listbox items.",
    "relief": "Border style such as flat, raised, sunken, groove, or ridge.",
    "selectmode": "Selection behavior for list/calendar controls.",
    "sorted": "Whether option/list data should be sorted before presentation.",
    "wrap": "How multiline text wraps: none, char, or word.",
    "values": "Options displayed by a Combobox. Enter a list or comma-separated values.",
    "state": "Combobox state: normal, readonly, or disabled.",
    "maxdropdown": "Maximum number of rows displayed by the Combobox drop-down.",
    "maxlength": "Maximum number of characters accepted by the control.",
    "sashrelief": "Visual border style of a PanedWindow sash.",
    "file": "Source Excel/CSV file used by a Table element.",
    "sheet": "Worksheet name/index used when loading Excel data.",
    "columns": "Comma-separated list of data columns to display in a Table.",
    "image_path": "Image resource path used by an Image element.",
    "keep_aspect": "Keeps the source image proportional while fitting it to the element bounds.",
    "tabs": "Notebook tab names. Enter a list or comma-separated tab labels.",
    "active_tab": "Notebook tab currently used as the active design/preview page.",
    "initial_date": "Date shown when the Calendar first opens, using the configured date pattern.",
    "date_pattern": "Calendar display format, such as yyyy-mm-dd or dd/mm/yyyy.",
    "firstweekday": "First weekday displayed in the Calendar.",
    "showweeknumbers": "Shows or hides week numbers in the Calendar.",
    "mindate": "Earliest date permitted in the Calendar.",
    "maxdate": "Latest date permitted in the Calendar.",
    "selectbackground": "Background color for the selected Calendar date.",
    "normalbackground": "Background color for ordinary Calendar dates.",
    "shape": "Visual shape for custom Push Button, Radio Button or LED Indicator elements.",
    "behavior": "Push Button interaction mode: Momentary returns off after release; Toggle stays on/off after each click.",
    "default_state": "Initial Push Button state when the generated application starts.",
    "selected": "Initial Radio Button selection state.",
    "active_fg": "Foreground color used by a selected custom Radio Button.",
    "active_bg": "Active/pressed/selected color used by custom controls.",
    "brightness": "Relative LED intensity from 0 to 100.",
    "glow": "Adds a luminous halo around active LED elements.",
    "leading_zeros": "Pads a multi-digit LED display with zeros up to the configured digit count.",
    "segment_width": "Thickness of the seven-segment LED strokes.",
    "state": "Boolean-style LED Indicator state: On or Off.",
    "on_color": "LED Indicator color while active.",
    "off_color": "LED Indicator color while inactive.",
    "source_widget": "Element ID selected as the LED Indicator's visual-feedback source.",
    "digit_gap": "Gap in pixels between adjacent digits in a multi-digit LED Display.",
    "group_id": "Design-time group membership shared by selected elements. Grouping does not create a runtime container.",
    "source_mode": "LED Indicator binding mode: Mirror, Toggle or Momentary.",
    "value": "Numeric or text value shown by an LED/Gauge/measurement element.",
    "digits": "Number of seven-segment positions in an LED Display.",
    "color": "Primary LED/value color for the custom display.",
    "min_value": "Lower bound of a Gauge range.",
    "max_value": "Upper bound of a Gauge range.",
    "start_angle": "Gauge sweep starting angle in degrees.",
    "end_angle": "Gauge sweep ending angle in degrees.",
    "needle_color": "Gauge needle color.",
    "arc_color": "Gauge active-range arc color.",
    "track_color": "Gauge inactive track color.",
    "tick_color": "Gauge tick/value text color.",
    "ticks": "Number of tick intervals drawn on the Gauge.",
    "show_value": "Shows or hides the Gauge's numeric readout.",
    "unit": "Engineering unit displayed with a Gauge or Measurement Display, such as V, A, °C or RPM.",
    "thickness": "Gauge arc/needle thickness in pixels.",
    "label": "Heading displayed above the primary measurement value.",
    "style": "Visual style used by custom Push Button/Measurement Display elements.",
    "decimal_places": "Number of decimal places used when a Measurement Display formats numeric values.",
    "prefix": "Text placed before a Measurement Display value.",
    "suffix": "Text placed after a Measurement Display value.",
    "secondary_text": "Optional secondary/status text shown below a Measurement Display.",
    "secondary_color": "Color of secondary label/unit/status text.",
    "align": "Horizontal alignment used by a Measurement Display: left, center or right.",
    "led_digits": "Reserved display width hint for LED-style Measurement Displays.",
    "tooltip": "Text shown by the generated application's widget tooltip on hover.",
    "visible": "Controls whether the widget is placed visibly when the generated application starts.",
    "border_width": "Border width used by the widget, where supported by its Tkinter/ttk implementation.",
    "showweeknumbers": "Controls display of week numbers in the Calendar.",
}

TOOLTIP_HELP = {
    "New Design": "Create a new empty design. Unsaved changes are handled by the existing new-design workflow.",
    "Load Design": "Open a saved .tvd design file.",
    "Save Design": "Save the current design. Ctrl+S performs the same action.",
    "Save As": "Save the current design to a new .tvd file.",
    "Undo": "Undo the most recent design change. Shortcut: Ctrl+Z.",
    "Redo": "Redo the last undone design change. Shortcut: Ctrl+Y.",
    "Delete": "Delete the selected canvas element(s). Shortcut: Delete.",
    "Clear Canvas": "Remove all elements from the current design canvas.",
    "Copy Code": "Copy the generated live Python code to the clipboard.",
    "Run Preview": "Generate and launch a temporary preview of the current application.",
    "Toggle Code": "Show or hide the Live Code panel.",
    "Code Editor": "Open the full code editor for the generated application code and custom code regions.",
    "TOOLBOX": "Choose an element type, then click the canvas to place it. Right-drag and Ctrl+Shift+A support container-scoped selection.",
    "Properties": "Shows editable properties for the current selection. Changes are reflected in the design and generated code.",
    "Canvas": "Design surface. Click to place the selected tool, drag to move elements, resize with handles, and use Ctrl+wheel for zoom.",
}

KEYBOARD_HELP = [
    ("Ctrl+N", "New design"),
    ("Ctrl+O", "Load design"),
    ("Ctrl+S", "Save design"),
    ("Ctrl+Shift+S", "Save As"),
    ("Ctrl+C / Ctrl+V", "Copy and paste selected elements"),
    ("Delete", "Delete selected elements"),
    ("Ctrl+Z / Ctrl+Y", "Undo / redo"),
    ("Ctrl+A", "Select all elements in the canvas"),
    ("Ctrl+Shift+A", "Select all elements within the active container"),
    ("Arrow keys", "Move selected elements"),
    ("Ctrl + mouse wheel", "Zoom the design canvas"),
    ("Double-click element", "Open its code in the code editor"),
    ("Right-drag", "Box-select within the active container scope"),
]


class HelpMixin:
    """Owns the builder help guide and contextual hover-help mode."""

    def _init_help_system(self):
        self._context_help_enabled = False
        self._help_window = None
        self._context_help_target = None

    def _help_toggle(self):
        self._context_help_enabled = not self._context_help_enabled
        if hasattr(self, "_context_help_btn"):
            self._context_help_btn.configure(
                text="?" if not self._context_help_enabled else "? ✓",
                bg=self._accent if self._context_help_enabled else "#FFFFFF",
                fg=self._accent_fg if self._context_help_enabled else self._panel_fg,
                activebackground="#1560AC" if self._context_help_enabled else "#E8E8E8",
            )
        self._hide_tooltip()
        state = "enabled" if self._context_help_enabled else "disabled"
        self._update_status(
            f"Context help {state}. Hover over a toolbox item, canvas element, or main UI control."
        )

    def _open_help(self):
        if self._help_window is not None and self._help_window.winfo_exists():
            self._help_window.deiconify()
            self._help_window.lift()
            self._help_window.focus_force()
            return

        win = tk.Toplevel(self.root)
        self._help_window = win
        win.title("Tkinter Visual Designer — Help Guide")
        win.geometry("960x720")
        win.minsize(720, 520)
        win.transient(self.root)

        win.grid_rowconfigure(1, weight=1)
        win.grid_columnconfigure(0, weight=1)

        header = tk.Frame(win, bg=self._accent)
        header.grid(row=0, column=0, sticky="ew")
        tk.Label(
            header, text="Tkinter Visual Designer Help Guide",
            font=("Segoe UI", 15, "bold"), bg=self._accent,
            fg="#FFFFFF", anchor="w"
        ).pack(side=tk.LEFT, padx=14, pady=10)
        tk.Button(
            header, text="Close", command=win.destroy,
            relief="flat", bd=0, bg="#FFFFFF", fg=self._panel_fg,
            activebackground="#E8E8E8", padx=12, pady=4, cursor="hand2"
        ).pack(side=tk.RIGHT, padx=12, pady=8)

        body = tk.Frame(win, bg="#FFFFFF")
        body.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)

        text = tk.Text(
            body, wrap="word", font=("Segoe UI", 10),
            bg="#FFFFFF", fg="#212121", relief="flat", borderwidth=0,
            padx=14, pady=10
        )
        scroll = ttk.Scrollbar(body, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        text.tag_configure("title", font=("Segoe UI", 16, "bold"), spacing3=8)
        text.tag_configure("h1", font=("Segoe UI", 13, "bold"), spacing1=14, spacing3=6)
        text.tag_configure("h2", font=("Segoe UI", 11, "bold"), spacing1=8, spacing3=3)
        text.tag_configure("muted", foreground="#666666")
        text.tag_configure("code", font=("Consolas", 9), background="#F3F3F3")

        self._populate_help_text(text)
        text.configure(state="disabled")

        win.bind("<Escape>", lambda _e: win.destroy())
        win.protocol("WM_DELETE_WINDOW", win.destroy)

    def _populate_help_text(self, text):
        text.insert("end", "Tkinter Visual Designer\n", "title")
        text.insert("end", "Full user guide: interface, elements, properties, selection, code generation, and shortcuts.\n\n", "muted")

        text.insert("end", "1. Main interface\n", "h1")
        text.insert("end", "Top bar — file operations, undo/redo, canvas actions, code tools, context help, and this guide.\n")
        text.insert("end", "Toolbox — choose a widget/container and click the canvas to place it. Categories organize the available controls.\n")
        text.insert("end", "Design canvas — move, resize, select, and arrange elements. Ctrl+mouse wheel changes zoom.\n")
        text.insert("end", "Properties — edit the selected element's configuration. Values are applied live and feed the code generator.\n")
        text.insert("end", "Live Code — optional generated Python source view; use Toggle Code to show/hide it.\n\n")

        text.insert("end", "2. Contextual hover help\n", "h1")
        text.insert("end", "Click the ? button in the top bar to enable Context Help Mode. With it enabled, hover over a toolbox item, a canvas element, or a major interface control to see a description. The same behavior works in both normal and compact toolbox modes. Click ? again to disable it.\n\n")

        text.insert("end", "3. GUI elements and properties\n", "h1")
        categories = {}
        for name, info in ELEMENT_TYPES.items():
            categories.setdefault(info.get("category", "Other"), []).append(name)
        for category, names in categories.items():
            text.insert("end", f"{category}\n", "h2")
            for name in names:
                info = ELEMENT_TYPES[name]
                widget = info.get("widget", "")
                text.insert("end", f"{name} — {ELEMENT_HELP.get(name, 'GUI element available in the toolbox.')}\n")
                text.insert("end", f"Tk widget: {widget}\n", "muted")
                fields = PROPERTY_FIELDS.get(name, [])
                if fields:
                    text.insert("end", "Properties:\n")
                    for field in fields:
                        key, label = field[0], field[1]
                        desc = PROPERTY_HELP.get(key, f"Configures {label.lower()} for this element.")
                        text.insert("end", f"  • {label} ({key}) — {desc}\n")
                text.insert("end", "\n")

        text.insert("end", "4. Selection and containers\n", "h1")
        text.insert("end", "Containers include Frame, LabelFrame, Notebook, and PanedWindow. Elements can belong to a container; moving/removing a container therefore affects its children according to the builder's current container rules.\n")
        text.insert("end", "Ctrl+A selects all elements on the canvas. Ctrl+Shift+A selects only elements in the active container scope. Right-drag creates a scoped selection box.\n\n")

        text.insert("end", "5. Code generation and events\n", "h1")
        text.insert("end", "The builder keeps a live Python representation of the design. Elements with supported events receive generated handler stubs. Editing properties updates the generated code, while the code editor preserves user-added custom module/class regions supported by the project.\n\n")

        text.insert("end", "6. Keyboard shortcuts\n", "h1")
        for shortcut, desc in KEYBOARD_HELP:
            text.insert("end", f"{shortcut:<22} {desc}\n", "code")
        text.insert("end", "\n")
        text.insert("end", "7. Practical workflow\n", "h1")
        text.insert("end", "1) Choose a toolbox element.  2) Click the canvas to place it.  3) Select it and edit Properties.  4) Arrange/resize and group elements inside containers.  5) Use Run Preview to validate the generated application.  6) Save the .tvd design when satisfied.\n\n")
        text.insert("end", "8. Built-in tooltip property\n", "h1")
        text.insert("end", "Most design elements expose a Tooltip property. This is separate from the builder's Context Help Mode: Tooltip is text intended for the generated application, while Context Help is documentation for the designer itself.\n")

    def _context_help_text_for(self, kind, key=None, elem=None):
        if elem is not None:
            name = elem.elem_type
            return (
                f"{name} (ID {elem.elem_id})\n"
                f"{ELEMENT_HELP.get(name, '')}\n\n"
                "Hover details come from the element's current help definition.\n"
                "Use the Properties panel to configure it."
            )
        if kind == "property" and key:
            return PROPERTY_HELP.get(key, f"Property: {key}")
        if kind == "element" and key:
            return f"{key}\n{ELEMENT_HELP.get(key, 'GUI element available in the toolbox.')}"
        return TOOLTIP_HELP.get(key or kind, str(key or kind))

    def _context_help_enter(self, widget, text_or_factory):
        if not self._context_help_enabled:
            return
        self._context_help_target = widget
        text = text_or_factory() if callable(text_or_factory) else text_or_factory
        self._show_tooltip(widget, text)

    def _context_help_leave(self, widget=None):
        if widget is None or self._context_help_target is widget:
            self._context_help_target = None
            self._hide_tooltip()

    def _bind_context_help(self, widget, text_or_factory):
        widget.bind(
            "<Enter>", lambda _e, w=widget, t=text_or_factory:
            self._context_help_enter(w, t), add="+"
        )
        widget.bind(
            "<Leave>", lambda _e, w=widget: self._context_help_leave(w), add="+"
        )

    def _bind_canvas_context_help(self):
        # Canvas contextual help requires identifying the element at the pointer,
        # so it is handled by _on_canvas_motion in UIMixin rather than a static bind.
        pass
