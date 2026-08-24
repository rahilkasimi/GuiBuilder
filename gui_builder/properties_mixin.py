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
    def _show_properties_multi(self):
        for row in self.prop_rows:
            row["frame"].pack_forget()
            row["visible"] = False
        self.prop_title_label.configure(
            text=f"[{len(self.selected_elems)} elements selected - Common Properties]"
        )

        common_fields = [
            ("font", "Font", "font"),
            ("fg", "Foreground", "color"),
            ("bg", "Background", "color"),
            ("width", "Width", "entry"),
            ("height", "Height", "entry"),
        ]

        row_index = 0
        for field_key, label, widget_type in common_fields:
            if row_index >= len(self.prop_rows):
                break
            row = self.prop_rows[row_index]
            row["label"].configure(text=label + " (All):")
            row["field_key"] = field_key

            self._clear_prop_row(row)

            var = tk.StringVar(value="")

            if widget_type in ("entry", "color"):
                var.trace_add("write", lambda *args,
                                              r=row: self._on_live_multi_prop_change(
                    r
                )
                              )
                row["var"] = var

                if widget_type == "entry":
                    tk.Entry(row["control_frame"], textvariable=var,
                             width=24
                             ).pack(fill=tk.X)
                elif widget_type == "color":
                    frame = tk.Frame(row["control_frame"], bg=self._panel_bg)
                    frame.pack(fill=tk.X)
                    tk.Entry(frame, textvariable=var, width=20).pack(
                        side=tk.LEFT, fill=tk.X, expand=True
                    )
                    self._flat_button(
                        frame, "Pick",
                        lambda v=var: self._pick_color(v)
                    ).pack(side=tk.RIGHT)
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

            elif widget_type == "font":
                frame = tk.Frame(row["control_frame"], bg=self._panel_bg)
                frame.pack(fill=tk.X)
                family_var = tk.StringVar(value="Segoe UI")
                size_var = tk.StringVar(value="9")

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
                             values=families, width=18, state="readonly"
                             ).pack(side=tk.LEFT, padx=(0, 2))
                ttk.Combobox(frame, textvariable=size_var,
                             values=[str(s) for s in
                                     [8, 9, 10, 11, 12, 14, 16, 18, 20,
                                      24]], width=5, state="readonly"
                             ).pack(side=tk.LEFT)

                var.trace_add("write", lambda *args,
                                              r=row: self._on_live_multi_prop_change(
                    r
                )
                              )
                row["var"] = var

            row["frame"].pack(fill=tk.X, pady=2)
            row["visible"] = True
            row_index += 1

    def _on_live_multi_prop_change(self, row):
        if len(self.selected_elems) <= 1 or not row.get("visible"):
            return
        field_key = row.get("field_key")
        var = row.get("var")
        if not field_key or var is None:
            return
        value = var.get()
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
        fields = PROPERTY_FIELDS.get(elem.elem_type, [])
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
                    (elem.elem_type == "Image" and field_key == "image_path") or
                    (field_key == "tabs" and elem.elem_type == "Notebook") or
                    (field_key in ("items", "values") and elem.elem_type in ("Listbox", "Combobox"))
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
                row_index += 1
                continue

            if elem.elem_type == "Image" and field_key == "image_path":
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
                row_index += 1
                continue

            if field_key in ("items", "values") and elem.elem_type in ("Listbox", "Combobox"):
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
        self._invalidate_full_code()
        self.renderer.redraw_element(elem)
        self._show_properties(elem)
        self._update_code()
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
        self._invalidate_full_code()
        self.renderer.redraw_element(elem)
        self._show_properties(elem)
        self._update_code()
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
        row_index += 1

        row = self.prop_rows[row_index]
        row["label"].configure(text="Window State:")
        self._clear_prop_row(row)
        var_state = tk.StringVar(
            value=getattr(self, "WINDOW_STATE", "Normal")
            )
        ttk.Combobox(row["control_frame"], textvariable=var_state,
                     values=["Normal", "Maximized", "Minimized"],
                     width=22, state="readonly"
                     ).pack(fill=tk.X)
        var_state.trace_add(
            "write",
            lambda *a, v=var_state: self._apply_window_state_from_props(v)
            )
        row["frame"].pack(fill=tk.X, pady=2)
        row["visible"] = True
        row_index += 1

    def _apply_window_state_from_props(self, var_state):
        self.WINDOW_STATE = var_state.get()
        # Unlike width/height/background, the window-state block is a
        # multi-line conditional (see CodeGenerator._window_state_lines)
        # that may not exist in the script yet, or may need switching
        # between three different shapes -- regex-patching it in place
        # in an already-generated self.full_code (the way
        # _update_code_for_canvas_change patches geometry/bg) isn't worth
        # the risk of corrupting the script. A full regenerate is cheap
        # and this field changes rarely, so just do that instead.
        self._invalidate_full_code()
        self._update_code()
        self._schedule_save()

    def _apply_canvas_size_from_props(self, var_w, var_h, var_bg):
        try:
            if var_w:
                self.CANVAS_W = round(float(var_w.get()), 2)
            if var_h:
                self.CANVAS_H = round(float(var_h.get()), 2)
            if var_bg:
                self.CANVAS_BG = var_bg.get()
            self.canvas.config(width=self.CANVAS_W, height=self.CANVAS_H,
                               bg=self.CANVAS_BG,
                               scrollregion=(0, 0, self.CANVAS_W,
                                             self.CANVAS_H)
                               )
            self.renderer.draw_grid(self.CANVAS_W, self.CANVAS_H)
            self._update_code_for_canvas_change()
            self._update_code()
            self._schedule_save()
        except ValueError:
            pass

    def _update_code_for_canvas_change(self):
        if self.full_code:
            self.full_code = re.sub(
                r'root\.geometry\([^\)]+\)',
                f'root.geometry("{self.CANVAS_W}x{self.CANVAS_H}")',
                self.full_code
            )
            self.full_code = re.sub(
                r'root\.configure\(bg=[^\)]+\)',
                f'root.configure(bg="{self.CANVAS_BG}")',
                self.full_code
            )
        else:
            self._invalidate_full_code()
            self._update_code()

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

        if field_key == "orient" and elem.elem_type in ("Scale", "Separator",
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
        elif field_key == "font":
            elem.props["font"] = _coerce_font_value(value)
        elif field_key in ("values", "items"):
            elem.props[field_key] = _coerce_item_list(value)
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
        def _safe_invalidate_and_update():
            # Preserve existing custom handlers and class codes before clearing project state
            existing_handlers = {e.elem_id: getattr(e, 'handler_code', 'pass') for e in self.elements}
            existing_class_code = getattr(self, 'custom_class_code', '')

            self._invalidate_full_code()

            # Restore them immediately so the generator applies them instead of stubs
            for e in self.elements:
                if e.elem_id in existing_handlers:
                    e.handler_code = existing_handlers[e.elem_id]
            if existing_class_code:
                self.custom_class_code = existing_class_code

            self._update_code()

        if not self.full_code:
            _safe_invalidate_and_update()
            return

        widget_line, place_line, extra_lines = CodeGenerator.generate_element_lines(
            elem, self.elements
        )

        if elem.elem_type == "Image":
            self._ensure_header_imports(
                ["import os", "from PIL import Image, ImageTk"]
                )
        elif elem.elem_type == "Calendar":
            self._ensure_header_imports(
                ["from tkcalendar import Calendar", "from datetime import date"]
                )

        # Some widget types (an Image with a resolved image_path, which
        # wraps Image.open()/ImageTk.PhotoImage() in a try/except) generate
        # a multi-line widget_line where the actual "self._elem_N = ..."
        # assignment is nested inside the try/except at a deeper indent
        # than a single-line splice can safely locate and replace. Trying
        # to regex-match it here would either silently fail every time
        # (forcing a needless full regenerate on every edit) or, worse,
        # match a partial/unexpected line and splice a fresh block into
        # the middle of a stale one -- corrupting whatever element's code
        # follows it (e.g. a button's handler method ends up looking like
        # it reverted to "pass"). Route these straight to a clean full
        # regenerate instead of attempting the line-level patch.
        if "\n" in widget_line:
            _safe_invalidate_and_update()
            return

        widget_pattern = rf'        self\._elem_{elem.elem_id} = .+'
        place_pattern = rf'        self\._elem_{elem.elem_id}\.place\(.+'

        lines = self.full_code.splitlines(keepends=True)
        new_lines = []
        widget_found = False
        place_found = False
        i = 0
        while i < len(lines):
            line = lines[i]
            if not widget_found and re.match(widget_pattern, line):
                widget_found = True
                block_lines = []
                block_start = i
                while i < len(lines):
                    current = lines[i]
                    if re.match(place_pattern, current):
                        block_lines.append(current)
                        i += 1
                        place_found = True
                        break
                    if re.match(r'        self\._elem_\d+ = ', current
                                ) and current != lines[block_start]:
                        break
                    block_lines.append(current)
                    i += 1
                new_block = [widget_line]
                if extra_lines:
                    new_block.extend(extra_lines)
                new_block.append(place_line)
                new_lines.extend([l + '\n' for l in new_block])
                continue
            else:
                new_lines.append(line)
                i += 1

        if not widget_found or not place_found:
            _safe_invalidate_and_update()
        else:
            self.full_code = ''.join(new_lines)
            self._current_code = self.full_code

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
