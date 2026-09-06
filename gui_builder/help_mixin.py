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
    "DateTimePicker": "A compact date/time entry field with a pop-up calendar. Display Format chooses whether Date, Time, both, or a Custom pattern is shown; Calendar Date Format and Time Format control how the value is rendered, and Initial Value seeds the field when the generated application starts.",
    "PushButton": "A richer push button for instrument/control-panel interfaces. Shape can be Square or Round; Behavior chooses Momentary or Toggle and Default State sets the startup state.",
    "RadioButton": "A custom radio option (toolbox name: Radio Option) with Round or Square indicator shapes. Share the same Variable across related options and use Value to identify the selected choice.",
    "LEDDigit": "A single seven-segment LED digit. Digit Value controls 0-9, while LED Color, brightness and glow control the appearance.",
    "LEDDisplay": "A multi-digit seven-segment display. Value and Digits define the number shown; Leading Zeros, brightness, glow and colors control the presentation.",
    "LEDIndicator": "A compact status LED. State controls the standalone indicator; Source Widget can mirror or react to buttons/radio/check controls as visual feedback.",
    "Gauge": "An analog-style gauge/meter with configurable range, sweep angles, tick count, needle, track and value display.",
    "MeasurementDisplay": "A composite dashboard readout combining a label, value and unit with Modern or LED-style presentation and optional secondary text.",
    "LinkLabel": "A hyperlink-styled label. Text is the caption and URL (optional) automatically opens in the system browser when clicked, in addition to the generated _on_LinkLabel_N handler stub. Font/Foreground default to a classic blue/underlined hyperlink look but can be changed.",
    "StatusBar": "A docked status bar. Placed automatically at the bottom of the canvas, full width, regardless of where you click to add it, and re-docks itself if you resize the canvas afterward. Text is the message shown; no background image is offered for this element.",
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
    "url": "Web address opened in the system browser when the LinkLabel is clicked. Leave blank to use only the generated click-handler stub.",
    "tooltip": "Text shown by the generated application's widget tooltip on hover.",
    "visible": "Controls whether the widget is placed visibly when the generated application starts.",
    "border_width": "Border width used by the widget, where supported by its Tkinter/ttk implementation.",
    "showweeknumbers": "Controls display of week numbers in the Calendar.",
    "initial_datetime": "Date/time value used to seed a DateTimePicker when the generated application starts, using the field's configured format.",
    "display_format": "Which parts of the value a DateTimePicker shows and edits: Date, Time, Date & Time, or Custom.",
    "custom_format": "strftime-style pattern used by a DateTimePicker when Display Format is set to Custom.",
    "date_pattern": "Calendar/date display pattern, such as yyyy-mm-dd or dd/mm/yyyy.",
    "time_format": "Clock format used by a DateTimePicker's time portion: 24h or 12h.",
    "image_path": "Optional background image applied behind the widget's own content. Works on any element, not only the dedicated Image element.",
    "image_mode": "How a background image is fitted to the element: Stretch, Fill, Fit, Center, Tile, or None.",
    "image_anchor": "Where a background image is positioned within the element when it is not stretched to fill the full bounds.",
    "content_anchor": "Anchors a Label/Button/Checkbutton/Radiobutton's text (and image, when Image + Text is combined) within its bounds, e.g. nw, center, se.",
    "compound": "Places an element's optional image relative to its text: none, left, right, top, bottom, or center — mirrors Tkinter's compound option.",
    "target_widget": "Element ID of the Text or Canvas widget a Scrollbar drives. Orientation determines whether xview/xscrollcommand or yview/yscrollcommand is wired.",
    "window_title": "Title shown in the generated application's window title bar.",
    "canvas_width": "Overall design-canvas / generated-window width in pixels. Distinct from an individual element's own Width (px) property.",
    "canvas_height": "Overall design-canvas / generated-window height in pixels. Distinct from an individual element's own Height (px) property.",
    "canvas_background": "Solid background color of the entire design canvas / generated application window.",
    "canvas_bg_image": "Background image applied behind the entire design canvas / generated application window, independent of any per-widget background image.",
    "canvas_bg_image_mode": "How the canvas-level background image is fitted to the window: Stretch, Fill, Fit, Center, Tile, or None.",
    "canvas_bg_image_anchor": "Where the canvas-level background image is positioned when it is not stretched to fill the window.",
    "window_state": "Startup window state applied by the generated application: Normal, Maximized, Minimized, or Centered.",
    "window_locked": "When enabled, the generated/preview window disables manual resizing and the native maximize control (root.resizable(False, False)).",
    "label_font": "Font used by a Measurement Display's heading label.",
    "label_color": "Text color of a Measurement Display's heading label.",
    "value_font": "Font used by a Measurement Display's primary numeric/text value.",
    "value_color": "Color of a Measurement Display's primary value text.",
    "unit_font": "Font used by a Measurement Display's unit text.",
    "unit_color": "Color of a Measurement Display's unit text.",
    "secondary_font": "Font used by a Measurement Display's secondary/status text.",
    "secondary_text_color": "Color of a Measurement Display's secondary/status text.",
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
    "Theme": "Switch between Light and Dark themes for the entire application.",
    "Compact Toolbox": "Toggle toolbox presentation between labeled list mode and compact icon mode.",
    "Right-click canvas": "Open a context menu for the clicked element or current selection: Copy, Paste, Delete, Group Selected, Ungroup Selected, Bring to Front, and Send to Back, plus element-specific actions such as LED value/state editing and gauge value editing.",
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
            colors = self._get_theme_colors()
            self._context_help_btn.configure(
                text="?" if not self._context_help_enabled else "? ✓",
                bg=self._accent if self._context_help_enabled else self._button_bg,
                fg=self._accent_fg if self._context_help_enabled else self._button_fg,
                activebackground=colors.get("accent_hover", self._accent) if self._context_help_enabled else self._button_hover_bg,
                activeforeground=self._accent_fg if self._context_help_enabled else self._button_fg,
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
        win.geometry("1180x760")
        win.minsize(860, 520)
        win.transient(self.root)

        win.grid_rowconfigure(1, weight=1)
        win.grid_columnconfigure(0, weight=1)

        header = tk.Frame(win, bg=self._accent)
        header.grid(row=0, column=0, sticky="ew")
        tk.Label(
            header, text="Tkinter Visual Designer Help Guide",
            font=("Segoe UI", 15, "bold"), bg=self._accent,
            fg=self._accent_fg, anchor="w"
        ).pack(side=tk.LEFT, padx=14, pady=10)
        tk.Button(
            header, text="Close", command=win.destroy,
            relief="flat", bd=0, bg=self._button_bg, fg=self._button_fg,
            activebackground=self._button_hover_bg, activeforeground=self._button_fg,
            padx=12, pady=4, cursor="hand2"
        ).pack(side=tk.RIGHT, padx=12, pady=8)

        body = tk.Frame(win, bg=self._panel_bg)
        body.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=0)
        body.grid_columnconfigure(1, weight=1)

        # --------------------------------------------------------------
        # Left: bookmark tree -- sections, widget categories, and every
        # individual element, so a long guide is still one click away
        # from any topic.
        # --------------------------------------------------------------
        tree_frame = tk.Frame(body, width=230, bg=self._panel_bg)
        tree_frame.grid(row=0, column=0, sticky="ns", padx=(0, 8))
        tree_frame.grid_propagate(False)
        tree_frame.grid_rowconfigure(1, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        tree_header = tk.Label(
            tree_frame, text="BOOKMARKS", font=("Segoe UI", 9, "bold"),
            bg=self._panel_bg, fg=self._panel_fg, anchor="w"
        )
        tree_header.grid(row=0, column=0, sticky="ew", padx=4, pady=(2, 4))

        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
        bookmark_tree = ttk.Treeview(
            tree_frame, show="tree", selectmode="browse",
            yscrollcommand=tree_scroll.set
        )
        tree_scroll.configure(command=bookmark_tree.yview)
        bookmark_tree.grid(row=1, column=0, sticky="nsew")
        tree_scroll.grid(row=1, column=1, sticky="ns")

        # --------------------------------------------------------------
        # Right: Find bar + the help text itself.
        # --------------------------------------------------------------
        right_frame = tk.Frame(body, bg=self._panel_bg)
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        colors = self._get_theme_colors()
        search_frame = tk.Frame(right_frame, bg=colors.get("search_frame_bg", self._panel_bg))
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        search_frame.grid_columnconfigure(1, weight=1)

        find_label = tk.Label(
            search_frame, text="Find:", bg=colors.get("search_frame_bg", self._panel_bg),
            fg=self._panel_fg
        )
        find_label.grid(row=0, column=0, padx=(6, 4), pady=6, sticky="w")

        find_var = tk.StringVar()
        find_entry = tk.Entry(
            search_frame, textvariable=find_var,
            bg=self._entry_bg, fg=self._entry_fg,
            insertbackground=colors.get("entry_insert", self._entry_fg),
            relief="solid", bd=1, highlightthickness=1,
            highlightbackground=colors.get("entry_border", self._panel_bg),
            highlightcolor=self._accent
        )
        find_entry.grid(row=0, column=1, padx=(0, 6), pady=6, sticky="ew")

        search_status_var = tk.StringVar(value="")
        search_status_label = tk.Label(
            search_frame, textvariable=search_status_var,
            bg=colors.get("search_frame_bg", self._panel_bg), fg=self._muted_fg
        )
        search_status_label.grid(row=0, column=2, padx=(0, 8))

        text_frame = tk.Frame(right_frame, bg=self._panel_bg)
        text_frame.grid(row=1, column=0, sticky="nsew")
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        text = tk.Text(
            text_frame, wrap="word", font=("Segoe UI", 10),
            bg=self._entry_bg, fg=self._panel_fg, relief="flat", borderwidth=0,
            padx=14, pady=10
        )
        scroll = ttk.Scrollbar(text_frame, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        text.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        text.tag_configure("title", font=("Segoe UI", 16, "bold"), spacing3=8)
        text.tag_configure("h1", font=("Segoe UI", 13, "bold"), spacing1=14, spacing3=6)
        text.tag_configure("h2", font=("Segoe UI", 11, "bold"), spacing1=8, spacing3=3)
        text.tag_configure("muted", foreground=self._muted_fg)
        text.tag_configure("code", font=("Consolas", 9), background=self._button_hover_bg,
                           foreground=self._panel_fg)
        text.tag_configure("search_match", background=colors.get("search_match_bg", "#FFF3CD"),
                           foreground=colors.get("search_match_fg", self._panel_fg))
        text.tag_configure("search_current", background=colors.get("search_current_bg", self._accent),
                           foreground=colors.get("search_current_fg", self._accent_fg))
        text.tag_configure("bookmark_jump", background=colors.get("highlight_bg", "#FFF3CD"),
                           foreground=colors.get("highlight_fg", self._panel_fg))

        bookmarks = []
        self._populate_help_text(text, bookmarks)
        text.configure(state="disabled")

        # --- Bookmark tree population ---
        # bookmarks is in document order, so every parent is guaranteed to
        # have already been inserted (and therefore exist as a valid iid)
        # by the time any of its children are appended.
        for idx, title, parent in bookmarks:
            bookmark_tree.insert(
                parent or "", "end", iid=idx, text=title, open=(parent is None)
            )

        def _on_bookmark_select(_event=None):
            selection = bookmark_tree.selection()
            if not selection:
                return
            idx = selection[0]
            text.see(idx)
            # A brief highlight so it's obvious where the jump landed,
            # rather than just a scroll position that's easy to lose in a
            # long guide.
            text.tag_remove("bookmark_jump", "1.0", "end")
            text.tag_add("bookmark_jump", f"{idx} linestart", f"{idx} lineend+1c")
            win.after(1200, lambda: text.tag_remove("bookmark_jump", "1.0", "end"))

        bookmark_tree.bind("<<TreeviewSelect>>", _on_bookmark_select)

        # --- Find bar behavior ---
        search_matches = []
        current_match = [0]

        def _clear_search_tags():
            try:
                text.tag_remove("search_match", "1.0", "end")
                text.tag_remove("search_current", "1.0", "end")
            except tk.TclError:
                pass

        def _collect_matches(query):
            matches = []
            if not query:
                return matches
            pos = "1.0"
            while True:
                found = text.search(query, pos, stopindex="end", nocase=True)
                if not found:
                    break
                end_pos = text.index(f"{found} + {len(query)} chars")
                matches.append((found, end_pos))
                next_pos = text.index(f"{found} + 1 chars")
                if text.compare(next_pos, ">=", "end"):
                    break
                pos = next_pos
            return matches

        def _refresh_search(reset_index=True):
            nonlocal search_matches
            _clear_search_tags()
            query = find_var.get()
            if not query:
                search_matches = []
                search_status_var.set("")
                return
            search_matches = _collect_matches(query)
            if not search_matches:
                search_status_var.set("0 matches")
                return
            if reset_index:
                current_match[0] = 0
            else:
                current_match[0] = min(current_match[0], len(search_matches) - 1)
            for s_idx, e_idx in search_matches:
                text.tag_add("search_match", s_idx, e_idx)
            _highlight_current()

        def _highlight_current():
            if not search_matches:
                return
            s_idx, e_idx = search_matches[current_match[0]]
            text.tag_remove("search_match", s_idx, e_idx)
            text.tag_add("search_current", s_idx, e_idx)
            text.see(s_idx)
            search_status_var.set(f"{current_match[0] + 1} of {len(search_matches)} matches")

        def _find_next(event=None):
            if not find_var.get():
                return "break"
            if not search_matches:
                _refresh_search()
            if not search_matches:
                return "break"
            s_idx, e_idx = search_matches[current_match[0]]
            text.tag_remove("search_current", s_idx, e_idx)
            text.tag_add("search_match", s_idx, e_idx)
            current_match[0] = (current_match[0] + 1) % len(search_matches)
            _highlight_current()
            return "break"

        def _find_previous(event=None):
            if not find_var.get():
                return "break"
            if not search_matches:
                _refresh_search()
            if not search_matches:
                return "break"
            s_idx, e_idx = search_matches[current_match[0]]
            text.tag_remove("search_current", s_idx, e_idx)
            text.tag_add("search_match", s_idx, e_idx)
            current_match[0] = (current_match[0] - 1) % len(search_matches)
            _highlight_current()
            return "break"

        def _find_var_changed(*_args):
            _refresh_search(reset_index=True)

        def _find_escape(_event=None):
            _clear_search_tags()
            find_var.set("")
            search_status_var.set("")
            text.focus_set()
            return "break"

        find_var.trace_add("write", _find_var_changed)
        find_entry.bind("<Return>", _find_next)
        find_entry.bind("<Shift-Return>", _find_previous)
        find_entry.bind("<F3>", _find_next)
        find_entry.bind("<Shift-F3>", _find_previous)
        find_entry.bind("<Escape>", _find_escape)

        prev_btn = self._flat_button(search_frame, "◀ Prev", _find_previous)
        prev_btn.grid(row=0, column=3, padx=(0, 4), pady=6)
        next_btn = self._flat_button(search_frame, "Next ▶", _find_next)
        next_btn.grid(row=0, column=4, padx=(0, 8), pady=6)

        def _focus_find(_event=None):
            find_entry.focus_set()
            find_entry.selection_range(0, "end")
            return "break"

        win.bind("<Control-f>", _focus_find)
        win.bind("<F3>", _find_next)
        win.bind("<Shift-F3>", _find_previous)

        win._theme_widgets = {
            "header": header,
            "title_label": header.winfo_children()[0],
            "close_button": header.winfo_children()[1],
            "body": body,
            "text": text,
            "tree_frame": tree_frame,
            "tree_header": tree_header,
            "search_frame": search_frame,
            "find_label": find_label,
            "find_entry": find_entry,
            "search_status_label": search_status_label,
            "prev_button": prev_btn,
            "next_button": next_btn,
        }

        win.bind("<Escape>", lambda _e: win.destroy())
        win.protocol("WM_DELETE_WINDOW", win.destroy)
        find_entry.focus_set()

    def _populate_help_text(self, text, bookmarks=None):
        """Write the full Help Guide body into `text`.

        When `bookmarks` is passed (a list), every numbered top-level
        section, every widget category inside section 3, and every
        individual element within a category gets appended to it as
        (index, title, parent_index) -- index is a plain Tk text index
        string ("42.0") captured with text.index("end-1c") right before
        that heading/line is inserted. Because content is only ever
        appended (never inserted earlier), that index string stays valid
        for the lifetime of the widget -- no separate Tk marks needed.
        _open_help() turns this list into the bookmark Treeview.
        """
        def mark(title, parent=None):
            if bookmarks is None:
                return None
            idx = text.index("end-1c")
            bookmarks.append((idx, title, parent))
            return idx

        text.insert("end", "Tkinter Visual Designer\n", "title")
        text.insert("end", "Full user guide: interface, elements, properties, selection, code generation, and shortcuts.\n\n", "muted")

        mark("1. Main interface")
        text.insert("end", "1. Main interface\n", "h1")
        text.insert("end", "Top bar — file operations, undo/redo, canvas actions, code tools, context help, and this guide.\n")
        text.insert("end", "Toolbox — choose a widget/container and click the canvas to place it. Categories organize the available controls.\n")
        text.insert("end", "Design canvas — move, resize, select, and arrange elements. Ctrl+mouse wheel changes zoom. Shift-click adds an element to the current selection; Ctrl-click toggles the clicked element on/off. While dragging, nearby element edges/centers create temporary alignment guides and the moving selection snaps to them. Hovering a selected element's orange handle (or the canvas's own edge handles when nothing is selected) swaps the mouse cursor to match that handle's drag direction.\n")
        text.insert("end", "Properties — edit the selected element's configuration. Values are applied live and feed the code generator.\n")
        text.insert("end", "Live Code — optional generated Python source view; use Toggle Code to show/hide it.\n\n")

        mark("2. Contextual hover help")
        text.insert("end", "2. Contextual hover help\n", "h1")
        text.insert("end", "Click the ? button in the top bar to enable Context Help Mode. With it enabled, hover over a toolbox item, a canvas element, or a major interface control to see a description. The same behavior works in both normal and compact toolbox modes. Click ? again to disable it.\n\n")

        sec3 = mark("3. GUI elements and properties")
        text.insert("end", "3. GUI elements and properties\n", "h1")
        categories = {}
        for name, info in ELEMENT_TYPES.items():
            categories.setdefault(info.get("category", "Other"), []).append(name)
        for category, names in categories.items():
            cat_mark = mark(category, parent=sec3)
            text.insert("end", f"{category}\n", "h2")
            for name in names:
                info = ELEMENT_TYPES[name]
                mark(name, parent=cat_mark)
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

        mark("4. Selection and containers")
        text.insert("end", "4. Selection and containers\n", "h1")
        text.insert("end", "Containers include Frame, LabelFrame, Notebook, and PanedWindow. Elements can belong to a container; moving/removing a container therefore affects its children according to the builder's current container rules.\n")
        text.insert("end", "Ctrl+A selects all elements on the canvas. Ctrl+Shift+A selects only elements in the active container scope. Right-drag creates a scoped selection box.\n\n")

        mark("5. Code generation and events")
        text.insert("end", "5. Code generation and events\n", "h1")
        text.insert("end", "The builder keeps a live Python representation of the design. Elements with supported events receive generated handler stubs. Editing properties updates the generated code, while the code editor preserves user-added custom module/class regions supported by the project.\n\n")

        mark("6. Keyboard shortcuts")
        text.insert("end", "6. Keyboard shortcuts\n", "h1")
        for shortcut, desc in KEYBOARD_HELP:
            text.insert("end", f"{shortcut:<22} {desc}\n", "code")
        text.insert("end", "\n")

        mark("7. Practical workflow")
        text.insert("end", "7. Practical workflow\n", "h1")
        text.insert("end", "1) Choose a toolbox element.  2) Click the canvas to place it.  3) Select it and edit Properties.  4) Arrange/resize and group elements inside containers.  5) Use Run Preview to validate the generated application.  6) Save the .tvd design when satisfied.\n\n")

        mark("8. Built-in tooltip property")
        text.insert("end", "8. Built-in tooltip property\n", "h1")
        text.insert("end", "Most design elements expose a Tooltip property. This is separate from the builder's Context Help Mode: Tooltip is text intended for the generated application, while Context Help is documentation for the designer itself.\n\n")

        mark("9. Backgrounds and content alignment")
        text.insert("end", "9. Backgrounds and content alignment\n", "h1")
        text.insert("end", "Any element can carry its own Background Image, Image Mode (Stretch, Fill, Fit, Center, Tile, or None), and Image Alignment, independent of the dedicated Image element (Status Bar is the one exception -- it carries no background-image properties at all). Label, Button, Checkbutton, Radiobutton, and LinkLabel additionally expose Content Alignment and an Image + Text (compound) option so text and an image can share the same control. The whole design canvas / generated window can also carry its own background image through Canvas Settings, using the same Mode and Alignment options.\n\n")

        mark("10. Canvas settings, window state, and lock")
        text.insert("end", "10. Canvas settings, window state, and lock\n", "h1")
        text.insert("end", "With nothing selected, the Properties panel shows Canvas Settings: canvas width/height, canvas background color, an optional canvas-level Background Image with its own Mode/Alignment, Window State (Normal, Maximized, Minimized, or Centered), and Locked. Enabling Locked calls root.resizable(False, False) in the generated and previewed application, disabling manual resizing and the native maximize control. Any Status Bar element on the canvas automatically re-docks itself to the new bottom edge and width whenever you resize the canvas here, or by dragging the canvas's own resize handle.\n\n")

        mark("11. Instrumentation and dashboard widgets")
        text.insert("end", "11. Instrumentation and dashboard widgets\n", "h1")
        text.insert("end", "The Instrumentation toolbox category adds Push Button, Radio Option, LED Digit, LED Display, LED Indicator, Gauge / Meter, and Measurement Display. These are drawn with a self-contained runtime that is embedded directly into generated Python source, so exported applications never need to import the GUI Builder package. An LED Indicator can optionally mirror, toggle with, or momentarily follow another control through its Source Widget and Source Mode properties.\n\n")

        mark("12. Grouping and the canvas context menu")
        text.insert("end", "12. Grouping and the canvas context menu\n", "h1")
        text.insert("end", "Right-click the canvas to open a context menu for the clicked element or the current selection: Copy, Paste, Delete, Group Selected, Ungroup Selected, Bring to Front, and Send to Back. Selected controls also expose type-specific actions, such as editing an LED's value/state or a Gauge's value directly. Grouping is a design-time convenience only -- it assigns a shared Group ID so elements can be selected and moved together, without inserting an extra runtime container into the generated application.\n\n")

        mark("13. Date and time input")
        text.insert("end", "13. Date and time input\n", "h1")
        text.insert("end", "Calendar places a full month-view date picker on the canvas. DateTimePicker instead places a compact entry field with a pop-up calendar, and can be configured to show a Date, a Time, both, or a Custom strftime-style pattern through its Display Format, Calendar Date Format, and Time Format properties.\n\n")

        mark("14. Themes and toolbox layout")
        text.insert("end", "14. Themes and toolbox layout\n", "h1")
        text.insert("end", "The theme selector in the top bar switches the entire builder between Light and Dark. The toolbox can be switched between a labeled list and a compact icon grid; both layouts support Context Help Mode identically, and list mode uses a compact, IDE-style row density.\n\n")

        mark("15. LinkLabel and Status Bar")
        text.insert("end", "15. LinkLabel and Status Bar\n", "h1")
        text.insert("end", "LinkLabel is a hyperlink-styled Label (blue/underlined by default, hand cursor). Its URL property, if set, opens the link in the system browser on click via a generated webbrowser.open() call, in addition to the usual generated click-handler stub -- so both run on the same click. Status Bar docks itself to the bottom of the canvas at full width the instant it's placed, regardless of where you clicked to add it, and re-docks itself automatically whenever the canvas is resized afterward. It has no background-image properties by design.\n\n")

        mark("16. Finding text in this guide")
        text.insert("end", "16. Finding text in this guide\n", "h1")
        text.insert("end", "Use the Find bar above this text (or press Ctrl+F) to search the whole guide. Enter/F3 jumps to the next match, Shift+Enter/Shift+F3 to the previous one, and Escape clears the highlighting. The Bookmarks tree on the left jumps straight to any section, widget category, or individual element.\n")


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
