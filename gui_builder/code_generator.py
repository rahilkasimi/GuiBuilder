"""Source-code generation for exported applications."""
from .dependencies import *
from .config import *
from .models import DesignElement
from .instrumentation_widgets import INSTRUMENTATION_RUNTIME_CODE


# ─── CodeGenerator ──────────────────────────────────────────────────────────
#
# NOTE ON STRUCTURE: generate() (full-script regeneration) and
# generate_element_lines() (single-element incremental splice, used by
# PropertiesMixin._update_code_for_element and
# CodeMixin._insert_code_for_new_elements) used to each independently
# reimplement the same per-element widget/property/extra-lines logic.
# generate() now simply calls generate_element_lines() once per element in
# its ordered loop -- there is exactly one place that knows how to turn a
# DesignElement into widget-creation code.

class CodeGenerator:
    @staticmethod
    def _container_depth(
            elem: DesignElement, by_id: Dict[int, DesignElement]
    ) -> int:
        depth = 0
        seen = set()
        current = elem
        while current.parent_id is not None and current.parent_id in by_id and current.parent_id not in seen:
            seen.add(current.parent_id)
            current = by_id[current.parent_id]
            depth += 1
        return depth

    @staticmethod
    def _is_visible(elem: DesignElement) -> bool:
        """Whether the Visible property (present on every element type,
        default on) is currently on. Missing/blank counts as visible so
        elements created before this property existed -- or that never
        touched it -- behave exactly as before. Accepts "Yes"/"No" (the
        current property values) case-insensitively, plus the legacy
        "1"/"0" a project saved before that switch may still have stored.
        """
        v = str(elem.props.get("visible", "yes")).strip().lower()
        return v not in ("no", "0", "false")

    @staticmethod
    def _place_line(elem: DesignElement, var_name: str, rel_x, rel_y) -> str:
        """Build the "self._elem_N.place(...)" statement, honoring the
        Visible property. The widget is always created and placed either
        way -- so its geometry is established and any handler code that
        later calls self._elem_N.place(...) to reveal it keeps working --
        it's just immediately hidden again with place_forget() when
        Visible is off, right on the same line so the callers that splice
        a single place_line back into an existing script (see
        PropertiesMixin._update_code_for_element) don't need to know
        anything changed.

        Every generated widget is plain tkinter/ttk, and every one of them
        takes its on-screen size from place()'s own width/height rather
        than from a constructor kwarg (unlike CustomTkinter widgets, which
        size themselves via the constructor and ignore place(width=...) --
        that distinction no longer applies now that nothing here is CTk).
        """
        width = round(float(elem.canvas_w), 2)
        height = round(float(elem.canvas_h), 2)
        line = (f"        {var_name}.place(x={rel_x}, y={rel_y}, "
                f"width={width:.2f}, height={height:.2f})")
        if not CodeGenerator._is_visible(elem):
            line += f"; {var_name}.place_forget()  # Visible = Off"
        return line

    @staticmethod
    def _image_widget_line(
            elem: DesignElement, var_name: str, parent_name: str
    ) -> str:
        """Build the widget-creation statement(s) for an Image element.

        When a file is configured this is deliberately multi-line (a
        try/except around Image.open()/ImageTk.PhotoImage()) so a missing
        or unreadable file degrades to a visible "[Image Error]" label in
        the exported app instead of crashing it outright at startup.
        Callers that only ever splice a single "self._elem_N = ..." line
        back into an existing script (see
        PropertiesMixin._update_code_for_element) specifically check for
        "\\n" in the return value and fall back to a full regenerate when
        it's present, rather than trying to patch a multi-line block in
        place.
        """
        props = elem.props
        raw_path = str(props.get("image_path", "") or "").strip()
        keep_aspect = str(props.get("keep_aspect", 1)) not in (
            "0", "False", "false", ""
        )
        bg = props.get("bg") or ""
        bg_kw = f", bg={json.dumps(bg)}" if bg else ""

        if not raw_path:
            return f"        {var_name} = tk.Label({parent_name}, text='[No Image]'{bg_kw})"

        w = max(1, int(round(float(elem.canvas_w))))
        h = max(1, int(round(float(elem.canvas_h))))
        tag = str(elem.elem_id)
        lines = [
            "        try:",
            f"            _img_path_{tag} = os.path.join("
            f"os.path.dirname(os.path.abspath(__file__)), "
            f"{json.dumps(raw_path)})",
            f"            _pil_img_{tag} = Image.open(_img_path_{tag})",
        ]
        if keep_aspect:
            lines.append(f"            _pil_img_{tag}.thumbnail(({w}, {h}))")
        else:
            lines.append(
                f"            _pil_img_{tag} = "
                f"_pil_img_{tag}.resize(({w}, {h}))"
            )
        # Keep the PhotoImage referenced on self (the same object lifetime
        # as the widget itself). Unlike CTkImage, a plain
        # ImageTk.PhotoImage is garbage-collected as soon as there's no
        # remaining reference to it -- a purely-local variable here would
        # be freed the moment this method returns, leaving the label
        # blank despite no error being raised anywhere.
        lines.append(
            f"            self._elem_{tag}_img = ImageTk.PhotoImage(_pil_img_{tag})"
        )
        lines.append(
            f"            {var_name} = tk.Label({parent_name}, "
            f"image=self._elem_{tag}_img{bg_kw})"
        )
        lines.append("        except Exception as e:")
        lines.append("            print('Image load error:', e)")
        lines.append(
            f"            {var_name} = tk.Label({parent_name}, "
            f"text='[Image Error]'{bg_kw})"
        )
        return "\n".join(lines)

    @staticmethod
    def _calendar_widget_line(
            elem: DesignElement, var_name: str, parent_name: str
    ) -> str:
        """Build the single widget-creation statement for a Calendar
        element (tkcalendar.Calendar). Kept to one line -- unlike Image --
        so property edits (date format, initial date, colors, etc.) can
        still go through the fast incremental splice path.
        """
        props = elem.props

        def _parse_date(s: str):
            s = str(s or "").strip()
            if not s:
                return None
            try:
                return datetime.strptime(s, "%Y-%m-%d")
            except ValueError:
                return None  # invalid/partial date typed so far -- ignore it

        date_pattern = str(props.get("date_pattern") or "yyyy-mm-dd")
        selectmode = str(props.get("selectmode") or "day")
        bg = props.get("bg", "")
        fg = props.get("fg", "")
        firstweekday = str(props.get("firstweekday") or "monday").strip().lower()
        showweeknumbers = str(
            props.get("showweeknumbers", "Yes")
        ).strip().lower() not in ("no", "0", "false")
        selectbackground = props.get("selectbackground", "")
        normalbackground = props.get("normalbackground", "")

        kwargs = [f"selectmode={json.dumps(selectmode)}",
                  f"date_pattern={json.dumps(date_pattern)}",
                  f"showweeknumbers={showweeknumbers}"]
        if bg:
            kwargs.append(f"background={json.dumps(str(bg))}")
        if fg:
            kwargs.append(f"foreground={json.dumps(str(fg))}")
        if firstweekday in ("monday", "sunday"):
            kwargs.append(f"firstweekday={json.dumps(firstweekday)}")
        if selectbackground:
            kwargs.append(
                f"selectbackground={json.dumps(str(selectbackground))}"
            )
        if normalbackground:
            kwargs.append(
                f"normalbackground={json.dumps(str(normalbackground))}"
            )

        d = _parse_date(props.get("initial_date", ""))
        if d:
            kwargs.extend([f"year={d.year}", f"month={d.month}",
                            f"day={d.day}"])

        # mindate/maxdate need actual datetime.date objects (not plain
        # ints like the initial year/month/day above) -- the exported
        # script picks up the "from datetime import date" import added in
        # generate()/_empty_template() whenever any Calendar is present.
        md = _parse_date(props.get("mindate", ""))
        if md:
            kwargs.append(f"mindate=date({md.year}, {md.month}, {md.day})")
        xd = _parse_date(props.get("maxdate", ""))
        if xd:
            kwargs.append(f"maxdate=date({xd.year}, {xd.month}, {xd.day})")

        return f"        {var_name} = Calendar({parent_name}, {', '.join(kwargs)})"

    @staticmethod
    def _combobox_widget_line(
            elem: DesignElement, var_name: str, parent_name: str
    ) -> str:
        """Build the widget-creation statement for a Combobox element
        (always ttk.Combobox -- the only tkinter combobox that supports
        every property this element exposes, including a capped/scrollable
        dropdown via Max Dropdown Rows -> its native `height` option).
        """
        props = elem.props
        values = props.get("values", [])
        if not isinstance(values, list):
            values = []
        if str(props.get("sorted", "No")).strip().lower() in ("yes", "1", "true"):
            values = sorted(values, key=lambda s: str(s).lower())

        state = props.get("state", "readonly")
        font = props.get("font")
        if isinstance(font, list):
            font = tuple(font)
        width = props.get("width", "")

        kwargs = [f"values={repr(values)}"]
        if state:
            kwargs.append(f"state={json.dumps(str(state))}")
        if str(width).strip() not in ("", "None"):
            try:
                kwargs.append(f"width={int(width)}")
            except (TypeError, ValueError):
                pass
        if font:
            kwargs.append(f"font={repr(font)}")

        maxdropdown = str(props.get("maxdropdown", "")).strip()
        if maxdropdown:
            try:
                n = int(maxdropdown)
                if n > 0:
                    kwargs.append(f"height={n}")
            except ValueError:
                pass

        border_width = props.get("border_width", "")
        style_name = f"BuilderCombobox{elem.elem_id}.TCombobox"
        if str(border_width).strip() not in ("", "None"):
            try:
                bw = int(border_width)
                if bw >= 0:
                    kwargs.append(f"style={json.dumps(style_name)}")
            except (TypeError, ValueError):
                border_width = ""

        return f"        {var_name} = ttk.Combobox({parent_name}, {', '.join(kwargs)})"

    @staticmethod
    def _combobox_maxlength_line(elem: DesignElement, var_name: str) -> Optional[str]:
        """A bound <KeyRelease> handler that truncates the combobox's
        typed text to Max Length characters, if set.

        ttk.Combobox exposes no native maxlength-style option (unlike,
        say, an HTML <input>). Re-truncating via get()/set() on every
        keystroke is the simple approach that works regardless -- the
        trade-off is that, like any validatecommand-free approach, it
        always snaps the cursor to the end of the text, so it's most
        natural for a user who's typing forward rather than editing
        mid-string.
        """
        maxlength = str(elem.props.get("maxlength", "")).strip()
        if not maxlength:
            return None
        try:
            n = int(maxlength)
        except ValueError:
            return None
        if n <= 0:
            return None
        return (f"        {var_name}.bind('<KeyRelease>', "
                f"lambda e, _w={var_name}, _n={n}: _w.set(_w.get()[:_n]))")

    @staticmethod
    def _window_state_lines(window_state: str, indent: str, window_locked: bool = False) -> List[str]:
        """Lines that put the exported window into the configured initial
        state right after it's created.

        Both states are applied via root.after(...) instead of directly
        in __init__/main(): calling root.state('zoomed') /
        root.attributes('-zoomed', True) / root.iconify() immediately,
        right after root.geometry(...), races the window manager's own
        (asynchronous) handling of that geometry request -- the window
        visibly snaps to maximized for an instant and then the WM's
        delayed geometry processing overrides it back down to the
        explicit size a moment later. Deferring past the current event
        loop tick (and reapplying once more a little later, as a second
        safety net against any other startup geometry churn from the
        window manager) makes sure our call is the last one to run.
        iconify() is wrapped in the same try/except as maximize for the
        same reason: an exception raised while building the window (e.g.
        a window manager that errors on iconifying a not-yet-mapped
        window) would otherwise propagate out of __init__/main with no
        dialog or traceback for anyone running the exported .pyw file
        outside a console to see, which looks exactly like "the app
        closed itself". Normal needs no extra lines at all -- that's just
        how a freshly created Tk window already behaves.
        """
        if window_state == "Maximized":
            body = [
                "def _apply_window_state():",
                "    try:",
                "        if platform.system() in (\"Windows\", \"Darwin\"):",
                "            root.state('zoomed')",
                "        else:",
                "            root.attributes('-zoomed', True)",
                "    except Exception:",
                "        try:",
                "            root.state('zoomed')",
                "        except Exception:",
                "            pass",
                "root.after(10, _apply_window_state)",
                "root.after(250, _apply_window_state)",
            ]
        elif window_state == "Minimized":
            body = [
                "def _apply_window_state():",
                "    try:",
                "        root.iconify()",
                "    except Exception:",
                "        pass",
                "root.after(10, _apply_window_state)",
            ]
        else:
            body = []
        if window_locked:
            # A fixed runtime window should not be manually resized.  On
            # native Windows title bars this also disables the maximize
            # button while retaining the normal title-bar controls.
            body.extend([
                "try:",
                "    root.resizable(False, False)",
                "except tk.TclError:",
                "    pass",
            ])
        return [indent + line for line in body]

    @staticmethod
    def _instrumentation_types() -> set:
        return {
            "PushButton", "RadioButton", "LEDDigit", "LEDDisplay",
            "LEDIndicator", "Gauge", "MeasurementDisplay",
        }

    @staticmethod
    def _instrumentation_widget_line(
            elem: DesignElement, var_name: str, parent_name: str, props: Dict[str, Any]
    ) -> str:
        """Build constructor code for a custom instrumentation widget."""
        def q(key, default=""):
            return json.dumps(str(props.get(key, default)))

        width = round(float(elem.canvas_w), 2)
        height = round(float(elem.canvas_h), 2)

        if elem.elem_type == "PushButton":
            font = props.get("font", ("Segoe UI", 9, "bold"))
            if isinstance(font, list):
                font = tuple(font)
            if not isinstance(font, tuple):
                font = ("Segoe UI", 9, "bold")
            return (
                f"        {var_name} = BuilderPushButton({parent_name}, "
                f"text={q('text', 'Push Button')}, shape={q('shape', 'Square')}, "
                f"style={q('style', 'Mechanical')}, behavior={q('behavior', 'Momentary')}, "
                f"default_state={q('default_state', 'Off')}, font={repr(font)}, fg={q('fg', '#FFFFFF')}, "
                f"bg={q('bg', '#1976D2')}, active_bg={q('active_bg', '#0D47A1')}, "
                f"border_width={repr(props.get('border_width', 2) or 2)}, "
                f"command=__COMMAND__, width={width}, height={height})"
            )
        if elem.elem_type == "RadioButton":
            var_expr = f"self.{props.get('variable')}" if props.get('variable') else "None"
            font = props.get("font", ("Segoe UI", 9))
            if isinstance(font, list):
                font = tuple(font)
            if not isinstance(font, tuple):
                font = ("Segoe UI", 9)
            return (
                f"        {var_name} = BuilderRadioButton({parent_name}, "
                f"text={q('text', 'Option')}, variable={var_expr}, value={q('value', '1')}, "
                f"shape={q('shape', 'Round')}, selected={q('selected', 'No')}, font={repr(font)}, "
                f"fg={q('fg', '#212121')}, bg={q('bg', '#F5F5F5')}, "
                f"active_fg={q('active_fg', '#1976D2')}, active_bg={q('active_bg', '#1976D2')}, "
                f"command=__COMMAND__, width={width}, height={height})"
            )
        if elem.elem_type == "LEDDigit":
            return (
                f"        {var_name} = BuilderLEDDisplay({parent_name}, mode='Single Digit', "
                f"value={q('value', '0')}, digits=1, color={q('color', '#00FF66')}, "
                f"off_color={q('off_color', '#16351F')}, brightness={repr(props.get('brightness', 100) or 100)}, "
                f"glow={q('glow', 'Yes')}, leading_zeros='No', "
                f"segment_width={repr(props.get('segment_width', 4) or 4)}, digit_gap={repr(props.get('digit_gap', 12) or 12)}, bg={q('bg', '#101010')}, width={width}, height={height})"
            )
        if elem.elem_type == "LEDDisplay":
            return (
                f"        {var_name} = BuilderLEDDisplay({parent_name}, mode='Multi Digit', "
                f"value={q('value', '120')}, digits={repr(props.get('digits', 3) or 3)}, "
                f"color={q('color', '#00FF66')}, off_color={q('off_color', '#16351F')}, "
                f"brightness={repr(props.get('brightness', 100) or 100)}, glow={q('glow', 'Yes')}, "
                f"leading_zeros={q('leading_zeros', 'No')}, segment_width={repr(props.get('segment_width', 4) or 4)}, digit_gap={repr(props.get('digit_gap', 12) or 12)}, "
                f"bg={q('bg', '#101010')}, width={width}, height={height})"
            )
        if elem.elem_type == "LEDIndicator":
            return (
                f"        {var_name} = BuilderLEDIndicator({parent_name}, state={q('state', 'Off')}, "
                f"on_color={q('on_color', '#00FF66')}, off_color={q('off_color', '#16351F')}, "
                f"shape={q('shape', 'Round')}, brightness={repr(props.get('brightness', 100) or 100)}, "
                f"glow={q('glow', 'Yes')}, border_width={repr(props.get('border_width', 1) or 1)}, "
                f"bg={q('bg', '#E0E0E0')}, width={width}, height={height})"
            )
        if elem.elem_type == "Gauge":
            return (
                f"        {var_name} = BuilderGauge({parent_name}, value={repr(props.get('value', 50))}, "
                f"min_value={repr(props.get('min_value', 0))}, max_value={repr(props.get('max_value', 100))}, "
                f"start_angle={repr(props.get('start_angle', 225))}, end_angle={repr(props.get('end_angle', -45))}, "
                f"needle_color={q('needle_color', '#E53935')}, arc_color={q('arc_color', '#1976D2')}, "
                f"track_color={q('track_color', '#D9D9D9')}, tick_color={q('tick_color', '#555555')}, "
                f"ticks={repr(props.get('ticks', 10) or 10)}, show_value={q('show_value', 'Yes')}, "
                f"unit={q('unit', '')}, thickness={repr(props.get('thickness', 8) or 8)}, bg={q('bg', '#FFFFFF')}, width={width}, height={height})"
            )
        if elem.elem_type == "MeasurementDisplay":
            return (
                f"        {var_name} = BuilderMeasurementDisplay({parent_name}, label={q('label', 'Temperature')}, "
                f"value={q('value', '24')}, unit={q('unit', '°C')}, style={q('style', 'Modern')}, "
                f"color={q('color', '#1976D2')}, bg={q('bg', '#FFFFFF')}, "
                f"decimal_places={repr(props.get('decimal_places', 0) or 0)}, prefix={q('prefix', '')}, "
                f"suffix={q('suffix', '')}, secondary_text={q('secondary_text', '')}, "
                f"secondary_color={q('secondary_color', '#666666')}, align={q('align', 'center')}, "
                f"led_digits={repr(props.get('led_digits', 3) or 3)}, width={width}, height={height})"
            )
        raise ValueError(f"Unsupported instrumentation type: {elem.elem_type}")

    @staticmethod
    def _instrumentation_binding_lines(elements: List[DesignElement]) -> List[str]:
        """Generate post-construction state bindings, notably LED indicators."""
        by_id = {e.elem_id: e for e in elements}
        lines: List[str] = []
        for elem in elements:
            if elem.elem_type != "LEDIndicator":
                continue
            raw_source = str(elem.props.get("source_widget", "") or "").strip()
            try:
                source_id = int(raw_source)
            except (TypeError, ValueError):
                continue
            source = by_id.get(source_id)
            if source is None:
                continue
            led_var = f"self._elem_{elem.elem_id}"
            src_var = f"self._elem_{source.elem_id}"
            mode = str(elem.props.get("source_mode", "Mirror")).strip().lower()
            if source.elem_type == "PushButton":
                # BuilderPushButton exposes a state listener that already
                # distinguishes momentary press/release from toggle state.
                if mode == "toggle":
                    lines.append(f"        {src_var}.canvas.bind('<ButtonRelease-1>', lambda e, _led={led_var}: _led.set_state(not _led.get_state()), add='+')")
                else:
                    lines.append(f"        {src_var}.add_state_listener({led_var}.set_state)")
            elif source.elem_type == "RadioButton":
                if mode == "momentary":
                    lines.append(f"        {src_var}.canvas.bind('<ButtonPress-1>', lambda e, _led={led_var}: _led.set_state(True), add='+')")
                    lines.append(f"        {src_var}.canvas.bind('<ButtonRelease-1>', lambda e, _led={led_var}: _led.set_state(False), add='+')")
                elif mode == "toggle":
                    lines.append(f"        {src_var}.canvas.bind('<ButtonRelease-1>', lambda e, _led={led_var}: _led.set_state(not _led.get_state()), add='+')")
                else:
                    lines.append(f"        {src_var}.add_state_listener({led_var}.set_state)")
            elif source.elem_type == "Radiobutton":
                variable = source.props.get("variable")
                value = str(source.props.get("value", "1"))
                if variable:
                    state_expr = f"str(self.{variable}.get()) == {json.dumps(value)}"
                    lines.append(f"        {src_var}.bind('<ButtonRelease-1>', lambda e, _led={led_var}: _led.set_state({state_expr}), add='+')")
            elif source.elem_type == "Checkbutton":
                variable = source.props.get("variable")
                if variable:
                    if mode == "toggle":
                        lines.append(f"        {src_var}.bind('<ButtonRelease-1>', lambda e, _led={led_var}: _led.set_state(not _led.get_state()), add='+')")
                    else:
                        lines.append(f"        {src_var}.bind('<ButtonRelease-1>', lambda e, _led={led_var}, _src=self.{variable}: _led.set_state(bool(_src.get())), add='+')")
            elif mode == "toggle":
                lines.append(f"        {src_var}.bind('<ButtonRelease-1>', lambda e, _led={led_var}: _led.set_state(not _led.get_state()), add='+')")
        return lines

    @staticmethod
    def _scrollbar_binding_lines(elements: List[DesignElement]) -> List[str]:
        """Generate post-construction bindings for designer Scrollbars.

        The binding block is emitted after *all* widgets are created so a
        scrollbar can target a Text/Canvas that happens to appear later in
        the element ordering. The persisted relationship is an element ID,
        not a display caption.
        """
        by_id = {e.elem_id: e for e in elements}
        lines: List[str] = []
        for scrollbar in elements:
            if scrollbar.elem_type != "Scrollbar":
                continue
            raw_target = scrollbar.props.get("target_widget", "")
            try:
                target_id = int(raw_target)
            except (TypeError, ValueError):
                continue
            target = by_id.get(target_id)
            if target is None or target.elem_type not in ("Text", "Canvas"):
                continue

            sb_var = f"self._elem_{scrollbar.elem_id}"
            target_var = f"self._elem_{target.elem_id}"
            orient = str(scrollbar.props.get("orient", "vertical")).strip().lower()
            if orient == "horizontal":
                lines.append(
                    f"        {sb_var}.configure(command={target_var}.xview)"
                )
                lines.append(
                    f"        {target_var}.configure(xscrollcommand={sb_var}.set)"
                )
            else:
                lines.append(
                    f"        {sb_var}.configure(command={target_var}.yview)"
                )
                lines.append(
                    f"        {target_var}.configure(yscrollcommand={sb_var}.set)"
                )
        return lines

    # ─── Per-element code generation (single source of truth) ─────────────
    @staticmethod
    def generate_element_lines(
            elem: DesignElement, all_elements: List[DesignElement]
    ) -> Tuple[str, str, List[str]]:
        """Build (widget_line, place_line, extra_lines) for exactly one
        element. Used both by generate()'s full-script loop below and by
        the incremental single-element splice paths in PropertiesMixin /
        CodeMixin.
        """
        by_id = {e.elem_id: e for e in all_elements}
        extra_lines: List[str] = []

        var_name = f"self._elem_{elem.elem_id}"
        widget_class = ELEMENT_TYPES[elem.elem_type]["widget"]
        props = copy.deepcopy(elem.props)

        if elem.elem_type == "Label" and "justify" in props:
            justify = props["justify"]
            anchor_map = {"left": "w", "center": "center", "right": "e"}
            if "anchor" not in props:
                props["anchor"] = anchor_map.get(justify, "center")

        bindings = []
        for e in all_elements:
            if e.handler_code.strip():
                event = DEFAULT_EVENT_MAP.get(e.elem_type)
                if event:
                    bindings.append((e, event, f"self._elem_{e.elem_id}"))

        listbox_items = props.pop("items", []) if elem.elem_type == "Listbox" else []
        notebook_tabs = props.pop("tabs", ["Tab 1", "Tab 2"]) if elem.elem_type == "Notebook" else []
        if elem.elem_type == "Notebook":
            props.pop("active_tab", None)

        for b_elem, b_event, _ in bindings:
            if b_elem == elem and b_event == "command":
                props["command"] = f"self._on_{elem.elem_type}_{elem.elem_id}"

        if props.get("textvariable") == "":
            props.pop("textvariable", None)
        def_val = props.pop("default_value", None)
        tooltip_val = props.pop("tooltip", None)

        # Build the property string. Every remaining key in `props` is
        # already a real tkinter/ttk constructor keyword argument -- see
        # SKIPPED_GENERIC_PROPS in config.py for the (small) set of keys
        # that aren't, either because they're design-time-only controls or
        # because a dedicated code block elsewhere handles them instead.
        prop_strs = []
        color_keys = {
            "fg", "bg", "activebackground", "activeforeground",
            "highlightbackground", "highlightcolor", "insertbackground",
            "selectbackground", "selectforeground",
        }
        for k, v in props.items():
            # A font tuple accidentally stored in a color property is invalid
            # Tcl/Tk input.  Fall back to that element's configured default
            # rather than allowing a malformed project to crash Run Preview.
            if k in color_keys and not isinstance(v, str):
                fallback = ELEMENT_TYPES.get(elem.elem_type, {}).get(
                    "defaults", {}).get(k)
                if isinstance(fallback, str):
                    v = fallback
                else:
                    continue
            if k == "font" and isinstance(v, list):
                # Defense in depth: font must be emitted as a tuple
                # literal, never a list (tkinter raises for a list font
                # argument). from_dict() normalizes this already, but
                # guard here too in case a prop dict reaches this point
                # some other way.
                v = tuple(v)
            if k in SKIPPED_GENERIC_PROPS:
                continue
            if k == "variable":
                if v:
                    prop_strs.append(f"variable=self.{v}")
                continue
            elif k == "textvariable":
                if v:
                    prop_strs.append(f"textvariable=self.{v}")
                continue
            elif k in ("border_width", "bd"):
                # ttk widgets do not accept tkinter's constructor-level `bd`
                # option. Combobox/Notebook use a dedicated ttk style instead;
                # classic tkinter widgets keep the native bd option.
                if elem.elem_type in ("Combobox", "Notebook") and k == "border_width":
                    continue
                if v not in (None, ""):
                    try:
                        prop_strs.append(f"bd={int(v)}")
                    except (TypeError, ValueError):
                        pass
                continue
            elif k == "command" and isinstance(v, str) and v.startswith("self."):
                prop_strs.append(f"command={v}")
            elif k == "values" and isinstance(v, list):
                prop_strs.append(f"values={repr(v)}")
            elif k in ("from_", "to", "onvalue", "offvalue"):
                prop_strs.append(f"{k}={v}")
            elif isinstance(v, str):
                prop_strs.append(f"{k}={json.dumps(v)}")
            elif isinstance(v, (int, float)):
                prop_strs.append(f"{k}={v}")
            else:
                prop_strs.append(f"{k}={repr(v)}")

        prop_str = (", " + ", ".join(prop_strs)) if prop_strs else ""

        parent_name = "root"
        rel_x, rel_y = elem.x, elem.y
        if elem.parent_id is not None and elem.parent_id in by_id:
            parent_elem = by_id[elem.parent_id]
            if parent_elem.elem_type == "Notebook":
                tab_idx = elem.parent_tab if elem.parent_tab is not None else parent_elem.props.get(
                    "active_tab", 0
                )
                tabs_count = len(parent_elem.props.get("tabs", ["Tab 1"])) or 1
                tab_idx = max(0, min(int(tab_idx or 0), tabs_count - 1))
                parent_name = f"self._elem_{parent_elem.elem_id}_tab_{tab_idx}"
            else:
                parent_name = f"self._elem_{parent_elem.elem_id}"
            rel_x = elem.x - parent_elem.x
            rel_y = elem.y - parent_elem.y

        # --- Widget-creation line(s) ---
        if elem.elem_type == "Table":
            table_file = elem.props.get("file", "")
            table_sheet = elem.props.get("sheet", 0)
            columns_csv = elem.props.get("columns", "")
            table_height = int(elem.props.get("height", 8) or 8)

            lines = ["        columns = []"]
            if columns_csv:
                cols = [c.strip() for c in columns_csv.split(",") if c.strip()]
                lines.append(f"        columns = {repr(cols)}")
            lines.append(
                f"        {var_name} = ttk.Treeview({parent_name}, columns=columns, show='headings', height={table_height})"
            )
            lines.append("        for col in columns:")
            lines.append(f"            {var_name}.heading(col, text=col)")
            lines.append(f"            {var_name}.column(col, width=100, anchor='w')")
            if table_file:
                lines.append("        try:")
                lines.append("            import pandas as pd")
                if str(table_file).lower().endswith(('.xlsx', '.xls')):
                    lines.append(
                        f"            df = pd.read_excel({json.dumps(table_file)}, sheet_name={json.dumps(table_sheet) if table_sheet else 0})"
                    )
                else:
                    lines.append(
                        f"            df = pd.read_csv({json.dumps(table_file)})"
                    )
                lines.append("            if not columns:")
                lines.append("                columns = list(df.columns)")
                lines.append("                for col in columns:")
                lines.append(f"                    {var_name}.heading(col, text=col)")
                lines.append(f"                    {var_name}.column(col, width=100, anchor='w')")
                lines.append("            for _, row in df.head(10).iterrows():")
                lines.append(f"                {var_name}.insert('', 'end', values=list(row))")
                lines.append("        except Exception as e:")
                lines.append("            print('Table load error:', e)")
            widget_line = "\n".join(lines)
            place_line = CodeGenerator._place_line(elem, var_name, rel_x, rel_y)
            return widget_line, place_line, []

        if elem.elem_type in CodeGenerator._instrumentation_types():
            widget_line = CodeGenerator._instrumentation_widget_line(
                elem, var_name, parent_name, props
            )
            # Dedicated instrumentation constructors accept a command only for
            # command-capable elements. The placeholder is resolved here so
            # generated handlers remain identical to the existing event model.
            command_target = f"self._on_{elem.elem_type}_{elem.elem_id}"
            if elem.elem_type in ("PushButton", "RadioButton") and any(
                    b_elem == elem and b_event == "command" for b_elem, b_event, _ in bindings
            ):
                widget_line = widget_line.replace("__COMMAND__", command_target)
            else:
                widget_line = widget_line.replace("command=__COMMAND__", "command=None")
        elif elem.elem_type == "Image":
            widget_line = CodeGenerator._image_widget_line(elem, var_name, parent_name)
        elif elem.elem_type == "Calendar":
            widget_line = CodeGenerator._calendar_widget_line(elem, var_name, parent_name)
        elif elem.elem_type == "Combobox":
            widget_line = CodeGenerator._combobox_widget_line(elem, var_name, parent_name)
        else:
            widget_line = f"        {var_name} = {widget_class}({parent_name}{prop_str})"

        # --- Extra lines for specific widgets ---
        if elem.elem_type == "Notebook":
            border_width = elem.props.get("border_width", "")
            notebook_style = f"BuilderNotebook{elem.elem_id}.TNotebook"
            try:
                bw = int(border_width) if str(border_width).strip() not in ("", "None") else None
            except (TypeError, ValueError):
                bw = None
            if bw is not None and bw >= 0:
                extra_lines.append(
                    f"        ttk.Style().configure({json.dumps(notebook_style)}, borderwidth={bw})"
                )
                widget_line = widget_line[:-1] + f", style={json.dumps(notebook_style)})"
            if not notebook_tabs:
                notebook_tabs = ["Tab 1"]
            for i, tab_title in enumerate(notebook_tabs):
                # ttk.Notebook tabs are ordinary child widgets added via
                # .add(child, text=...) -- unlike CTkTabview's .add(name),
                # which both creates and names a tab in one call. Each
                # tab's Frame is what child elements nested in that tab
                # are placed into (see parent_name resolution above,
                # self._elem_N_tab_i), so it must exist before any of
                # them are generated -- guaranteed by the containers-first
                # element ordering in generate().
                extra_lines.append(f"        {var_name}_tab_{i} = tk.Frame({var_name})")
                extra_lines.append(
                    f"        {var_name}.add({var_name}_tab_{i}, text={json.dumps(str(tab_title))})"
                )
            active_tab = int(elem.props.get("active_tab", 0) or 0)
            active_tab = max(0, min(active_tab, len(notebook_tabs) - 1))
            extra_lines.append(f"        {var_name}.select({var_name}_tab_{active_tab})")

        if elem.elem_type == "Combobox":
            border_width = elem.props.get("border_width", "")
            try:
                bw = int(border_width) if str(border_width).strip() not in ("", "None") else None
            except (TypeError, ValueError):
                bw = None
            if bw is not None and bw >= 0:
                extra_lines.append(
                    f"        ttk.Style().configure({json.dumps(f'BuilderCombobox{elem.elem_id}.TCombobox')}, borderwidth={bw})"
                )

        # LabelFrame: no extra lines needed -- tk.LabelFrame has a native
        # "text"/"font" title, which already passes through the generic
        # prop_str loop above like any other property.
        # Progressbar: no extra lines needed -- ttk.Progressbar takes
        # "value"/"maximum" directly as constructor kwargs (both already
        # pass through the generic prop_str loop above); it has no
        # CTkProgressBar-style fraction-based .set() method.

        if def_val is not None and str(def_val).strip() != "":
            if elem.elem_type == "Checkbutton":
                var_name_chk = copy.deepcopy(elem.props).get("variable")
                if var_name_chk:
                    extra_lines.append(
                        f"        self.{var_name_chk}.set({json.dumps(def_val)})"
                    )
                elif str(def_val).lower() in ("1", "true", "yes"):
                    extra_lines.append(f"        {var_name}.select()")
            elif elem.elem_type == "Spinbox":
                extra_lines.append(f"        {var_name}.delete(0, 'end')")
                extra_lines.append(
                    f"        {var_name}.insert(0, {json.dumps(str(def_val))})"
                )
            elif elem.elem_type == "Entry":
                extra_lines.append(
                    f"        {var_name}.insert(0, {json.dumps(str(def_val))})"
                )
            elif elem.elem_type == "Combobox":
                extra_lines.append(
                    f"        {var_name}.set({json.dumps(str(def_val))})"
                )
            elif elem.elem_type == "Scale":
                try:
                    num_val = float(def_val) if "." in str(def_val) else int(def_val)
                    extra_lines.append(f"        {var_name}.set({num_val})")
                except (ValueError, TypeError):
                    pass

        if elem.elem_type == "Listbox" and listbox_items:
            if str(elem.props.get("sorted", "No")).strip().lower() in (
                    "yes", "1", "true"
            ):
                listbox_items = sorted(listbox_items, key=lambda s: str(s).lower())
            for item in listbox_items:
                extra_lines.append(
                    f"        {var_name}.insert('end', {json.dumps(item)})"
                )

        if elem.elem_type == "Combobox":
            maxlen_line = CodeGenerator._combobox_maxlength_line(elem, var_name)
            if maxlen_line:
                extra_lines.append(maxlen_line)

        if elem.elem_type == "RadioButton" and str(elem.props.get("selected", "No")).strip().lower() in ("yes", "1", "true"):
            extra_lines.append(f"        {var_name}.select()")

        if tooltip_val:
            extra_lines.append(
                f"        _ToolTip({var_name}, {json.dumps(str(tooltip_val))})"
            )

        place_line = CodeGenerator._place_line(elem, var_name, rel_x, rel_y)

        return widget_line, place_line, extra_lines

    # ─── Full-script generation ─────────────────────────────────────────────
    @staticmethod
    def generate(
            elements: List[DesignElement], window_title: str,
            window_size: Tuple[int, int], canvas_bg: str, canvas_imports: str,
            custom_module_code: str = "", custom_class_code: str = "",
            window_state: str = "Normal", window_locked: bool = False
    ) -> str:
        if not elements:
            return CodeGenerator._empty_template(window_title, window_size,
                                                  canvas_bg, canvas_imports,
                                                  custom_module_code,
                                                  custom_class_code,
                                                  window_state, window_locked)

        has_table = any(e.elem_type == "Table" for e in elements)
        if has_table and "import pandas as pd" not in canvas_imports:
            canvas_imports = canvas_imports.rstrip() + "\nimport pandas as pd"

        has_image = any(e.elem_type == "Image" for e in elements)
        if has_image:
            if "import os" not in canvas_imports:
                canvas_imports = canvas_imports.rstrip() + "\nimport os"
            if "from PIL import Image, ImageTk" not in canvas_imports:
                canvas_imports = canvas_imports.rstrip() + "\nfrom PIL import Image, ImageTk"

        has_calendar = any(e.elem_type == "Calendar" for e in elements)
        if has_calendar:
            if "from tkcalendar import Calendar" not in canvas_imports:
                canvas_imports = canvas_imports.rstrip() + "\nfrom tkcalendar import Calendar"
            if "from datetime import date" not in canvas_imports:
                canvas_imports = canvas_imports.rstrip() + "\nfrom datetime import date"

        if window_state == "Maximized" and "import platform" not in canvas_imports:
            canvas_imports = canvas_imports.rstrip() + "\nimport platform"

        by_id = {e.elem_id: e for e in elements}
        class_body: List[str] = []
        class_body.append("    def __init__(self, root):")
        class_body.append("        self.root = root")
        class_body.append(f"        root.title({json.dumps(window_title)})")
        class_body.append(
            f"        root.geometry({json.dumps(f'{int(round(float(window_size[0])))}x{int(round(float(window_size[1])))}')})"
        )
        class_body.append(
            f"        root.configure(bg={json.dumps(canvas_bg)})"
        )
        class_body.extend(
            CodeGenerator._window_state_lines(window_state, "        ", window_locked)
        )
        class_body.append("")

        vars_to_create = {}
        for elem in elements:
            if elem.elem_type in ("Radiobutton", "RadioButton", "Checkbutton"):
                var_name = elem.props.get("variable")
                if var_name and var_name not in vars_to_create:
                    var_type = "tk.IntVar(value=0)" if elem.elem_type == "Checkbutton" else "tk.StringVar(value='')"
                    vars_to_create[var_name] = var_type
            elif elem.elem_type == "Entry":
                var_name = elem.props.get("textvariable")
                if var_name and var_name not in vars_to_create:
                    vars_to_create[var_name] = "tk.StringVar(value='')"
        for v_name, v_type in vars_to_create.items():
            class_body.append(f"        self.{v_name} = {v_type}")
        if vars_to_create:
            class_body.append("")

        bindings = []
        for elem in elements:
            if elem.handler_code.strip():
                event = DEFAULT_EVENT_MAP.get(elem.elem_type)
                if event:
                    bindings.append(
                        (elem, event, f"self._elem_{elem.elem_id}")
                    )

        # Order elements: containers first, then by depth, then by id
        depths = {}
        for e in elements:
            depths[e.elem_id] = CodeGenerator._container_depth(e, by_id)
        ordered = sorted(elements, key=lambda e: (
            not (e.elem_type in CONTAINER_TYPES),  # containers first (False < True)
            depths.get(e.elem_id, 0),
            e.elem_id
        ))

        for elem in ordered:
            widget_line, place_line, extra_lines = CodeGenerator.generate_element_lines(
                elem, elements
            )
            class_body.extend(widget_line.splitlines())
            class_body.extend(extra_lines)
            class_body.append(place_line)

        scrollbar_bindings = CodeGenerator._scrollbar_binding_lines(elements)
        if scrollbar_bindings:
            class_body.append("")
            class_body.extend(scrollbar_bindings)

        instrumentation_bindings = CodeGenerator._instrumentation_binding_lines(elements)
        if instrumentation_bindings:
            class_body.append("")
            class_body.extend(instrumentation_bindings)

        # --- Bindings and handler methods ---
        for elem, event, var_name in bindings:
            if event != "command":
                method_name = f"_on_{elem.elem_type}_{elem.elem_id}"
                class_body.append(
                    f"        {var_name}.bind('{event}', self.{method_name})"
                )

        for elem, event, var_name in bindings:
            method_name = f"_on_{elem.elem_type}_{elem.elem_id}"
            class_body.append("")
            class_body.append(f"    def {method_name}(self, event=None):")

            if not elem.handler_code.strip():
                class_body.append(f'        """')
                class_body.append(f'        Event handler for {elem.elem_type} (ID: {elem.elem_id}).')
                class_body.append(f'        Triggered by: {event}')
                class_body.append(f'        Access widget instance via: {var_name}')
                class_body.append(f'        """')
                class_body.append(f"        pass")
            else:
                code_lines = elem.handler_code.strip().splitlines()
                for cline in code_lines:
                    class_body.append(
                        f"        {cline}" if cline.strip() else "        "
                    )

        class_body.append("")
        main_guard = [
            "", "if __name__ == '__main__':", "    root = tk.Tk()",
            "    app = MainApplication(root)", "    root.mainloop()",
        ]

        has_tooltips = any(e.props.get("tooltip") for e in elements)
        has_instrumentation = any(
            e.elem_type in CodeGenerator._instrumentation_types() for e in elements
        )
        helper_block = []
        if has_instrumentation:
            helper_block.extend([INSTRUMENTATION_RUNTIME_CODE.rstrip("\n"), ""])
        if has_tooltips:
            helper_block.extend([TOOLTIP_HELPER_CODE, ""])

        # Any code the user typed into the code editor that wasn't part of
        # the recognized boilerplate/handler regions -- module-level
        # constants, dicts, extra imports, standalone functions, or extra
        # methods appended to the class -- gets captured separately (see
        # _extract_custom_regions) specifically so a later full regenerate
        # (adding an element, undo/redo, etc.) doesn't silently wipe it.
        module_block = ([custom_module_code.rstrip("\n"), ""]
                         if custom_module_code.strip() else [])
        if custom_class_code.strip():
            class_body.append("")
            class_body.extend(custom_class_code.rstrip("\n").splitlines())

        return "\n".join([
                             '"""Generated by Tkinter Visual Designer."""', "",
                             canvas_imports, "",
                             *helper_block,
                             *module_block,
                             "class MainApplication:", *class_body, *main_guard,
                         ]
                         )

    @staticmethod
    def _empty_template(
            window_title: str, window_size: Tuple[int, int], canvas_bg: str,
            canvas_imports: str, custom_module_code: str = "",
            custom_class_code: str = "",
            window_state: str = "Normal", window_locked: bool = False
    ) -> str:
        """Generate a valid MainApplication even for an empty canvas.

        Keeping the same class/entry-point contract as non-empty designs is
        important because Run Preview instantiates MainApplication against a
        Toplevel parent. Standalone exports still use Tk() in the main guard.
        """
        if window_state == "Maximized" and "import platform" not in canvas_imports:
            canvas_imports = canvas_imports.rstrip() + "\nimport platform"

        # Custom class code is captured at method indentation (4 spaces);
        # restore it under MainApplication.
        class_methods = []
        if custom_class_code.strip():
            class_methods.extend(
                custom_class_code.rstrip("\n").splitlines()
            )

        body = [
            '"""Generated by Tkinter Visual Designer."""',
            "",
            canvas_imports,
            "",
        ]

        if custom_module_code.strip():
            body.extend([custom_module_code.rstrip("\n"), ""])

        body.extend([
            "class MainApplication:",
            "    def __init__(self, root):",
            "        self.root = root",
            f"        root.title({json.dumps(window_title)})",
            f"        root.geometry({json.dumps(f'{int(round(float(window_size[0])))}x{int(round(float(window_size[1])))}')})",
            f"        root.configure(bg={json.dumps(canvas_bg)})",
        ])

        window_state_lines = CodeGenerator._window_state_lines(
            window_state, "        "
        )
        body.extend(window_state_lines)
        body.extend([
            "",
            '        label = tk.Label(',
            f'            root, text="Add elements from the toolbox to begin!",',
            f'            font=("Segoe UI", 10), bg={json.dumps(canvas_bg)}',
            "        )",
            "        label.place(x=10, y=10, width=300, height=30)",
        ])

        if class_methods:
            body.append("")
            body.extend(class_methods)

        body.extend([
            "",
            "if __name__ == '__main__':",
            "    root = tk.Tk()",
            "    app = MainApplication(root)",
            "    root.mainloop()",
            "",
        ])
        return "\n".join(body)

