"""UI construction, toolbars, toolbox, tooltip and view controls."""
from .dependencies import *
from .config import ELEMENT_TYPES, TOOLBOX_NORMAL_COLOR, TOOLBOX_HOVER_COLOR, TOOLBOX_ACTIVE_COLOR
from .renderer import CanvasRenderer


class _VScrollFrame(tk.Frame):
    """A vertically-scrollable container: pack/grid child widgets into
    the .inner frame (not the _VScrollFrame instance itself) -- this
    class is just the fixed-size viewport + scrollbar wrapper around it.

    Plain tkinter has no built-in scrollable-frame widget (unlike
    CustomTkinter's CTkScrollableFrame) -- this is the standard
    Canvas + inner Frame + Scrollbar recipe for building one. The
    mouse wheel is only bound while the pointer is actually over this
    widget (bind_all on Enter, unbind_all on Leave), so scrolling one
    scrollable panel never steals wheel events meant for another.
    """

    def __init__(self, parent, bg=None, **kwargs):
        super().__init__(parent, bg=bg, **kwargs)
        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self._vsb = ttk.Scrollbar(
            self, orient="vertical", command=self._canvas.yview
            )
        self.inner = tk.Frame(self._canvas, bg=bg)
        self._canvas.configure(yscrollcommand=self._vsb.set)

        self._vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._inner_window = self._canvas.create_window(
            (0, 0), window=self.inner, anchor="nw"
            )

        self.inner.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind("<Enter>", lambda e: self._bind_wheel())
        self._canvas.bind("<Leave>", lambda e: self._unbind_wheel())

    def _on_inner_configure(self, event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._inner_window, width=event.width)

    def _bind_wheel(self):
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind_all("<Button-4>", self._on_mousewheel)
        self._canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_wheel(self):
        self._canvas.unbind_all("<MouseWheel>")
        self._canvas.unbind_all("<Button-4>")
        self._canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        if getattr(event, "num", None) == 4:
            self._canvas.yview_scroll(-1, "units")
        elif getattr(event, "num", None) == 5:
            self._canvas.yview_scroll(1, "units")
        else:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class UIMixin:
        def _setup_styles(self):
            style = ttk.Style()
            default_font = tkfont.nametofont("TkDefaultFont")
            default_font.configure(family="Segoe UI", size=9)
            self.root.option_add("*Font", default_font)

            # Shared palette for the builder's own chrome (plain tkinter/
            # ttk widgets have no theme-wide accent color the way
            # CustomTkinter's set_default_color_theme("blue") gave every
            # widget for free, so buttons/labels below apply these
            # explicitly instead).
            self._panel_bg = "#F5F5F5"
            self._panel_fg = "#212121"
            self._muted_fg = "#757575"
            self._accent = "#1976D2"
            self._accent_fg = "#FFFFFF"
            bg = self._panel_bg
            fg = self._panel_fg
            select_bg = self._accent

            # The native ttk themes ("vista"/"xpnative" on Windows, "aqua" on
            # macOS) ignore most style.configure() calls for widgets like
            # Scrollbar and PanedWindow, which is why those widgets used to look
            # visually disconnected from CustomTkinter's flat design elsewhere in
            # the app (native 3D sash/scrollbar chrome next to flat CTk buttons).
            # "clam" is a theme-able ttk theme that actually honors the color/
            # relief overrides below, so switch to it before configuring styles.
            try:
                style.theme_use("clam")
            except tk.TclError:
                pass  # fall back to whatever default theme is available

            style.configure("Treeview", background="white", foreground=fg,
                             fieldbackground="white", rowheight=24
                             )
            style.map("Treeview", background=[('selected', select_bg)])
            style.configure("Treeview.Heading", background=bg, foreground=fg,
                             relief="flat", borderwidth=0
                             )

            # Flat look for the ttk widgets used in the builder's own chrome
            # (main pane splitters, canvas/code-editor scrollbars, and the
            # dropdown fields in the property inspector).
            style.configure("TPanedWindow", background=bg)
            style.configure("Sash", sashthickness=6, gripcount=0,
                             background=bg, lightcolor=bg, darkcolor="#D0D0D0"
                             )
            for orient in ("Vertical", "Horizontal"):
                name = f"{orient}.TScrollbar"
                style.configure(name, background=bg, troughcolor="#EDEDED",
                                 bordercolor=bg, arrowcolor=fg,
                                 relief="flat", borderwidth=0
                                 )
                style.map(name,
                          background=[("active", "#D5D5D5"), ("pressed", "#C0C0C0")]
                          )
            style.configure("TCombobox", fieldbackground="white",
                             background=bg, foreground=fg
                             )
            style.configure("TButton", background=bg, foreground=fg)

        def _flat_button(self, parent, text, command, accent=False,
                         font=None, **pack_kwargs):
            """A small consistently-styled tk.Button -- flat relief, no
            focus ring, an optional accent fill for primary actions.
            Centralizes the repeated look every toolbar/toolbox button in
            this module shares; pack_kwargs are forwarded to .pack().
            """
            fg_ = self._accent_fg if accent else self._panel_fg
            bg_ = self._accent if accent else "#FFFFFF"
            active_bg = "#1560AC" if accent else "#E8E8E8"
            btn = tk.Button(
                parent, text=text, command=command, font=font,
                bg=bg_, fg=fg_, activebackground=active_bg,
                activeforeground=fg_, relief="flat", bd=0,
                highlightthickness=0, cursor="hand2", padx=8, pady=4
            )
            if pack_kwargs:
                btn.pack(**pack_kwargs)
            # All flat builder buttons participate in contextual help mode.
            # The HelpMixin supplies a richer description where one exists.
            if hasattr(self, "_bind_context_help"):
                help_text = getattr(self, "_context_help_text_for")("control", text)
                self._bind_context_help(btn, help_text)
            return btn

        def _update_window_title_display(self):
            filename = os.path.basename(self.current_file_path) if self.current_file_path else "Untitled.tvd"
            dirty_marker = "*" if self._is_modified else ""
            self.root.title(
                f"Tkinter Visual Designer - [{filename}{dirty_marker}]"
                )

        def _build_ui(self):
            self.root.grid_rowconfigure(0, weight=0)
            self.root.grid_rowconfigure(1, weight=1)
            self.root.grid_rowconfigure(2, weight=0)
            self.root.grid_columnconfigure(0, weight=1)

            self._build_toolbar()

            self.v_paned = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
            self.v_paned.grid(row=1, column=0, sticky="nsew")

            self.main_paned = ttk.PanedWindow(self.v_paned,
                                               orient=tk.HORIZONTAL
                                               )
            self.v_paned.add(self.main_paned, weight=3)

            self.toolbox_frame = tk.Frame(self.main_paned, width=220,
                                           bg=self._panel_bg
                                           )
            self.toolbox_frame.pack_propagate(False)
            self.main_paned.add(self.toolbox_frame, weight=0)
            self._build_toolbox()

            center_frame = tk.Frame(self.main_paned, bg=self._panel_bg)
            self.main_paned.add(center_frame, weight=1)

            self.canvas_scroll_y = ttk.Scrollbar(center_frame,
                                                  orient=tk.VERTICAL
                                                  )
            self.canvas_scroll_x = ttk.Scrollbar(center_frame,
                                                  orient=tk.HORIZONTAL
                                                  )
            self.canvas = tk.Canvas(
                center_frame, bg=self.CANVAS_BG, width=self.CANVAS_W,
                height=self.CANVAS_H,
                yscrollcommand=self.canvas_scroll_y.set,
                xscrollcommand=self.canvas_scroll_x.set,
                takefocus=1, highlightthickness=0, relief="flat"
            )
            self.canvas_scroll_y.config(command=self.canvas.yview)
            self.canvas_scroll_x.config(command=self.canvas.xview)

            self.canvas.grid(row=0, column=0, sticky="nsew")
            self.canvas_scroll_y.grid(row=0, column=1, sticky="ns")
            self.canvas_scroll_x.grid(row=1, column=0, sticky="ew")
            center_frame.grid_rowconfigure(0, weight=1)
            center_frame.grid_columnconfigure(0, weight=1)

            self.canvas.config(
                scrollregion=(0, 0, self.CANVAS_W, self.CANVAS_H)
                )
            self.renderer = CanvasRenderer(self.canvas)
            self.renderer.zoom = self._zoom

            self.canvas.bind("<ButtonPress-1>", self._on_canvas_click)
            self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
            self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
            self.canvas.bind("<Double-Button-1>", self._on_canvas_double_click)
            self.canvas.bind("<ButtonPress-3>", self._on_canvas_scoped_select_press)
            self.canvas.bind("<B3-Motion>", self._on_canvas_scoped_select_drag)
            self.canvas.bind("<ButtonRelease-3>", self._on_canvas_scoped_select_release)
            self.canvas.bind("<Control-MouseWheel>", self._on_ctrl_zoom)
            self.canvas.bind("<Control-Button-4>", self._on_ctrl_zoom)
            self.canvas.bind("<Control-Button-5>", self._on_ctrl_zoom)

            self.prop_frame = tk.Frame(self.main_paned, width=400,
                                        bg=self._panel_bg
                                        )
            self.prop_frame.pack_propagate(False)
            self.main_paned.add(self.prop_frame, weight=0)
            self._build_property_inspector()

            self.code_frame = tk.Frame(self.v_paned, bg=self._panel_bg)
            self.code_frame.grid_rowconfigure(0, weight=0)
            self.code_frame.grid_rowconfigure(1, weight=1)
            self.code_frame.grid_rowconfigure(2, weight=0)
            self.code_frame.grid_columnconfigure(0, weight=1)
            self.code_frame.grid_columnconfigure(1, weight=0)

            code_header = tk.Frame(self.code_frame, bg=self._panel_bg)
            code_header.grid(row=0, column=0, columnspan=2, sticky="ew",
                              padx=2, pady=2
                              )
            tk.Label(code_header, text="LIVE CODE",
                     font=("Segoe UI", 10, "bold"), bg=self._panel_bg,
                     fg=self._panel_fg
                     ).pack(side=tk.LEFT, padx=5)

            self.code_text = tk.Text(
                self.code_frame, font=("Consolas", 13), wrap="none",
                fg="#1E1E1E", bg="#FAFAFA", relief="flat", borderwidth=0,
                highlightthickness=0
            )
            code_scroll_y = ttk.Scrollbar(
                self.code_frame, orient="vertical", command=self.code_text.yview
                )
            code_scroll_x = ttk.Scrollbar(
                self.code_frame, orient="horizontal", command=self.code_text.xview
                )
            self.code_text.configure(
                yscrollcommand=code_scroll_y.set, xscrollcommand=code_scroll_x.set
                )
            self.code_text.grid(row=1, column=0, sticky="nsew", padx=2,
                                 pady=2
                                 )
            code_scroll_y.grid(row=1, column=1, sticky="ns", pady=2)
            code_scroll_x.grid(row=2, column=0, sticky="ew", padx=2)
            self.code_text.configure(state="disabled")

            self.status_var = tk.StringVar()
            self.count_var = tk.StringVar()
            self.zoom_var = tk.StringVar(value="Zoom: 100%")
            status_bar = tk.Frame(self.root, bg=self._panel_bg)
            status_bar.grid(row=2, column=0, sticky="ew")
            tk.Label(status_bar, textvariable=self.status_var, anchor="w",
                     bg=self._panel_bg, fg=self._panel_fg
                     ).pack(side=tk.LEFT, fill=tk.X, expand=True,
                             padx=4, pady=2
                             )
            tk.Label(status_bar, textvariable=self.count_var, anchor="e",
                     bg=self._panel_bg, fg=self._panel_fg
                     ).pack(side=tk.RIGHT, padx=4, pady=2)
            tk.Label(status_bar, textvariable=self.zoom_var, anchor="e",
                     bg=self._panel_bg, fg=self._panel_fg
                     ).pack(side=tk.RIGHT, padx=10, pady=2)

        def _build_toolbar(self):
            toolbar = tk.Frame(self.root, bg=self._panel_bg)
            toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=4)
            toolbar.columnconfigure(0, weight=1)

            def _sep():
                tk.Frame(toolbar, width=2, height=28, bg="#D0D0D0").pack(
                    side=tk.LEFT, fill=tk.Y, padx=5, pady=2
                    )

            self._flat_button(toolbar, "📄 New Design", self._new_design,
                              side=tk.LEFT, padx=2)
            self._flat_button(toolbar, "📂 Load Design", self._load_design,
                              side=tk.LEFT, padx=2)
            self._flat_button(toolbar, "💾 Save Design", self._save_design,
                              side=tk.LEFT, padx=2)
            self._flat_button(toolbar, "💾 Save As", self._save_design_as,
                              side=tk.LEFT, padx=2)
            _sep()
            undo_btn = self._flat_button(toolbar, " ↶ ", self._undo,
                                         font=("Helv", 14, "bold"))
            undo_btn.pack(side=tk.LEFT, padx=2)
            undo_btn.bind("<Enter>", lambda e, b=undo_btn: self._show_tooltip(b,
                                                                              "Undo (Ctrl+Z)"
                                                                              )
                           )
            undo_btn.bind("<Leave>", self._hide_tooltip)
            redo_btn = self._flat_button(toolbar, " ↷ ", self._redo,
                                         font=("Helv", 14, "bold"))
            redo_btn.pack(side=tk.LEFT, padx=2)
            redo_btn.bind("<Enter>", lambda e, b=redo_btn: self._show_tooltip(b,
                                                                              "Redo (Ctrl+Y)"
                                                                              )
                           )
            redo_btn.bind("<Leave>", self._hide_tooltip)
            _sep()
            self._flat_button(toolbar, "🗑️ Delete", self._delete_selected,
                              side=tk.LEFT, padx=2)
            self._flat_button(toolbar, "🧹 Clear Canvas", self._clear_all,
                              side=tk.LEFT, padx=2)
            _sep()

            self._flat_button(toolbar, "📋 Copy Code", self._copy_code,
                              side=tk.LEFT, padx=2)
            self._flat_button(toolbar, "▶ Run Preview", self._run_preview,
                              accent=True, side=tk.LEFT, padx=2)
            _sep()
            self._flat_button(toolbar, "👁️ Toggle Code", self._toggle_code_view,
                              side=tk.LEFT, padx=2)
            _sep()
            self._flat_button(toolbar, "📝 Code Editor",
                              lambda: self._open_code_editor(None),
                              side=tk.LEFT, padx=2)

            # Keep help controls at the far right so the toolbar remains usable
            # as the application window changes size.
            tk.Frame(toolbar, bg=self._panel_bg).pack(side=tk.LEFT, fill=tk.X, expand=True)
            self._context_help_btn = tk.Button(
                toolbar, text="?", command=self._help_toggle,
                font=("Segoe UI", 12, "bold"), width=3,
                bg="#FFFFFF", fg=self._panel_fg, activebackground="#E8E8E8",
                activeforeground=self._panel_fg, relief="flat", bd=0,
                highlightthickness=0, cursor="hand2", padx=5, pady=3
            )
            self._context_help_btn.pack(side=tk.LEFT, padx=(4, 2))
            self._bind_context_help(
                self._context_help_btn,
                "Context Help Mode — click ? to enable/disable hover help for canvas elements, toolbox items, and main UI controls."
            )
            help_btn = self._flat_button(
                toolbar, "Help", self._open_help, side=tk.LEFT, padx=2
            )
            self._bind_context_help(
                help_btn,
                "Open the complete in-app Help Guide covering every GUI element, its properties, selection, code generation, and keyboard shortcuts."
            )

        def _toggle_code_view(self):
            if self.code_visible:
                self.v_paned.forget(self.code_frame)
                self.code_visible = False
                self._update_status("Live code section hidden.")
            else:
                self.v_paned.add(self.code_frame, weight=1)
                self.code_visible = True
                self._update_status("Live code section visible.")

        def _build_toolbox(self):
            header = tk.Frame(self.toolbox_frame, bg=self._panel_bg)
            header.pack(fill=tk.X, pady=(4, 3))
            tk.Label(header, text="TOOLBOX", font=("Segoe UI", 10, "bold"),
                     bg=self._panel_bg, fg=self._panel_fg
                     ).pack(side=tk.LEFT, padx=6)
            self._toolbox_toggle_btn = self._flat_button(
                header, "⊞ Icons", self._toggle_toolbox_mode,
                font=("Segoe UI", 10)
            )
            self._toolbox_toggle_btn.pack(side=tk.RIGHT, padx=6)
            self._bind_context_help(
                self._toolbox_toggle_btn,
                "Toggle toolbox presentation between labeled list mode and compact icon mode."
            )
            toolbox_label = header.winfo_children()[0]
            self._bind_context_help(toolbox_label, "TOOLBOX — choose a GUI element, then click the canvas to place it.")

            self.toolbox_items_container = _VScrollFrame(
                self.toolbox_frame, bg=self._panel_bg
                )
            self.toolbox_items_container.pack(fill=tk.BOTH, expand=True, padx=2,
                                              pady=1)
            toolbox_items_parent = self.toolbox_items_container.inner

            self._toolbox_items = {}  # name -> (frame, icon_lbl, name_lbl)
            self._toolbox_buttons = {}  # name -> frame
            self._toolbox_category_frames = {}  # cat -> (header_lbl, items_frame)

            categories = {}
            for name, spec in ELEMENT_TYPES.items():
                cat = spec.get("category", "Other")
                categories.setdefault(cat, []).append((name, spec))

            category_order = ["Input", "Instrumentation", "Containers", "Display"]
            ordered_categories = [c for c in category_order if c in categories] + [c for c in categories if c not in category_order]
            for cat in ordered_categories:
                # Each category gets its own always-packed wrapper. The header
                # label lives directly in this wrapper (always packed). The
                # items live in a dedicated sub-frame that we can freely switch
                # between pack (list mode) and grid (compact mode) without ever
                # mixing geometry managers with sibling widgets.
                cat_wrapper = tk.Frame(toolbox_items_parent, bg=self._panel_bg)
                cat_wrapper.pack(fill=tk.X, padx=0, pady=0)

                header_lbl = tk.Label(cat_wrapper, text=cat,
                              font=("Segoe UI", 9, "bold"),
                              anchor="w", bg=self._panel_bg, fg=self._panel_fg
                              )
                header_lbl.pack(anchor=tk.W, padx=5, pady=(8, 1))

                items_frame = tk.Frame(cat_wrapper, bg=self._panel_bg)
                items_frame.pack(fill=tk.X, padx=0, pady=0)

                self._toolbox_category_frames[cat] = (header_lbl, items_frame)

                for name, spec in sorted(categories[cat], key=lambda x: x[0]):
                    display_str = spec["display"]
                    parts = display_str.split(" ", 1)
                    icon = parts[0] if len(parts) > 1 else ""
                    elem_name = parts[1] if len(parts) > 1 else display_str

                    item_frame = tk.Frame(items_frame, cursor="hand2",
                                           bg=TOOLBOX_NORMAL_COLOR
                                           )
                    item_frame.pack(fill=tk.X, padx=5, pady=1)

                    lbl_icon = tk.Label(item_frame, text=icon, anchor="w",
                                        font=("Segoe UI Emoji", 12),
                                        bg=TOOLBOX_NORMAL_COLOR
                                        )
                    lbl_icon.pack(side=tk.LEFT, padx=6, pady=4)

                    lbl_name = tk.Label(item_frame, text=elem_name,
                                         anchor="e", bg=TOOLBOX_NORMAL_COLOR,
                                         fg=self._panel_fg
                                         )
                    lbl_name.pack(side=tk.RIGHT, padx=6, pady=4)

                    def on_click(e, t=name):
                        self._tool_selected(t)

                    def on_enter(e, f=item_frame, tip=elem_name):
                        f.configure(bg=TOOLBOX_HOVER_COLOR)
                        for child in f.winfo_children():
                            child.configure(bg=TOOLBOX_HOVER_COLOR)
                        if self._toolbox_compact and not self._context_help_enabled:
                            self._show_tooltip(f, tip)
                        if self._context_help_enabled:
                            self._context_help_target = f
                            self._show_tooltip(
                                f,
                                self._context_help_text_for("element", tip)
                            )

                    def on_leave(e, f=item_frame):
                        f.configure(bg=TOOLBOX_NORMAL_COLOR)
                        for child in f.winfo_children():
                            child.configure(bg=TOOLBOX_NORMAL_COLOR)
                        if self._context_help_target is f or self._toolbox_compact:
                            self._hide_tooltip()

                    for widget in (item_frame, lbl_icon, lbl_name):
                        widget.bind("<Button-1>", on_click)
                        widget.bind("<Enter>", on_enter)
                        widget.bind("<Leave>", on_leave)
                        # Keep contextual help active over the entire sidebar row,
                        # not just its text/icon child.

                    self._toolbox_items[name] = (item_frame, lbl_icon, lbl_name, cat)
                    self._toolbox_buttons[name] = item_frame

            self._toolbox_compact = False

        def _toggle_toolbox_mode( self ):
            self._toolbox_compact = not self._toolbox_compact

            # Group items by category so each category's own items_frame is
            # gridded/packed independently. Each items_frame is a distinct
            # parent, so this never mixes geometry managers within one parent.
            items_by_cat = {}
            for name, (frame, icon_lbl, name_lbl, cat) in self._toolbox_items.items():
                items_by_cat.setdefault(cat, []).append((frame, icon_lbl, name_lbl))

            if self._toolbox_compact:
                # Compact mode: grid with 3 columns per category, larger icons
                for frame, icon_lbl, name_lbl, _cat in self._toolbox_items.values():
                    frame.pack_forget()
                    name_lbl.pack_forget()
                    icon_lbl.pack_forget()
                    icon_lbl.configure(
                        font = ("Segoe UI Emoji", 18)
                        )
                    icon_lbl.pack( expand = True, fill = tk.BOTH, padx = 4,
                                   pady = 4
                                   )

                for cat, (header_lbl, items_frame) in self._toolbox_category_frames.items():
                    row = col = 0
                    for frame, icon_lbl, name_lbl in items_by_cat.get(cat, []):
                        # grid these into items_frame, which never has pack siblings
                        frame.grid( row = row, column = col, padx = 2, pady = 2,
                                    sticky = "nsew"
                                    )
                        col += 1
                        if col >= 3:
                            col = 0
                            row += 1
                    for c in range( 3 ):
                        items_frame.grid_columnconfigure( c, weight = 1 )
                self._toolbox_toggle_btn.configure( text = "☰ Labels" )
            else:
                # Two-phase transition, mirroring the compact-mode branch:
                # forget ALL grid placements first, THEN pack everything back.
                # Packing a frame immediately after forgetting only itself
                # (while siblings in the same items_frame are still under grid)
                # mixes geometry managers within one parent and raises TclError.
                for frame, icon_lbl, name_lbl, _cat in self._toolbox_items.values():
                    frame.grid_forget()

                for frame, icon_lbl, name_lbl, _cat in self._toolbox_items.values():
                    icon_lbl.pack_forget()
                    name_lbl.pack_forget()
                    icon_lbl.configure(
                        font = ("Segoe UI Emoji", 12)
                        )
                    frame.pack( fill = tk.X, padx = 4, pady = 0 )
                    icon_lbl.pack( side = tk.LEFT, padx = 6, pady = 4 )
                    name_lbl.pack( side = tk.RIGHT, padx = 6, pady = 4 )
                self._toolbox_toggle_btn.configure( text = "⊞ Icons" )

        def _show_tooltip(self, widget, text):
            self._hide_tooltip()
            if not text:
                return
            try:
                x = widget.winfo_pointerx() + 14
                y = widget.winfo_pointery() + 18
                if x < 0 or y < 0:
                    x = widget.winfo_rootx()
                    y = widget.winfo_rooty() + widget.winfo_height() + 4
            except Exception:
                return
            self._tooltip_win = tk.Toplevel(self.root)
            self._tooltip_win.wm_overrideredirect(True)
            label = tk.Label(
                self._tooltip_win, text=text, justify=tk.LEFT,
                wraplength=420,
                background="#2b2b2b", foreground="#ffffff",
                relief=tk.SOLID, borderwidth=1, font=("Segoe UI", 9),
                padx=8, pady=5
            )
            label.pack()
            self._tooltip_win.update_idletasks()
            sw = self._tooltip_win.winfo_screenwidth()
            sh = self._tooltip_win.winfo_screenheight()
            tw = self._tooltip_win.winfo_reqwidth()
            th = self._tooltip_win.winfo_reqheight()
            x = min(max(4, x), max(4, sw - tw - 8))
            y = min(max(4, y), max(4, sh - th - 8))
            self._tooltip_win.wm_geometry(f"+{x}+{y}")

        def _hide_tooltip(self, event=None):
            if getattr(self, "_tooltip_win", None) is not None:
                try:
                    self._tooltip_win.destroy()
                except Exception:
                    pass
                self._tooltip_win = None

        def _on_canvas_motion(self, event):
            x, y = self._logical_xy(event)
            elem = self._find_element_at(x, y)
            if elem and self._context_help_enabled:
                tooltip_text = self._context_help_text_for("element", elem=elem)
                # Position directly near the pointer for responsive contextual help.
                self._show_tooltip(self.canvas, tooltip_text)
                return
            if elem and not self._context_help_enabled:
                self._hide_tooltip()
            else:
                self._hide_tooltip()

        def _on_canvas_leave(self, event):
            self._hide_tooltip()

        def _on_ctrl_zoom(self, event):
            if getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0:
                self._zoom = min(3.0, self._zoom * 1.1)
            elif getattr(event, "num", None) == 5 or getattr(event, "delta", 0) < 0:
                self._zoom = max(0.3, self._zoom / 1.1)
            else:
                return "break"
            self.renderer.zoom = self._zoom
            self.canvas.config(
                scrollregion=(0, 0, int(self.CANVAS_W * self._zoom),
                                int(self.CANVAS_H * self._zoom))
                )
            self.renderer.draw_grid(self.CANVAS_W, self.CANVAS_H)
            self._redraw_all_elements()
            self._update_zoom_label()
            return "break"

        def _update_zoom_label(self):
            if hasattr(self, "zoom_var"):
                self.zoom_var.set(f"Zoom: {int(round(self._zoom * 100))}%")

        def _highlight_active_tool(self, active_name: str):
            for name in ELEMENT_TYPES:
                frame = self._toolbox_buttons.get(name)
                if frame:
                    color = TOOLBOX_ACTIVE_COLOR if name == active_name else TOOLBOX_NORMAL_COLOR
                    frame.configure(bg=color)
                    for child in frame.winfo_children():
                        child.configure(bg=color)

        def _reset_tool_colors(self):
            for name in ELEMENT_TYPES:
                frame = self._toolbox_buttons.get(name)
                if frame:
                    frame.configure(bg=TOOLBOX_NORMAL_COLOR)
                    for child in frame.winfo_children():
                        child.configure(bg=TOOLBOX_NORMAL_COLOR)

        def _build_property_inspector(self):
            tk.Label(self.prop_frame, text="PROPERTIES",
                     font=("Segoe UI", 10, "bold"), bg=self._panel_bg,
                     fg=self._panel_fg
                     ).pack(pady=(5, 6))
            self.prop_title_label = tk.Label(self.prop_frame,
                                              text="No element selected.",
                                              anchor="w", bg=self._panel_bg,
                                              fg=self._panel_fg
                                              )
            self.prop_title_label.pack(anchor=tk.W, padx=6, pady=(0, 2),
                                        fill=tk.X
                                        )
            self.prop_context_var = tk.StringVar(value="Container: None")
            tk.Label(self.prop_frame, textvariable=self.prop_context_var,
                     fg=self._muted_fg, bg=self._panel_bg, anchor="w"
                     ).pack(anchor=tk.W, padx=6, pady=(0, 5),
                             fill=tk.X
                             )

            self.prop_scrollable = _VScrollFrame(self.prop_frame,
                                                  bg=self._panel_bg
                                                  )
            self.prop_scrollable.pack(fill=tk.BOTH, expand=True)
            prop_rows_parent = self.prop_scrollable.inner

            self.prop_rows = []
            for i in range(20):
                frame = tk.Frame(prop_rows_parent, bg=self._panel_bg)
                lbl = tk.Label(frame, text="", width=13, anchor="w",
                               bg=self._panel_bg, fg=self._panel_fg
                               )
                lbl.pack(side=tk.LEFT, padx=(2, 4))
                control_frame = tk.Frame(frame, bg=self._panel_bg)
                control_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
                self.prop_rows.append({
                    "frame": frame, "label": lbl, "control_frame": control_frame,
                    "widget": None, "visible": False,
                    "_shape": None, "_trace_id": None, "_combo_widget": None,
                }
                )
