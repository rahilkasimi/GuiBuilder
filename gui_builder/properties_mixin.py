"""Property inspector and live property editing."""
from .dependencies import *
from .config import *
from .models import DesignElement
from .code_generator import CodeGenerator


def _yes_no(raw, default_yes: bool = True) -> str:
    """Normalize a property value that may be the current "Yes"/"No"
    convention or a legacy "1"/"0"/"true"/"false" one (saved by a project
    from before a field switched to Yes/No) into a valid combobox option.
    default_yes picks which side an unrecognized value falls on.
    """
    s = str(raw).strip().lower()
    if default_yes:
        return "No" if s in ("no", "0", "false") else "Yes"
    return "Yes" if s in ("yes", "1", "true") else "No"


def _coerce_font_value(value):
    """Parse a font value typed/stored as a Python literal string (e.g.
    "('Segoe UI', 10)") into an actual tuple, for storing on
    elem.props["font"]. Falls back to the raw string unchanged if it
    doesn't parse -- codegen's own "font" handling already tolerates a
    plain string there.
    """
    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, list):
            parsed = tuple(parsed)
        return parsed if isinstance(parsed, tuple) else value
    except Exception:
        return value


def _coerce_item_list(value):
    """Normalize legacy string representations and ordinary iterables into a
    clean list of item strings for Listbox/Combobox property editors."""
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value]
    if value is None:
        return []
    text = str(value).strip()
    if not text:
        return []
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, (list, tuple)):
            return [str(v) for v in parsed]
    except Exception:
        pass
    return [part.strip() for part in text.split(",") if part.strip()]


class PropertiesMixin:
    def _bind_widget_help(self, widget, help_text):
        """Bind Context Help hover text to a single Properties-pane widget.

        Uses a direct (non-accumulating) tk bind() rather than the
        add="+" pattern used for static UI chrome elsewhere in the app.
        Properties-pane rows are heavily reused/rebuilt as the selection
        changes -- the same tk.Entry/label instances are repeatedly
        repurposed for different fields -- so a plain bind() (which
        replaces any prior handler for that sequence on that widget)
        keeps exactly one, always-current handler per widget instead of
        letting handlers pile up call after call.
        """
        if widget is None:
            return
        widget.bind(
            "<Enter>",
            lambda e, w=widget, t=help_text: self._context_help_enter(w, t)
        )
        widget.bind(
            "<Leave>",
            lambda e, w=widget: self._context_help_leave(w)
        )

    def _apply_row_context_help(self, row, help_text):
        """Attach the same Context Help text to a property row's label and
        every control widget currently inside it (Entry/Combobox/buttons/
        color-pickers/nested frames), so hovering anywhere on the row --
        not just the label -- explains what the field does.

        Must be called AFTER the row's controls are built for the current
        field, since control_frame's children are destroyed and recreated
        whenever the property panel refreshes (new selection, new field
        assigned to this row slot, etc.).
        """
        if not help_text:
            return
        label = row.get("label")
        if label is not None:
            self._bind_widget_help(label, help_text)
        control_frame = row.get("control_frame")
        if control_frame is None:
            return
        stack = [control_frame]
        while stack:
            widget = stack.pop()
            self._bind_widget_help(widget, help_text)
            try:
                stack.extend(widget.winfo_children())
            except tk.TclError:
                pass

    def _group_ids(self):
        ids = []
        for elem in self.elements:
            raw = str(elem.props.get("group_id", "") or "").strip()
            if raw and raw not in ids:
                ids.append(raw)
        try:
            return sorted(ids, key=lambda v: int(v))
        except ValueError:
            return sorted(ids)

    def _group_options(self, include_create=False):
        options = ["(None)"] + [f"Group {gid}" for gid in self._group_ids()]
        if include_create:
            options.append("(Create New Group)")
        return options

    def _group_id_from_display(self, value):
        text = str(value or "").strip()
        if text == "(None)":
            return ""
        if text == "(Create New Group)":
            return None
        if text.lower().startswith("group "):
            return text[6:].strip()
        return text

    def _new_group_id(self):
        used = set()
        for elem in self.elements:
            raw = str(elem.props.get("group_id", "") or "").strip()
            if raw.isdigit():
                used.add(int(raw))
        gid = 1
        while gid in used:
            gid += 1
        return str(gid)

    def _group_elements(self, elements):
        elems = [e for e in elements if e in self.elements]
        if len(elems) < 2:
            return None
        gid = self._new_group_id()
        for elem in elems:
            elem.props["group_id"] = gid
        self._schedule_save()
        return gid

    def _ungroup_elements(self, elements):
        changed = False
        for elem in elements:
            if elem.props.pop("group_id", None) is not None:
                changed = True
        if changed:
            self._schedule_save()
        return changed

    def _group_members(self, elem):
        gid = str(elem.props.get("group_id", "") or "").strip()
        if not gid:
            return [elem]
        return [e for e in self.elements if str(e.props.get("group_id", "") or "").strip() == gid]

    def _show_properties_multi(self):
        """Show properties that can safely be edited across all selected elements.

        Every visible editor row owns its own StringVar.  The previous implementation
        accidentally reused the Group row's variable for Font/other rows, which could
        cascade a font tuple into the next property and ultimately generate invalid
        widget options (for example bg=("Segoe UI", 9)).
        """
        for row in self.prop_rows:
            row["frame"].pack_forget()
            row["visible"] = False
        self.prop_title_label.configure(
            text=f"[{len(self.selected_elems)} elements selected - Common Properties]"
        )

        common_fields = [
            ("group_id", "Group", "combobox"),
            ("font", "Font", "font"),
            ("fg", "Foreground", "color"),
            ("bg", "Background", "color"),
            ("width", "Width", "entry"),
            ("height", "Height", "entry"),
        ]

        def current_value(field_key):
            values = []
            for elem in self.selected_elems:
                if field_key == "width":
                    values.append(elem.canvas_w)
                elif field_key == "height":
                    values.append(elem.canvas_h)
                else:
                    values.append(elem.props.get(field_key, ""))
            return values[0] if values and all(v == values[0] for v in values) else ""

        row_index = 0
        for field_key, label, widget_type in common_fields:
            if row_index >= len(self.prop_rows):
                break
            row = self.prop_rows[row_index]
            row["label"].configure(text=label + " (All):")
            row["field_key"] = field_key
            self._clear_prop_row(row)

            initial = current_value(field_key)
            if field_key == "group_id":
                gid = str(initial or "").strip()
                display = f"Group {gid}" if gid else "(None)"
                var = tk.StringVar(value=display)
                row["var"] = var
                row["_trace_id"] = var.trace_add(
                    "write", lambda *args, r=row: self._on_live_multi_prop_change(r)
                )
                combo = ttk.Combobox(
                    row["control_frame"], textvariable=var,
                    values=self._group_options(include_create=True),
                    width=22, state="readonly"
                )
                combo.pack(fill=tk.X)
                row["_shape"] = (field_key, "group_combo")
                row["_combo_widget"] = combo

            elif widget_type in ("entry", "color"):
                var = tk.StringVar(value="" if initial is None else str(initial))
                row["var"] = var
                row["_trace_id"] = var.trace_add(
                    "write", lambda *args, r=row: self._on_live_multi_prop_change(r)
                )
                if widget_type == "entry":
                    tk.Entry(row["control_frame"], textvariable=var, width=24).pack(fill=tk.X)
                else:
                    frame = tk.Frame(row["control_frame"], bg=self._panel_bg)
                    frame.pack(fill=tk.X)
                    tk.Entry(frame, textvariable=var, width=20).pack(
                        side=tk.LEFT, fill=tk.X, expand=True
                    )
                    self._flat_button(
                        frame, "Pick", lambda v=var: self._pick_color(v)
                    ).pack(side=tk.RIGHT)
                    rgb_lbl = tk.Label(
                        row["control_frame"], text=self._rgb_label_text(var.get()),
                        font=("Segoe UI", 10), fg=self._muted_fg,
                        bg=self._panel_bg, anchor="w"
                    )
                    rgb_lbl.pack(fill=tk.X, pady=(1, 0))
                    var.trace_add(
                        "write", lambda *a, v=var, lbl=rgb_lbl: lbl.configure(
                            text=self._rgb_label_text(v.get())
                        )
                    )

            elif widget_type == "font":
                parsed = _coerce_font_value(str(initial)) if initial not in (None, "") else ("Segoe UI", 9)
                if not isinstance(parsed, tuple) or len(parsed) < 2:
                    parsed = ("Segoe UI", 9)
                family_var = tk.StringVar(value=str(parsed[0]))
                try:
                    size_value = int(float(parsed[1]))
                except (TypeError, ValueError):
                    size_value = 9
                size_var = tk.StringVar(value=str(size_value))
                var = tk.StringVar(value=str(parsed))
                row["var"] = var

                frame = tk.Frame(row["control_frame"], bg=self._panel_bg)
                frame.pack(fill=tk.X)

                def update_font(*args, target_var=var, f_var=family_var, s_var=size_var,
                                trace_row=row):
                    try:
                        size = int(s_var.get())
                    except (TypeError, ValueError):
                        size = 9
                    target_var.set(repr((f_var.get(), size)))

                family_trace = family_var.trace_add("write", update_font)
                size_trace = size_var.trace_add("write", update_font)
                var_trace = var.trace_add(
                    "write", lambda *args, r=row: self._on_live_multi_prop_change(r)
                )
                row["_trace_id"] = var_trace
                row["_font_aux_traces"] = [(family_var, family_trace), (size_var, size_trace)]
                try:
                    families = sorted(list(tkfont.families()))
                except Exception:
                    families = ["Arial", "Segoe UI"]
                ttk.Combobox(
                    frame, textvariable=family_var, values=families,
                    width=18, state="readonly"
                ).pack(side=tk.LEFT, padx=(0, 2))
                ttk.Combobox(
                    frame, textvariable=size_var,
                    values=[str(v) for v in [8, 9, 10, 11, 12, 14, 16, 18, 20, 24]],
                    width=5, state="readonly"
                ).pack(side=tk.LEFT)

            row["frame"].pack(fill=tk.X, pady=2)
            row["visible"] = True
            self._apply_row_context_help(
                row, self._context_help_text_for("property", field_key)
            )
            row_index += 1


    def _on_live_multi_prop_change(self, row):
        if len(self.selected_elems) <= 1 or not row.get("visible"):
            return
        field_key = row.get("field_key")
        var = row.get("var")
        if not field_key or var is None:
            return
        value = var.get()
        if field_key == "group_id":
            if value == "(Create New Group)":
                gid = self._group_elements(self.selected_elems)
                self._show_properties_multi()
                if gid:
                    self._update_status(f"Grouped {len(self.selected_elems)} elements as Group {gid}.")
                return
            gid = self._group_id_from_display(value) or ""
            for elem in self.selected_elems:
                elem.props["group_id"] = gid if gid else ""
                if not gid:
                    elem.props.pop("group_id", None)
                self.renderer.redraw_element(elem)
            self._update_code()
            self._schedule_save()
            return
        if not value:
            return

        for elem in self.selected_elems:
            if field_key in elem.props or field_key in ("width", "height"):
                if field_key == "width":
                    try:
                        elem.canvas_w = round(float(value), 2)
                    except (TypeError, ValueError):
                        pass
                elif field_key == "height":
                    try:
                        elem.canvas_h = round(float(value), 2)
                    except (TypeError, ValueError):
                        pass
                elif field_key == "font":
                    elem.props["font"] = _coerce_font_value(value)
                else:
                    elem.props[field_key] = value
                self.renderer.redraw_element(elem)

        self._update_code_for_moved_elements()
        self._update_code()
        self._schedule_save()

    def _clear_prop_row(self, row):
        """Destroy a property row's control widgets and reset its pooling
        state. Centralizes what used to be a repeated
        `for child in ...: child.destroy()` at every call site, and makes
        sure the fast-reuse path in _show_properties never mistakes a row
        that another function (multi-select / canvas properties) just
        rebuilt for one it can still safely pool.
        """
        for child in row["control_frame"].winfo_children():
            child.destroy()
        row["_shape"] = None
        row["_trace_id"] = None
        row["_combo_widget"] = None
        row["_font_aux_traces"] = []

    def _set_var_quiet(self, var: tk.StringVar, value: str, row: dict,
                       callback) -> None:
        """Update a StringVar's value without firing its live-edit trace.
        Used when reusing an existing property-field widget across a
        selection change: merely viewing a different element's properties
        should never mark the document modified or touch the generated
        code the way actually editing a field does, so the trace is
        detached for the programmatic set and reattached right after.
        """
        trace_id = row.get("_trace_id")
        if trace_id is not None:
            try:
                var.trace_remove("write", trace_id)
            except tk.TclError:
                pass
        var.set(value)
        row["_trace_id"] = var.trace_add("write", callback)

    def _scrollbar_target_options(self, scrollbar_elem: DesignElement):
        """Return (display_options, display_to_id) for a Scrollbar target.

        Only widgets that expose Tk's xview/yview API and are intentionally
        supported by the designer are listed. IDs are persisted instead of
        captions so duplicate/changed text cannot break the relationship.
        """
        options = ["(None)"]
        display_to_id = {"(None)": ""}
        for candidate in self.elements:
            if candidate is scrollbar_elem:
                continue
            if candidate.elem_type not in ("Text", "Canvas"):
                continue
            display = f"{candidate.elem_type} [id={candidate.elem_id}]"
            options.append(display)
            display_to_id[display] = str(candidate.elem_id)
        return options, display_to_id

    def _instrumentation_source_options(self, led_elem: DesignElement):
        """Return readable target options for an LED Indicator binding."""
        options = ["(None)"]
        display_to_id = {"(None)": ""}
        supported = {"PushButton", "RadioButton", "Radiobutton", "Checkbutton", "Button"}
        for candidate in self.elements:
            if candidate is led_elem or candidate.elem_type not in supported:
                continue
            display = f"{candidate.elem_type} [id={candidate.elem_id}]"
            options.append(display)
            display_to_id[display] = str(candidate.elem_id)
        return options, display_to_id

    def _instrumentation_source_display(self, target_value, display_to_id):
        target_id = str(target_value).strip()
        if not target_id:
            return "(None)"
        for display, elem_id in display_to_id.items():
            if str(elem_id) == target_id:
                return display
        return "(None)"

    def _scrollbar_target_display(self, target_value, display_to_id):
        """Resolve a persisted target ID to the readable dropdown label."""
        target_id = str(target_value).strip()
        if not target_id:
            return "(None)"
        for display, elem_id in display_to_id.items():
            if str(elem_id) == target_id:
                return display
        return "(None)"

    def _show_properties(self, elem: Optional[DesignElement]):
        for row in self.prop_rows:
            row["frame"].pack_forget()
            row["visible"] = False

        if elem is None:
            self.prop_title_label.configure(text="Canvas Settings")
            self.prop_context_var.set("Container: None")
            self._show_canvas_properties()
            return

        spec = ELEMENT_TYPES[elem.elem_type]
        self.prop_title_label.configure(
            text=f"{spec['display']} [id={elem.elem_id}]"
        )
        self.prop_context_var.set(self._parent_description(elem))
        # Legacy MeasurementDisplay projects may contain separate *_font_size
        # properties from older versions. Fold that size into the Font tuple
        # on first inspection so the Font picker remains the single source of
        # truth without exposing redundant fields.
        if elem.elem_type == "MeasurementDisplay":
            for font_key, size_key, fallback in (
                ("label_font", "label_font_size", 9),
                ("value_font", "value_font_size", 34),
                ("unit_font", "unit_font_size", 12),
                ("secondary_font", "secondary_font_size", 10),
            ):
                font_value = elem.props.get(font_key)
                size_value = elem.props.get(size_key)
                if size_value not in (None, "") and isinstance(font_value, (tuple, list)) and len(font_value) >= 2:
                    try:
                        size_int = max(1, int(float(size_value)))
                        family = font_value[0]
                        opts = tuple(font_value[2:])
                        elem.props[font_key] = (family, size_int, *opts)
                    except (TypeError, ValueError):
                        pass
        fields = list(PROPERTY_FIELDS.get(elem.elem_type, []))
        fields.append(("group_id", "Group", "combobox"))
        row_index = 0

        for fielddef in fields:
            if row_index >= len(self.prop_rows):
                break
            field_key, label, widget_type = fielddef[0], fielddef[1], fielddef[2]
            options = fielddef[3] if len(fielddef) > 3 else None
            row = self.prop_rows[row_index]
            row["label"].configure(text=label + ":")
            row["field_key"] = field_key

            if field_key == "canvas_w":
                value = elem.canvas_w
            elif field_key == "canvas_h":
                value = elem.canvas_h
            elif field_key == "visible":
                # Normalize a value read back from either the current
                # Yes/No property or a legacy 1/0 one (saved by a project
                # from before this switch) into a valid combobox option,
                # so an old project doesn't show a stale "1"/"0" sitting
                # outside the dropdown's own value set.
                value = _yes_no(elem.props.get("visible", "yes"))
            elif field_key == "showweeknumbers" and elem.elem_type == "Calendar":
                value = _yes_no(elem.props.get("showweeknumbers", "Yes"))
            elif field_key == "sorted" and elem.elem_type in ("Listbox", "Combobox"):
                value = _yes_no(elem.props.get("sorted", "No"), default_yes=False)
            elif field_key == "active_tab" and elem.elem_type == "Notebook":
                value = int(elem.props.get("active_tab", 0) or 0) + 1
                options = [str(i + 1) for i in range(
                    max(1, len(elem.props.get("tabs", [])))
                )]
            elif field_key == "target_widget" and elem.elem_type == "Scrollbar":
                options, target_map = self._scrollbar_target_options(elem)
                row["_target_map"] = target_map
                value = self._scrollbar_target_display(
                    elem.props.get("target_widget", ""), target_map
                )
            elif field_key == "group_id":
                options = self._group_options(include_create=True)
                value = "(None)" if not str(elem.props.get("group_id", "") or "").strip() else f"Group {elem.props.get('group_id')}"
            elif field_key == "source_widget" and elem.elem_type == "LEDIndicator":
                options, source_map = self._instrumentation_source_options(elem)
                row["_source_map"] = source_map
                value = self._instrumentation_source_display(
                    elem.props.get("source_widget", ""), source_map
                )
            else:
                value = elem.props.get(field_key, "")

            if field_key == "tabs" and elem.elem_type == "Notebook":
                value = ", ".join(
                    str(v) for v in (elem.props.get("tabs") or ["Tab 1"])
                )
            elif field_key in ("items", "values") and elem.elem_type in ("Listbox", "Combobox"):
                value = _coerce_item_list(elem.props.get(field_key, []))

            if field_key in ("canvas_w", "canvas_h"):
                display_val = f"{float(value):.2f}"
            else:
                display_val = "" if value is None else str(value)

            # Fields handled by dedicated composite widgets below (file
            # pickers, the notebook tab editor) are never pooled -- only
            # plain single-widget "entry"/"combobox" fields are, since
            # those are simple enough to reuse safely (see _set_var_quiet)
            # and make up the large majority of property fields overall.
            is_special = (
                    (elem.elem_type == "Table" and field_key == "file") or
                    (widget_type == "file_image" and field_key == "image_path") or
                    (field_key == "tabs" and elem.elem_type == "Notebook") or
                    (field_key in ("items", "values") and elem.elem_type in ("Listbox", "Combobox")) or
                    (field_key == "source_widget" and elem.elem_type == "LEDIndicator") or
                    (field_key == "target_widget" and elem.elem_type == "Scrollbar") or
                    field_key == "group_id"
            )
            poolable = (not is_special) and widget_type in ("entry", "combobox")
            shape = (field_key, widget_type) if poolable else None

            if poolable and row.get("_shape") == shape and row.get("var") is not None:
                # Fast path: this row already holds a live Entry/Combobox
                # for this exact field+widget shape (e.g. the previous
                # selection was another element of the same type). Reuse
                # it in place instead of destroying and rebuilding -- kept
                # as a cheap, purely defensive optimization for rapid
                # selection-switching, even though plain tk.Entry/
                # ttk.Combobox are themselves inexpensive to construct.
                var = row["var"]
                self._set_var_quiet(
                    var, display_val, row,
                    lambda *args, r=row: self._on_live_prop_change(r)
                )
                if widget_type == "combobox" and row.get("_combo_widget") is not None:
                    row["_combo_widget"].configure(
                        values=[str(o) for o in (options or [])]
                    )
                row["frame"].pack(fill=tk.X, pady=2)
                row["visible"] = True
                self._apply_row_context_help(
                    row, self._context_help_text_for("property", field_key)
                )
                row_index += 1
                continue

            self._clear_prop_row(row)
            var = tk.StringVar(value=display_val)

            if elem.elem_type == "Table" and field_key == "file":
                var.trace_add("write",
                              lambda *args, r=row: self._on_live_prop_change(
                                  r
                              )
                              )
                row["var"] = var
                file_frame = tk.Frame(row["control_frame"], bg=self._panel_bg)
                file_frame.pack(fill=tk.X)
                tk.Entry(file_frame, textvariable=var, width=20
                         ).pack(side=tk.LEFT, fill=tk.X,
                                expand=True
                                )
                self._flat_button(
                    file_frame, "…",
                    lambda v=var: self._browse_table_file(v)
                ).pack(side=tk.LEFT, padx=(3, 0))
                row["frame"].pack(fill=tk.X, pady=2)
                row["visible"] = True
                self._apply_row_context_help(
                    row, self._context_help_text_for("property", field_key)
                )
                row_index += 1
                continue

            if widget_type == "file_image" and field_key == "image_path":
                var.trace_add("write",
                              lambda *args, r=row: self._on_live_prop_change(
                                  r
                              )
                              )
                row["var"] = var
                img_frame = tk.Frame(row["control_frame"], bg=self._panel_bg)
                img_frame.pack(fill=tk.X)
                tk.Entry(img_frame, textvariable=var, width=20
                         ).pack(side=tk.LEFT, fill=tk.X,
                                expand=True
                                )
                self._flat_button(
                    img_frame, "…",
                    lambda v=var: self._browse_image_file(v)
                ).pack(side=tk.LEFT, padx=(3, 0))
                row["frame"].pack(fill=tk.X, pady=2)
                row["visible"] = True
                self._apply_row_context_help(
                    row, self._context_help_text_for("property", field_key)
                )
                row_index += 1
                continue

            if field_key == "group_id":
                var.trace_add("write", lambda *args, r=row: self._on_live_prop_change(r))
                row["var"] = var
                combo = ttk.Combobox(row["control_frame"], textvariable=var,
                                     values=[str(o) for o in options], width=22, state="readonly")
                combo.pack(fill=tk.X)
                row["_shape"] = (field_key, "group_combo")
                row["_trace_id"] = var.trace_info()[0][0] if var.trace_info() else None
                row["_combo_widget"] = combo
                helper_lbl = tk.Label(row["control_frame"], text="Use Group Selected from the right-click menu or another multi-selection.", font=("Segoe UI", 8), fg=self._muted_fg, bg=self._panel_bg, anchor="w")
                helper_lbl.pack(fill=tk.X, pady=(1, 0))
            elif field_key == "target_widget" and elem.elem_type == "Scrollbar":
                target_map = row.get("_target_map", {"(None)": ""})
                trace_id = var.trace_add(
                    "write",
                    lambda *args, r=row: self._on_live_prop_change(r)
                )
                row["var"] = var
                combo = ttk.Combobox(
                    row["control_frame"], textvariable=var,
                    values=[str(o) for o in (options or [])],
                    width=22, state="readonly"
                )
                combo.pack(fill=tk.X)
                row["_shape"] = (field_key, "target_widget")
                row["_trace_id"] = trace_id
                row["_combo_widget"] = combo
                row["_target_map"] = target_map
                helper_lbl = tk.Label(
                    row["control_frame"],
                    text="Text/Canvas only; use Orientation to choose x/y scrolling",
                    font=("Segoe UI", 8), fg=self._muted_fg,
                    bg=self._panel_bg, anchor="w"
                )
                helper_lbl.pack(fill=tk.X, pady=(1, 0))
            elif field_key == "source_widget" and elem.elem_type == "LEDIndicator":
                source_map = row.get("_source_map", {"(None)": ""})
                trace_id = var.trace_add(
                    "write", lambda *args, r=row: self._on_live_prop_change(r)
                )
                row["var"] = var
                combo = ttk.Combobox(
                    row["control_frame"], textvariable=var,
                    values=[str(o) for o in (options or [])],
                    width=22, state="readonly"
                )
                combo.pack(fill=tk.X)
                row["_shape"] = (field_key, "instrumentation_source")
                row["_trace_id"] = trace_id
                row["_combo_widget"] = combo
                row["_source_map"] = source_map
                helper_lbl = tk.Label(
                    row["control_frame"],
                    text="Mirror/toggle a button or selection state",
                    font=("Segoe UI", 8), fg=self._muted_fg,
                    bg=self._panel_bg, anchor="w"
                )
                helper_lbl.pack(fill=tk.X, pady=(1, 0))
            elif field_key in ("items", "values") and elem.elem_type in ("Listbox", "Combobox"):
                self._build_item_collection_editor(row, elem, field_key, _coerce_item_list(value))
            elif field_key == "tabs" and elem.elem_type == "Notebook":
                var.trace_add("write",
                              lambda *args, r=row: self._on_live_prop_change(
                                  r
                              )
                              )
                row["var"] = var
                tabs_frame = tk.Frame(row["control_frame"], bg=self._panel_bg)
                tabs_frame.pack(fill=tk.X)
                tk.Entry(tabs_frame, textvariable=var, width=20
                         ).pack(side=tk.LEFT, fill=tk.X,
                                expand=True
                                )
                self._flat_button(
                    tabs_frame, "+",
                    lambda e=elem: self._add_notebook_tab(e)
                ).pack(side=tk.LEFT, padx=(3, 0))
                self._flat_button(
                    tabs_frame, "−",
                    lambda e=elem: self._remove_notebook_tab(e)
                ).pack(side=tk.LEFT, padx=(2, 0))
            elif widget_type in ("entry", "combobox", "color"):
                trace_id = var.trace_add(
                    "write",
                    lambda *args, r=row: self._on_live_prop_change(r)
                )
                row["var"] = var
                if widget_type == "entry":
                    tk.Entry(row["control_frame"], textvariable=var,
                             width=24
                             ).pack(fill=tk.X)
                    row["_shape"] = (field_key, "entry")
                    row["_trace_id"] = trace_id
                elif widget_type == "combobox":
                    combo = ttk.Combobox(row["control_frame"], textvariable=var,
                                          values=[str(o) for o in
                                                  (options or [])],
                                          width=22, state="readonly"
                                          )
                    combo.pack(fill=tk.X)
                    row["_shape"] = (field_key, "combobox")
                    row["_trace_id"] = trace_id
                    row["_combo_widget"] = combo
                else:
                    cf = tk.Frame(row["control_frame"], bg=self._panel_bg)
                    cf.pack(fill=tk.X)
                    tk.Entry(cf, textvariable=var, width=20).pack(
                        side=tk.LEFT, fill=tk.X, expand=True
                    )
                    self._flat_button(
                        cf, "Pick",
                        lambda v=var: self._pick_color(v)
                    ).pack(side=tk.RIGHT, padx=(3, 0))
                    rgb_lbl = tk.Label(
                        row["control_frame"],
                        text=self._rgb_label_text(var.get()),
                        font=("Segoe UI", 10), fg=self._muted_fg,
                        bg=self._panel_bg, anchor="w"
                    )
                    rgb_lbl.pack(fill=tk.X, pady=(1, 0))
                    var.trace_add(
                        "write",
                        lambda *a, v=var, lbl=rgb_lbl: lbl.configure(
                            text=self._rgb_label_text(v.get())
                        )
                    )
                    # "color" fields aren't pooled (row["_shape"] stays
                    # None from _clear_prop_row), so this always rebuilds.
            elif widget_type == "text":
                text_w = tk.Text(row["control_frame"], height=4, width=22,
                                 font=("Segoe UI", 9), wrap=tk.WORD
                                 )
                text_w.pack(fill=tk.X)
                text_w.insert("1.0", display_val)
                text_w.bind("<KeyRelease>", lambda event, target_var=var,
                                                   tw=text_w: target_var.set(
                    tw.get("1.0", "end-1c")
                )
                            )
                var.trace_add("write",
                              lambda *args, r=row: self._on_live_prop_change(
                                  r
                              )
                              )
                row["var"] = var
            elif widget_type == "font":
                frame = tk.Frame(row["control_frame"], bg=self._panel_bg)
                frame.pack(fill=tk.X)
                family_var = tk.StringVar()
                size_var = tk.StringVar()
                if isinstance(value, (tuple, list)):
                    f_family = str(value[0]) if value else "Segoe UI"
                    f_size = str(value[1]) if len(value) > 1 else "9"
                else:
                    parsed = _coerce_font_value(str(value))
                    f_family = str(parsed[0]) if isinstance(parsed, (tuple, list)) and parsed else "Segoe UI"
                    f_size = str(parsed[1]) if isinstance(parsed, (tuple, list)) and len(parsed) > 1 else "9"
                family_var.set(f_family)
                size_var.set(f_size)

                def update_font(
                        *args, target_var=var, f_var=family_var,
                        s_var=size_var
                ):
                    target_var.set(f"('{f_var.get()}', {s_var.get()})")

                family_var.trace_add("write", update_font)
                size_var.trace_add("write", update_font)
                try:
                    families = sorted(list(tkfont.families()))
                except Exception:
                    families = ["Arial", "Segoe UI"]
                ttk.Combobox(frame, textvariable=family_var,
                             values=families, width=13, state="readonly"
                             ).pack(side=tk.LEFT, padx=(0, 2))
                ttk.Combobox(frame, textvariable=size_var,
                             values=[str(s) for s in
                                     [8, 9, 10, 11, 12, 14, 16, 18, 20,
                                      24, 28, 36, 48]], width=5,
                             state="readonly"
                             ).pack(side=tk.LEFT)
                var.trace_add("write",
                              lambda *args, r=row: self._on_live_prop_change(
                                  r
                              )
                              )
                row["var"] = var
            row["frame"].pack(fill=tk.X, pady=2)
            row["visible"] = True
            self._apply_row_context_help(
                row, self._context_help_text_for("property", field_key)
            )
            row_index += 1

    def _browse_table_file(self, var: tk.StringVar):
        path = filedialog.askopenfilename(
            filetypes=[("Excel/CSV Files", "*.xlsx *.xls *.csv"),
                       ("All Files", "*.*")]
        )
        if path:
            var.set(path)

    def _browse_image_file(self, var: tk.StringVar):
        path = filedialog.askopenfilename(
            filetypes=[("Image Files",
                        "*.png *.jpg *.jpeg *.gif *.bmp *.ico *.webp"),
                       ("All Files", "*.*")]
        )
        if not path:
            return
        try:
            rel_path = self._copy_image_to_resources(path)
        except Exception as e:
            messagebox.showerror("Image Error",
                                  f"Could not import image:\n{e}")
            return
        var.set(rel_path)

    def _copy_image_to_resources(self, src_path: str) -> str:
        """Copy an externally-picked image file into the builder's own
        resources/ folder and return its path relative to BASE_DIR.

        Both the design canvas (CanvasRenderer._load_thumbnail, which
        resolves a non-absolute image_path against BASE_DIR) and the
        exported script (which resolves it against its own
        os.path.dirname(__file__) -- see CodeGenerator._image_widget_line)
        need the file to live somewhere that travels with the project/export
        rather than at its original, possibly temporary or user-specific,
        location. Mirrors how Run Preview and Convert To EXE already copy
        resources/ alongside the generated script.
        """
        resources_dir = os.path.join(BASE_DIR, "resources")
        os.makedirs(resources_dir, exist_ok=True)
        filename = os.path.basename(src_path)
        dest_path = os.path.join(resources_dir, filename)
        if os.path.abspath(src_path) != os.path.abspath(dest_path):
            if os.path.exists(dest_path):
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(dest_path):
                    filename = f"{base}_{counter}{ext}"
                    dest_path = os.path.join(resources_dir, filename)
                    counter += 1
            shutil.copy2(src_path, dest_path)
        return os.path.join("resources", filename).replace(os.sep, "/")

    def _parent_description(self, elem: DesignElement) -> str:
        if elem.parent_id is None:
            return "Container: None (root)"
        parent = self._by_id.get(elem.parent_id)
        if parent is None:
            return f"Container: ID {elem.parent_id} (missing)"
        description = f"Container: {parent.elem_type} [id={parent.elem_id}]"
        if parent.elem_type == "Notebook":
            tabs = parent.props.get("tabs") or ["Tab 1"]
            idx = elem.parent_tab if elem.parent_tab is not None else 0
            idx = max(0, min(idx, len(tabs) - 1))
            description += f" — Tab {idx + 1}: {tabs[idx]}"
        return description

    def _add_notebook_tab(self, elem: DesignElement):
        tabs = list(elem.props.get("tabs") or ["Tab 1"])
        tabs.append(f"Tab {len(tabs) + 1}")
        elem.props["tabs"] = tabs
        self.renderer.redraw_element(elem)
        self._show_properties(elem)
        self._regenerate_designer_code()
        self._save_state()

    def _remove_notebook_tab(self, elem: DesignElement):
        tabs = list(elem.props.get("tabs") or ["Tab 1"])
        if len(tabs) <= 1:
            self._update_status("A Notebook must have at least one tab.")
            return
        tabs.pop()
        elem.props["tabs"] = tabs
        for child in self._children_by_parent.get(elem.elem_id, []):
            if child.parent_tab is not None and child.parent_tab >= len(tabs):
                child.parent_tab = len(tabs) - 1
        elem.props["active_tab"] = min(
            int(elem.props.get("active_tab", 0) or 0), len(tabs) - 1
        )
        self.renderer.redraw_element(elem)
        self._show_properties(elem)
        self._regenerate_designer_code()
        self._save_state()

    def _show_canvas_properties(self):
        row_index = 0

        row = self.prop_rows[row_index]
        row["label"].configure(text="Window Title:")
        self._clear_prop_row(row)
        self.title_var = tk.StringVar(value=self.window_title)
        title_entry = tk.Entry(row["control_frame"],
                               textvariable=self.title_var
                               )
        title_entry.pack(fill=tk.X)
        title_entry.bind("<KeyRelease>",
                         lambda e: self._window_title_changed()
                         )
        row["frame"].pack(fill=tk.X, pady=2)
        row["visible"] = True
        self._apply_row_context_help(
            row, self._context_help_text_for("property", "window_title")
        )
        row_index += 1

        row = self.prop_rows[row_index]
        row["label"].configure(text="Canvas Width:")
        self._clear_prop_row(row)
        var_w = tk.StringVar(value=f"{float(self.CANVAS_W):.2f}")
        tk.Entry(row["control_frame"], textvariable=var_w).pack(
            fill=tk.X
        )
        var_w.trace_add("write",
                        lambda *a: self._apply_canvas_size_from_props(var_w,
                                                                      None,
                                                                      None
                                                                      )
                        )
        row["frame"].pack(fill=tk.X, pady=2)
        row["visible"] = True
        self._apply_row_context_help(
            row, self._context_help_text_for("property", "canvas_width")
        )
        row_index += 1

        row = self.prop_rows[row_index]
        row["label"].configure(text="Canvas Height:")
        self._clear_prop_row(row)
        var_h = tk.StringVar(value=f"{float(self.CANVAS_H):.2f}")
        tk.Entry(row["control_frame"], textvariable=var_h).pack(
            fill=tk.X
        )
        var_h.trace_add("write",
                        lambda *a: self._apply_canvas_size_from_props(None,
                                                                      var_h,
                                                                      None
                                                                      )
                        )
        row["frame"].pack(fill=tk.X, pady=2)
        row["visible"] = True
        self._apply_row_context_help(
            row, self._context_help_text_for("property", "canvas_height")
        )
        row_index += 1

        row = self.prop_rows[row_index]
        row["label"].configure(text="Background:")
        self._clear_prop_row(row)
        var_bg = tk.StringVar(value=self.CANVAS_BG)
        frame_bg = tk.Frame(row["control_frame"], bg=self._panel_bg)
        frame_bg.pack(fill=tk.X)
        tk.Entry(frame_bg, textvariable=var_bg, width=16).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        self._flat_button(
            frame_bg, "Pick", lambda v=var_bg: self._pick_color(v)
        ).pack(side=tk.RIGHT, padx=(4, 0))
        rgb_lbl_bg = tk.Label(
            row["control_frame"], text=self._rgb_label_text(var_bg.get()),
            font=("Segoe UI", 10), fg=self._muted_fg, bg=self._panel_bg,
            anchor="w"
        )
        rgb_lbl_bg.pack(fill=tk.X, pady=(1, 0))
        var_bg.trace_add(
            "write",
            lambda *a, v=var_bg, lbl=rgb_lbl_bg: lbl.configure(
                text=self._rgb_label_text(v.get())
            )
        )
        var_bg.trace_add("write",
                         lambda *a: self._apply_canvas_size_from_props(None,
                                                                       None,
                                                                       var_bg
                                                                       )
                         )
        row["frame"].pack(fill=tk.X, pady=2)
        row["visible"] = True
        self._apply_row_context_help(
            row, self._context_help_text_for("property", "canvas_background")
        )
        row_index += 1

        row = self.prop_rows[row_index]
        row["label"].configure(text="Background Image:")
        self._clear_prop_row(row)
        var_img=tk.StringVar(value=getattr(self,"CANVAS_BG_IMAGE",""))
        f=tk.Frame(row["control_frame"],bg=self._panel_bg); f.pack(fill=tk.X)
        tk.Entry(f,textvariable=var_img,width=16).pack(side=tk.LEFT,fill=tk.X,expand=True)
        self._flat_button(f,"…",lambda v=var_img:self._browse_image_file(v)).pack(side=tk.LEFT,padx=(3,0))
        var_img.trace_add("write",lambda *a:self._apply_canvas_image_props(var_img,None,None))
        row["frame"].pack(fill=tk.X,pady=2); row["visible"]=True
        self._apply_row_context_help(row, self._context_help_text_for("property", "canvas_bg_image"))
        row_index+=1

        row=self.prop_rows[row_index]; row["label"].configure(text="Image Mode:"); self._clear_prop_row(row)
        var_mode=tk.StringVar(value=getattr(self,"CANVAS_BG_IMAGE_MODE","Fit"))
        ttk.Combobox(row["control_frame"],textvariable=var_mode,values=["Stretch","Fill","Fit","Center","Tile","None"],state="readonly").pack(fill=tk.X)
        var_mode.trace_add("write",lambda *a:self._apply_canvas_image_props(None,var_mode,None))
        row["frame"].pack(fill=tk.X,pady=2); row["visible"]=True
        self._apply_row_context_help(row, self._context_help_text_for("property", "canvas_bg_image_mode"))
        row_index+=1

        row=self.prop_rows[row_index]; row["label"].configure(text="Image Alignment:"); self._clear_prop_row(row)
        var_anchor=tk.StringVar(value=getattr(self,"CANVAS_BG_IMAGE_ANCHOR","Center"))
        ttk.Combobox(row["control_frame"],textvariable=var_anchor,values=["Top-Left","Top","Top-Right","Left","Center","Right","Bottom-Left","Bottom","Bottom-Right"],state="readonly").pack(fill=tk.X)
        var_anchor.trace_add("write",lambda *a:self._apply_canvas_image_props(None,None,var_anchor))
        row["frame"].pack(fill=tk.X,pady=2); row["visible"]=True
        self._apply_row_context_help(row, self._context_help_text_for("property", "canvas_bg_image_anchor"))
        row_index+=1

        row=self.prop_rows[row_index]; row["label"].configure(text="Window State:")
        self._clear_prop_row(row)
        var_state = tk.StringVar(
            value=getattr(self, "WINDOW_STATE", "Normal")
            )
        ttk.Combobox(row["control_frame"], textvariable=var_state,
                     values=["Normal", "Maximized", "Minimized", "Centered"],
                     width=22, state="readonly"
                     ).pack(fill=tk.X)
        var_state.trace_add(
            "write",
            lambda *a, v=var_state: self._apply_window_state_from_props(v)
            )
        row["frame"].pack(fill=tk.X, pady=2)
        row["visible"] = True
        self._apply_row_context_help(
            row, self._context_help_text_for("property", "window_state")
        )
        row_index += 1

        row = self.prop_rows[row_index]
        row["label"].configure(text="Locked:")
        self._clear_prop_row(row)
        var_locked = tk.StringVar(
            value="Yes" if getattr(self, "WINDOW_LOCKED", False) else "No"
        )
        ttk.Combobox(row["control_frame"], textvariable=var_locked,
                     values=["Yes", "No"], width=22, state="readonly"
                     ).pack(fill=tk.X)
        var_locked.trace_add(
            "write",
            lambda *a, v=var_locked: self._apply_window_lock_from_props(v)
        )
        row["frame"].pack(fill=tk.X, pady=2)
        row["visible"] = True
        self._apply_row_context_help(
            row, self._context_help_text_for("property", "window_locked")
        )
        row_index += 1

    def _apply_window_state_from_props(self, var_state):
        self.WINDOW_STATE = var_state.get()
        # Unlike the old single-file model, there's no risk calculus here
        # anymore -- regenerating the designer module wholesale is always
        # safe and cheap, window-state block or not.
        self._regenerate_designer_code()
        self._schedule_save()

    def _apply_window_lock_from_props(self, var_locked):
        value = str(var_locked.get()).strip().lower()
        self.WINDOW_LOCKED = value in ("yes", "true", "1", "on")
        self._regenerate_designer_code()
        self._schedule_save()

    def _apply_canvas_image_props(self,var_img,var_mode,var_anchor):
        if var_img is not None: self.CANVAS_BG_IMAGE=var_img.get()
        if var_mode is not None: self.CANVAS_BG_IMAGE_MODE=var_mode.get()
        if var_anchor is not None: self.CANVAS_BG_IMAGE_ANCHOR=var_anchor.get()
        self.renderer.draw_canvas_background(self.CANVAS_BG_IMAGE,self.CANVAS_BG_IMAGE_MODE,self.CANVAS_BG_IMAGE_ANCHOR,self.CANVAS_W,self.CANVAS_H)
        self._regenerate_designer_code(); self._schedule_save()

    def _apply_canvas_size_from_props(self, var_w, var_h, var_bg):
        try:
            if var_w:
                self.CANVAS_W = round(float(var_w.get()), 2)
            if var_h:
                self.CANVAS_H = round(float(var_h.get()), 2)
            if var_bg:
                self.CANVAS_BG = var_bg.get()
            self.canvas.config(width=self.CANVAS_W, height=self.CANVAS_H,
                               bg=self._get_theme_colors()["panel_bg"],
                               scrollregion=(0, 0, self.CANVAS_W,
                                             self.CANVAS_H)
                               )
            self.renderer.draw_canvas_surface(self.CANVAS_W, self.CANVAS_H, self.CANVAS_BG)
            self.renderer.draw_canvas_background(self.CANVAS_BG_IMAGE,self.CANVAS_BG_IMAGE_MODE,self.CANVAS_BG_IMAGE_ANCHOR,self.CANVAS_W,self.CANVAS_H)
            if self._resnap_status_bars():
                self._redraw_all_elements()
            # No more geometry/bg regex patching -- a full designer-module
            # regenerate is already the cheap, safe path for every change,
            # canvas size included.
            self._regenerate_designer_code()
            self._schedule_save()
        except ValueError:
            pass

    def _build_item_collection_editor(self, row, elem: DesignElement, field_key: str, items: List[str]):
        """Build a dedicated dropdown editor for Listbox/Combobox collections.

        The combobox shows one item at a time rather than Python's list
        representation. Users can type a new value and press Add, or select an
        existing value and press Remove.
        """
        var = tk.StringVar(value="")
        row["var"] = var
        row["_shape"] = (field_key, "item_editor")
        row["_trace_id"] = None
        combo_frame = tk.Frame(row["control_frame"], bg=self._panel_bg)
        combo_frame.pack(fill=tk.X)
        combo = ttk.Combobox(
            combo_frame, textvariable=var, values=[str(v) for v in items],
            width=18, state="normal"
        )
        combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        row["_combo_widget"] = combo

        def refresh_and_commit(new_items):
            normalized = [str(v) for v in new_items if str(v).strip()]
            elem.props[field_key] = normalized
            combo.configure(values=normalized)
            current = var.get().strip()
            if current and current not in normalized:
                var.set("")
            self.renderer.redraw_element(elem)
            self._update_code_for_element(elem)
            self._update_code()
            self._schedule_save()

        def add_item():
            new_item = var.get().strip()
            if not new_item:
                self._update_status("Enter an item before adding it.")
                return
            current_items = _coerce_item_list(elem.props.get(field_key, []))
            if new_item not in current_items:
                current_items.append(new_item)
                refresh_and_commit(current_items)
            else:
                combo.set(new_item)

        def remove_item():
            selected = var.get().strip()
            if not selected:
                return
            current_items = _coerce_item_list(elem.props.get(field_key, []))
            new_items = [item for item in current_items if item != selected]
            if len(new_items) != len(current_items):
                refresh_and_commit(new_items)
                combo.set("")

        self._flat_button(combo_frame, "+", add_item).pack(side=tk.LEFT, padx=(3, 0))
        self._flat_button(combo_frame, "−", remove_item).pack(side=tk.LEFT, padx=(2, 0))
        helper_lbl = tk.Label(
            row["control_frame"], text="Select an item or type a new value",
            font=("Segoe UI", 8), fg=self._muted_fg, bg=self._panel_bg, anchor="w"
        )
        helper_lbl.pack(fill=tk.X, pady=(1, 0))

    def _on_live_prop_change(self, row):
        if not self.selected_elems or len(self.selected_elems
                                          ) > 1 or not row.get("visible"):
            return
        elem = self.selected_elems[0]
        field_key = row.get("field_key")
        var = row.get("var")
        if not field_key or var is None:
            return

        value = var.get()

        if field_key == "group_id":
            if value == "(Create New Group)":
                gid = self._new_group_id()
                elem.props["group_id"] = gid
                self._show_properties(elem)
            else:
                gid = self._group_id_from_display(value) or ""
                if gid:
                    elem.props["group_id"] = gid
                else:
                    elem.props.pop("group_id", None)
            self.renderer.redraw_element(elem)
            self._update_code()
            self._schedule_save()
            return
        if field_key == "target_widget" and elem.elem_type == "Scrollbar":
            target_map = row.get("_target_map", {})
            elem.props["target_widget"] = str(target_map.get(value, ""))
        elif field_key == "source_widget" and elem.elem_type == "LEDIndicator":
            source_map = row.get("_source_map", {})
            elem.props["source_widget"] = str(source_map.get(value, ""))
        elif field_key == "orient" and elem.elem_type in ("Scale", "Separator",
                                                        "Progressbar",
                                                        "Scrollbar"):
            if value == "vertical" and elem.canvas_w > elem.canvas_h:
                elem.canvas_w, elem.canvas_h = elem.canvas_h, elem.canvas_w
            elif value == "horizontal" and elem.canvas_h > elem.canvas_w:
                elem.canvas_w, elem.canvas_h = elem.canvas_h, elem.canvas_w

        if field_key == "canvas_w":
            try:
                elem.canvas_w = round(float(value), 2)
            except (TypeError, ValueError):
                pass
        elif field_key == "canvas_h":
            try:
                elem.canvas_h = round(float(value), 2)
            except (TypeError, ValueError):
                pass
        elif field_key == "font" or (str(field_key).endswith("_font") and elem.elem_type == "MeasurementDisplay"):
            # MeasurementDisplay uses four dedicated font properties.  They
            # must follow the same tuple parsing path as the generic font
            # property; otherwise the value is stored as a string and the
            # renderer falls back to its default font.
            elem.props[field_key] = _coerce_font_value(value)
        elif field_key in ("values", "items"):
            elem.props[field_key] = _coerce_item_list(value)
        elif field_key in ("target_widget", "source_widget") and elem.elem_type in ("Scrollbar", "LEDIndicator"):
            # Already normalized above through the field-specific ID map.
            pass
        elif elem.elem_type == "Notebook" and field_key == "tabs":
            tabs = [v.strip() for v in value.split(",") if v.strip()] or [
                "Tab 1"]
            elem.props["tabs"] = tabs
            elem.props["active_tab"] = min(
                int(elem.props.get("active_tab", 0) or 0), len(tabs) - 1
            )
            for child in self._children_by_parent.get(elem.elem_id, []):
                if child.parent_tab is not None and child.parent_tab >= len(tabs):
                    child.parent_tab = len(tabs) - 1
            # Refresh just the active_tab dropdown's option count in place,
            # rather than calling _show_properties(elem) here. A full
            # property-panel rebuild destroys and recreates every row --
            # including the very entry field the user is actively typing
            # into -- which breaks keyboard focus after every single
            # keystroke and makes renaming a tab effectively impossible
            # (only the first character typed would ever register).
            for r in self.prop_rows:
                if r.get("field_key") == "active_tab" and r.get("_combo_widget") is not None:
                    r["_combo_widget"].configure(
                        values=[str(i + 1) for i in range(len(tabs))]
                    )
                    break
        elif elem.elem_type == "Notebook" and field_key == "active_tab":
            try:
                idx = max(0, int(value) - 1)
            except ValueError:
                idx = 0
            tabs = elem.props.get("tabs") or ["Tab 1"]
            elem.props["active_tab"] = min(idx, len(tabs) - 1)
            self._show_properties(elem)
        else:
            try:
                elem.props[field_key] = int(value)
            except ValueError:
                try:
                    elem.props[field_key] = float(value)
                except ValueError:
                    elem.props[field_key] = value

        self.renderer.redraw_element(elem)
        self._update_code_for_element(elem)
        self._update_code()

        self._schedule_save()

    def _update_code_for_element(self, elem: DesignElement):
        """Regenerate the designer module after a property edit to elem.

        This used to be ~100 lines: locate the element's block by regex,
        bail to a full regenerate for instrumentation types / Scrollbar
        targets / multi-line widgets (Image) / anything the pattern match
        didn't find cleanly, and even the "safe" fallback closure had its
        own gap -- it restored handler/class code from already-synced
        model state rather than the live code editor buffer, so an
        in-progress edit sitting in an open editor could be silently lost
        if it fired mid-edit. None of that exists anymore: regenerating
        the whole designer module is unconditionally safe (nothing
        user-written can ever be in it), and user code lives only in
        self.user_code, which this never touches at all.
        """
        self._regenerate_designer_code()

    def _pick_color(self, var: tk.StringVar):
        color = colorchooser.askcolor(initialcolor=var.get() or "#ffffff",
                                      title="Select Color"
                                      )
        if color[1]:
            var.set(color[1])

    def _rgb_label_text(self, hex_color: str) -> str:
        """RGB text for a "#RRGGBB" color, for the small label shown next
        to each color field's hex entry. The color picker dialog itself
        shows RGB sliders (a native OS control we can't restyle), but the
        field stores/generates hex -- showing both side by side means
        neither value looks unexplained.
        """
        hc = (hex_color or "").strip()
        if len(hc) == 7 and hc.startswith("#"):
            try:
                r, g, b = int(hc[1:3], 16), int(hc[3:5], 16), int(hc[5:7], 16)
                return f"RGB {r}, {g}, {b}"
            except ValueError:
                pass
        return ""
