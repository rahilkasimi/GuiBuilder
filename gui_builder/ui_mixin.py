"""UI construction, toolbars, toolbox, tooltip and view controls."""
from .dependencies import *
from .config import ELEMENT_TYPES, TOOLBOX_NORMAL_COLOR, TOOLBOX_HOVER_COLOR, TOOLBOX_ACTIVE_COLOR, THEMES, DEFAULT_THEME
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

        # Get current theme colors
        colors = self._get_theme_colors()
        self._panel_bg = colors["panel_bg"]
        self._panel_fg = colors["panel_fg"]
        self._muted_fg = colors["muted_fg"]
        self._accent = colors["accent"]
        self._accent_fg = colors["accent_fg"]
        self._hover_bg = colors.get("hover_bg", "#E3F2FD")
        self._button_bg = colors.get("button_bg", colors["panel_bg"])
        self._button_fg = colors.get("button_fg", colors["panel_fg"])
        self._button_hover_bg = colors.get("button_hover_bg", colors["panel_bg"])
        self._button_active_bg = colors.get("button_active_bg", colors["button_hover_bg"])
        self._separator = colors.get("separator", colors["panel_bg"])
        self._entry_bg = colors["entry_bg"]
        self._entry_fg = colors["entry_fg"]
        self._entry_insert = colors.get("entry_insert", colors["entry_fg"])
        self._entry_border = colors.get("entry_border", colors["panel_bg"])
        self._scroll_trough = colors.get("scroll_trough", colors["panel_bg"])
        self._scroll_hover = colors.get("scroll_hover", colors["hover_bg"])
        self._scroll_pressed = colors.get("scroll_pressed", colors["hover_bg"])

        # Apply ttk theme
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Treeview", background=self._entry_bg, foreground=self._panel_fg,
                         fieldbackground=self._entry_bg, rowheight=24,
                         borderwidth=0, relief="flat")
        style.map("Treeview",
                  background=[("selected", self._accent)],
                  foreground=[("selected", self._accent_fg)])
        style.configure("Treeview.Heading", background=self._panel_bg, foreground=self._panel_fg,
                         relief="flat", borderwidth=0)

        style.configure("TPanedWindow", background=self._panel_bg)
        style.configure("Sash", sashthickness=6, gripcount=0,
                         background=self._separator, lightcolor=self._separator,
                         darkcolor=self._separator)
        for orient in ("Vertical", "Horizontal"):
            name = f"{orient}.TScrollbar"
            style.configure(name, background=self._panel_bg,
                             troughcolor=self._scroll_trough,
                             bordercolor=self._panel_bg, arrowcolor=self._panel_fg,
                             relief="flat", borderwidth=0)
            style.map(name,
                      background=[("active", self._scroll_hover),
                                  ("pressed", self._scroll_pressed)])
        style.configure("TCombobox", fieldbackground=self._entry_bg,
                         background=self._button_bg, foreground=self._panel_fg,
                         bordercolor=self._entry_border, lightcolor=self._entry_border,
                         darkcolor=self._entry_border, arrowcolor=self._panel_fg)
        style.map("TCombobox",
                  fieldbackground=[("readonly", self._entry_bg), ("disabled", self._panel_bg)],
                  foreground=[("readonly", self._panel_fg), ("disabled", self._muted_fg)],
                  background=[("active", self._button_hover_bg), ("pressed", self._button_active_bg)])
        style.configure("TButton", background=self._button_bg, foreground=self._button_fg,
                        borderwidth=0, focusthickness=0)
        style.map("TButton",
                  background=[("active", self._button_hover_bg), ("pressed", self._button_active_bg)],
                  foreground=[("disabled", self._muted_fg)])

    def _flat_button(self, parent, text, command, accent=False,
                     font=None, **pack_kwargs):
        """A small consistently-styled tk.Button -- flat relief, no
        focus ring, an optional accent fill for primary actions.
        Centralizes the repeated look every toolbar/toolbox button in
        this module shares; pack_kwargs are forwarded to .pack().
        """
        colors = self._get_theme_colors()
        fg_ = colors["accent_fg"] if accent else colors["button_fg"]
        bg_ = colors["accent"] if accent else colors["button_bg"]
        active_bg = colors.get("accent_hover", colors["accent"]) if accent else colors["button_hover_bg"]
        btn = tk.Button(
            parent, text=text, command=command, font=font,
            bg=bg_, fg=fg_, activebackground=active_bg,
            activeforeground=fg_, relief="flat", bd=0,
            highlightthickness=0, cursor="hand2", padx=8, pady=4
        )
        btn._theme_role = "accent" if accent else "button"
        if pack_kwargs:
            btn.pack(**pack_kwargs)
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

    def _get_theme_colors(self, theme_name=None):
        """Return the theme dictionary for the given name or the current theme."""
        name = theme_name if theme_name is not None else getattr(self, "theme_name", DEFAULT_THEME)
        return THEMES.get(name, THEMES[DEFAULT_THEME])

    def _apply_theme(self, theme_name):
        """Switch the entire UI to the selected theme."""
        if theme_name not in THEMES:
            return
        self.theme_name = theme_name
        # Update main window
        self._apply_theme_to_main_window()
        # Update code editor if open
        if hasattr(self, "_code_editor_window") and self._code_editor_window is not None:
            try:
                if self._code_editor_window.winfo_exists():
                    self._apply_theme_to_code_editor(self._code_editor_window)
            except tk.TclError:
                pass
        # Update EXE log window if open
        if hasattr(self, "_exe_log_window") and self._exe_log_window is not None:
            try:
                if self._exe_log_window.winfo_exists():
                    self._apply_theme_to_exe_log(self._exe_log_window)
            except tk.TclError:
                pass
        # Update Help window if open
        if hasattr(self, "_help_window") and self._help_window is not None:
            try:
                if self._help_window.winfo_exists():
                    self._apply_theme_to_help_window(self._help_window)
            except tk.TclError:
                pass

    def _apply_theme_to_main_window(self):
        colors = self._get_theme_colors()
        # Update stored color attributes
        self._panel_bg = colors["panel_bg"]
        self._panel_fg = colors["panel_fg"]
        self._muted_fg = colors["muted_fg"]
        self._accent = colors["accent"]
        self._accent_fg = colors["accent_fg"]
        self._hover_bg = colors.get("hover_bg", "#E3F2FD")
        self._button_bg = colors.get("button_bg", colors["panel_bg"])
        self._button_fg = colors.get("button_fg", colors["panel_fg"])
        self._button_hover_bg = colors.get("button_hover_bg", colors["panel_bg"])
        self._button_active_bg = colors.get("button_active_bg", colors["button_hover_bg"])
        self._separator = colors.get("separator", colors["panel_bg"])
        self._entry_bg = colors["entry_bg"]
        self._entry_fg = colors["entry_fg"]
        self._entry_insert = colors.get("entry_insert", colors["entry_fg"])
        self._entry_border = colors.get("entry_border", colors["panel_bg"])
        self._scroll_trough = colors.get("scroll_trough", colors["panel_bg"])
        self._scroll_hover = colors.get("scroll_hover", colors["hover_bg"])
        self._scroll_pressed = colors.get("scroll_pressed", colors["hover_bg"])

        # Update root background
        self.root.configure(bg=colors["panel_bg"])

        # Update ttk styles
        style = ttk.Style()
        style.configure("TPanedWindow", background=colors["panel_bg"])
        style.configure("Sash", background=self._separator,
                        lightcolor=self._separator, darkcolor=self._separator)
        style.configure("TCombobox", fieldbackground=self._entry_bg,
                        background=self._button_bg, foreground=self._panel_fg,
                        bordercolor=self._entry_border, lightcolor=self._entry_border,
                        darkcolor=self._entry_border, arrowcolor=self._panel_fg)
        style.map("TCombobox",
                  fieldbackground=[("readonly", self._entry_bg), ("disabled", self._panel_bg)],
                  foreground=[("readonly", self._panel_fg), ("disabled", self._muted_fg)],
                  background=[("active", self._button_hover_bg), ("pressed", self._button_active_bg)])
        style.configure("TButton", background=self._button_bg, foreground=self._button_fg)
        style.map("TButton", background=[("active", self._button_hover_bg),
                                          ("pressed", self._button_active_bg)],
                  foreground=[("disabled", self._muted_fg)])
        style.configure("Treeview", background=self._entry_bg, foreground=self._panel_fg,
                        fieldbackground=self._entry_bg)
        style.map("Treeview", background=[("selected", self._accent)],
                  foreground=[("selected", self._accent_fg)])
        for orient in ("Vertical", "Horizontal"):
            style.map(f"{orient}.TScrollbar",
                      background=[("active", self._scroll_hover),
                                  ("pressed", self._scroll_pressed)])

        # Update known containers
        containers = [
            self.toolbar, self.toolbox_frame, self.prop_frame,
            self.code_frame, self.status_bar, self.v_paned
        ]
        for container in containers:
            self._update_widget_tree(container, colors)

        # Update property inspector rows
        for row in self.prop_rows:
            row["frame"].configure(bg=colors["panel_bg"])
            row["label"].configure(bg=colors["panel_bg"], fg=colors["panel_fg"])
            row["control_frame"].configure(bg=colors["panel_bg"])

        # Update code text background/foreground (if visible)
        self.code_text.configure(bg=colors["editor_bg"], fg=colors["editor_fg"],
                                 insertbackground=colors.get("insert_bg", colors["editor_fg"]),
                                 selectbackground=colors.get("selection_bg", colors["accent"]),
                                 selectforeground=colors.get("selection_fg", colors["accent_fg"]))

        # Update status bar labels
        for child in self.status_bar.winfo_children():
            if isinstance(child, tk.Label):
                child.configure(bg=colors["panel_bg"], fg=colors["panel_fg"])

        # --- FIX: Update toolbox items ---
        for frame in self._toolbox_buttons.values():
            frame.configure(bg=self._panel_bg)
            for child in frame.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=self._panel_bg)

        # --- FIX: Update property inspector scrollable area ---
        if hasattr(self, "prop_scrollable"):
            self.prop_scrollable.configure(bg=colors["panel_bg"])
            self.prop_scrollable.inner.configure(bg=colors["panel_bg"])
            try:
                self.prop_scrollable._canvas.configure(bg=colors["panel_bg"])
            except AttributeError:
                pass

    def _update_widget_tree(self, widget, colors):
        """Recursively update background/foreground of common tkinter widgets."""
        try:
            if isinstance(widget, tk.Frame):
                widget.configure(bg=colors["panel_bg"])
            elif isinstance(widget, tk.Label):
                widget.configure(bg=colors["panel_bg"], fg=colors["panel_fg"])
            elif isinstance(widget, tk.Button):
                role = getattr(widget, "_theme_role", "button")
                if role == "accent":
                    widget.configure(bg=colors["accent"], fg=colors["accent_fg"],
                                     activebackground=colors.get("accent_hover", colors["accent"]),
                                     activeforeground=colors["accent_fg"])
                elif role == "context":
                    widget.configure(bg=colors["accent"] if getattr(self, "_context_help_enabled", False) else colors["button_bg"],
                                     fg=colors["accent_fg"] if getattr(self, "_context_help_enabled", False) else colors["button_fg"],
                                     activebackground=colors.get("accent_hover", colors["accent"]) if getattr(self, "_context_help_enabled", False) else colors["button_hover_bg"],
                                     activeforeground=colors["accent_fg"] if getattr(self, "_context_help_enabled", False) else colors["button_fg"])
                else:
                    widget.configure(bg=colors["button_bg"], fg=colors["button_fg"],
                                     activebackground=colors["button_hover_bg"],
                                     activeforeground=colors["button_fg"])
            elif isinstance(widget, tk.Entry):
                widget.configure(bg=colors["entry_bg"], fg=colors["entry_fg"],
                                 insertbackground=colors.get("entry_insert", colors["entry_fg"]),
                                 highlightbackground=colors.get("entry_border", colors["panel_bg"]),
                                 highlightcolor=colors["accent"])
            elif isinstance(widget, tk.Text):
                widget.configure(bg=colors["editor_bg"], fg=colors["editor_fg"],
                                 insertbackground=colors.get("insert_bg", colors["editor_fg"]),
                                 selectbackground=colors.get("selection_bg", colors["accent"]),
                                 selectforeground=colors.get("selection_fg", colors["accent_fg"]))
        except tk.TclError:
            pass
        try:
            for child in widget.winfo_children():
                self._update_widget_tree(child, colors)
        except tk.TclError:
            pass

    def _apply_theme_to_help_window(self, window):
        """Refresh an already-open Help window without rebuilding its content."""
        colors = self._get_theme_colors()
        widgets = getattr(window, "_theme_widgets", {})
        if not widgets:
            return
        if "header" in widgets:
            widgets["header"].configure(bg=colors["accent"])
        if "body" in widgets:
            widgets["body"].configure(bg=colors["panel_bg"])
        if "title_label" in widgets:
            widgets["title_label"].configure(bg=colors["accent"], fg=colors["accent_fg"])
        if "close_button" in widgets:
            widgets["close_button"].configure(
                bg=colors["button_bg"], fg=colors["button_fg"],
                activebackground=colors["button_hover_bg"],
                activeforeground=colors["button_fg"])
        if "text" in widgets:
            text = widgets["text"]
            text.configure(
                bg=colors["entry_bg"], fg=colors["panel_fg"],
                insertbackground=colors.get("insert_bg", colors["panel_fg"]),
                selectbackground=colors["selection_bg"],
                selectforeground=colors.get("selection_fg", colors["accent_fg"]))
            text.tag_configure("muted", foreground=colors["muted_fg"])
            text.tag_configure("code", background=colors["button_hover_bg"],
                               foreground=colors["panel_fg"])
            text.tag_configure("search_match", background=colors.get("search_match_bg", "#FFF3CD"),
                               foreground=colors.get("search_match_fg", colors["panel_fg"]))
            text.tag_configure("search_current", background=colors.get("search_current_bg", colors["accent"]),
                               foreground=colors.get("search_current_fg", colors["accent_fg"]))
            text.tag_configure("bookmark_jump", background=colors.get("highlight_bg", "#FFF3CD"),
                               foreground=colors.get("highlight_fg", colors["panel_fg"]))
        if "tree_frame" in widgets:
            widgets["tree_frame"].configure(bg=colors["panel_bg"])
        if "tree_header" in widgets:
            widgets["tree_header"].configure(bg=colors["panel_bg"], fg=colors["panel_fg"])
        # The bookmark Treeview itself follows the global "Treeview" ttk
        # style, which _apply_theme_to_main_window() already reconfigures
        # on every theme switch -- nothing to do for it here.
        search_bg = colors.get("search_frame_bg", colors["panel_bg"])
        if "search_frame" in widgets:
            widgets["search_frame"].configure(bg=search_bg)
        if "find_label" in widgets:
            widgets["find_label"].configure(bg=search_bg, fg=colors["panel_fg"])
        if "search_status_label" in widgets:
            widgets["search_status_label"].configure(bg=search_bg, fg=colors["muted_fg"])
        if "find_entry" in widgets:
            widgets["find_entry"].configure(
                bg=colors["entry_bg"], fg=colors["entry_fg"],
                insertbackground=colors.get("entry_insert", colors["entry_fg"]),
                highlightbackground=colors.get("entry_border", colors["panel_bg"]),
                highlightcolor=colors["accent"])
        for key in ("prev_button", "next_button"):
            if key in widgets:
                widgets[key].configure(
                    bg=colors["button_bg"], fg=colors["button_fg"],
                    activebackground=colors["button_hover_bg"],
                    activeforeground=colors["button_fg"])

    def _apply_theme_to_code_editor(self, window):
        """Update the code editor window with the current theme."""
        colors = self._get_theme_colors()
        theme_widgets = getattr(window, "_theme_widgets", {})
        if not theme_widgets:
            return
        if "text_widget" in theme_widgets:
            theme_widgets["text_widget"].configure(
                bg=colors["editor_bg"], fg=colors["editor_fg"],
                selectbackground=colors["selection_bg"]
            )
        if "linenumbers" in theme_widgets:
            theme_widgets["linenumbers"].configure(bg=colors["line_numbers_bg"])
            if "redraw_linenumbers" in theme_widgets:
                theme_widgets["redraw_linenumbers"]()
        if "syntax_bar" in theme_widgets:
            theme_widgets["syntax_bar"].configure(bg=colors["panel_bg"])
        if "syntax_status_label" in theme_widgets:
            theme_widgets["syntax_status_label"].configure(
                bg=colors["panel_bg"], fg=colors["panel_fg"]
            )
        if "line_col_label" in theme_widgets:
            theme_widgets["line_col_label"].configure(
                bg=colors["panel_bg"], fg=colors["panel_fg"]
            )
        if "search_frame" in theme_widgets:
            theme_widgets["search_frame"].configure(bg=colors["search_frame_bg"])
        if "find_entry" in theme_widgets:
            theme_widgets["find_entry"].configure(
                bg=colors["search_entry_bg"], fg=colors["search_entry_fg"]
            )
        if "replace_entry" in theme_widgets:
            theme_widgets["replace_entry"].configure(
                bg=colors["search_entry_bg"], fg=colors["search_entry_fg"]
            )
        if "search_status_label" in theme_widgets:
            theme_widgets["search_status_label"].configure(
                bg=colors["search_frame_bg"], fg=colors["muted_fg"]
            )
        try:
            text = theme_widgets.get("text_widget")
            if text is not None:
                text.tag_config("syntax_error",
                                background=colors.get("syntax_error_bg", colors["highlight_bg"]),
                                foreground=colors.get("syntax_error_fg", colors["panel_fg"]))
                text.tag_config("search_match",
                                background=colors.get("search_match_bg", colors["highlight_bg"]),
                                foreground=colors.get("search_match_fg", colors["editor_fg"]))
                text.tag_config("search_current",
                                background=colors.get("search_current_bg", colors["accent"]),
                                foreground=colors.get("search_current_fg", colors["accent_fg"]))
                text.tag_config("highlight",
                                background=colors["highlight_bg"],
                                foreground=colors["highlight_fg"])
        except tk.TclError:
            pass
        # Update buttons in the editor window
        for child in window.winfo_children():
            if isinstance(child, tk.Button):
                self._update_widget_tree(child, colors)
            elif isinstance(child, tk.Frame):
                self._update_widget_tree(child, colors)

    def _apply_theme_to_exe_log(self, window):
        colors = self._get_theme_colors()
        theme_widgets = getattr(window, "_theme_widgets", {})
        if "log_text" in theme_widgets:
            theme_widgets["log_text"].configure(
                bg=colors["log_bg"], fg=colors["log_fg"]
            )
        if "log_frame" in theme_widgets:
            theme_widgets["log_frame"].configure(bg=colors["panel_bg"])
        for child in window.winfo_children():
            if isinstance(child, tk.Frame):
                self._update_widget_tree(child, colors)
            elif isinstance(child, tk.Label):
                child.configure(bg=colors["panel_bg"], fg=colors["panel_fg"])

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

        colors = self._get_theme_colors()
        self.toolbox_frame = tk.Frame(self.main_paned, width=220,
                                       bg=colors["panel_bg"]
                                       )
        self.toolbox_frame.pack_propagate(False)
        self.main_paned.add(self.toolbox_frame, weight=0)
        self._build_toolbox()

        center_frame = tk.Frame(self.main_paned, bg=colors["panel_bg"])
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
                                    bg=colors["panel_bg"]
                                    )
        self.prop_frame.pack_propagate(False)
        self.main_paned.add(self.prop_frame, weight=0)
        self._build_property_inspector()

        self.code_frame = tk.Frame(self.v_paned, bg=colors["panel_bg"])
        self.code_frame.grid_rowconfigure(0, weight=0)
        self.code_frame.grid_rowconfigure(1, weight=1)
        self.code_frame.grid_rowconfigure(2, weight=0)
        self.code_frame.grid_columnconfigure(0, weight=1)
        self.code_frame.grid_columnconfigure(1, weight=0)

        code_header = tk.Frame(self.code_frame, bg=colors["panel_bg"])
        code_header.grid(row=0, column=0, columnspan=2, sticky="ew",
                          padx=2, pady=2
                          )
        tk.Label(code_header, text="LIVE CODE",
                 font=("Segoe UI", 10, "bold"), bg=colors["panel_bg"],
                 fg=colors["panel_fg"]
                 ).pack(side=tk.LEFT, padx=5)

        self.code_text = tk.Text(
            self.code_frame, font=("Consolas", 13), wrap="none",
            fg=colors["editor_fg"], bg=colors["editor_bg"], relief="flat", borderwidth=0,
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
        self.position_var = tk.StringVar(value="Canvas: --, --    Size: -- × --")
        status_bar = tk.Frame(self.root, bg=colors["panel_bg"])
        status_bar.grid(row=2, column=0, sticky="ew")
        tk.Label(status_bar, textvariable=self.position_var, anchor="w",
                 bg=colors["panel_bg"], fg=colors["panel_fg"]
                 ).pack(side=tk.LEFT, padx=8, pady=2)
        tk.Label(status_bar, textvariable=self.status_var, anchor="w",
                 bg=colors["panel_bg"], fg=colors["panel_fg"]
                 ).pack(side=tk.LEFT, fill=tk.X, expand=True,
                         padx=4, pady=2
                         )
        tk.Label(status_bar, textvariable=self.count_var, anchor="e",
                 bg=colors["panel_bg"], fg=colors["panel_fg"]
                 ).pack(side=tk.RIGHT, padx=4, pady=2)
        tk.Label(status_bar, textvariable=self.zoom_var, anchor="e",
                 bg=colors["panel_bg"], fg=colors["panel_fg"]
                 ).pack(side=tk.RIGHT, padx=10, pady=2)
        self.status_bar = status_bar

    def _build_toolbar(self):
        toolbar = tk.Frame(self.root, bg=self._panel_bg)
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=4)
        toolbar.columnconfigure(0, weight=1)

        def _sep():
            tk.Frame(toolbar, width=2, height=28, bg=self._separator).pack(
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
                                                                          "Undo (Ctrl+Z)")
                       )
        undo_btn.bind("<Leave>", self._hide_tooltip)
        redo_btn = self._flat_button(toolbar, " ↷ ", self._redo,
                                     font=("Helv", 14, "bold"))
        redo_btn.pack(side=tk.LEFT, padx=2)
        redo_btn.bind("<Enter>", lambda e, b=redo_btn: self._show_tooltip(b,
                                                                          "Redo (Ctrl+Y)")
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

        # ---- Theme selector ----
        theme_var = tk.StringVar(value=self.theme_name)
        theme_combo = ttk.Combobox(toolbar, textvariable=theme_var,
                                   values=list(THEMES.keys()), width=10,
                                   state="readonly")
        theme_combo.pack(side=tk.LEFT, padx=(4, 2))
        theme_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_theme(theme_var.get()))
        self._bind_context_help(theme_combo, "Switch between Light and Dark themes for the entire application.")

        self._context_help_btn = tk.Button(
            toolbar, text="?", command=self._help_toggle,
            font=("Segoe UI", 12, "bold"), width=3,
            bg=self._button_bg, fg=self._button_fg, activebackground=self._button_hover_bg,
            activeforeground=self._button_fg, relief="flat", bd=0,
            highlightthickness=0, cursor="hand2", padx=5, pady=3
        )
        self._context_help_btn._theme_role = "context"
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
        self.toolbar = toolbar

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
                          font=("Segoe UI", 8, "bold"),
                          anchor="w", bg=self._panel_bg, fg=self._panel_fg
                          )
            header_lbl.pack(anchor=tk.W, padx=5, pady=(4, 0))

            items_frame = tk.Frame(cat_wrapper, bg=self._panel_bg)
            items_frame.pack(fill=tk.X, padx=0, pady=0)

            self._toolbox_category_frames[cat] = (header_lbl, items_frame)

            for name, spec in sorted(categories[cat], key=lambda x: x[0]):
                display_str = spec["display"]
                parts = display_str.split(" ", 1)
                icon = parts[0] if len(parts) > 1 else ""
                elem_name = parts[1] if len(parts) > 1 else display_str

                # --- FIX: use self._panel_bg instead of hard-coded TOOLBOX_NORMAL_COLOR ---
                item_frame = tk.Frame(items_frame, cursor="hand2",
                                      bg=self._panel_bg)
                item_frame.pack(fill=tk.X, padx=2, pady=0)

                lbl_icon = tk.Label(item_frame, text=icon, anchor="w",
                                    font=("Segoe UI Emoji", 10),
                                    bg=self._panel_bg)
                lbl_icon.pack(side=tk.LEFT, padx=(4, 3), pady=1)

                lbl_name = tk.Label(item_frame, text=elem_name,
                                    anchor="w", bg=self._panel_bg,
                                    fg=self._panel_fg,
                                    font=("Segoe UI", 8))
                lbl_name.pack(side=tk.LEFT, padx=1, pady=1)

                def on_click(e, t=name):
                    self._tool_selected(t)

                # --- FIX: use self._hover_bg and self._panel_bg for enter/leave ---
                def on_enter(e, f=item_frame, tip=elem_name):
                    f.configure(bg=self._hover_bg)
                    for child in f.winfo_children():
                        child.configure(bg=self._hover_bg)
                    if self._toolbox_compact and not self._context_help_enabled:
                        self._show_tooltip(f, tip)
                    if self._context_help_enabled:
                        self._context_help_target = f
                        self._show_tooltip(
                            f,
                            self._context_help_text_for("element", tip)
                        )

                def on_leave(e, f=item_frame):
                    f.configure(bg=self._panel_bg)
                    for child in f.winfo_children():
                        child.configure(bg=self._panel_bg)
                    if self._context_help_target is f or self._toolbox_compact:
                        self._hide_tooltip()

                for widget in (item_frame, lbl_icon, lbl_name):
                    widget.bind("<Button-1>", on_click)
                    widget.bind("<Enter>", on_enter)
                    widget.bind("<Leave>", on_leave)

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
                    font = ("Segoe UI Emoji", 10)
                    )
                frame.pack( fill = tk.X, padx = 2, pady = 0 )
                icon_lbl.pack( side = tk.LEFT, padx = (4, 3), pady = 1 )
                name_lbl.pack( side = tk.LEFT, padx = 1, pady = 1 )
            self._toolbox_toggle_btn.configure( text = "⊞ Icons" )

    def _show_tooltip(self, widget, text):
        self._hide_tooltip()
        if not text:
            return
        colors = self._get_theme_colors()
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
            background=colors["tooltip_bg"], foreground=colors["tooltip_fg"],
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
        self._update_resize_cursor(x, y)
        elem = self._find_element_at(x, y)
        if elem and self._context_help_enabled:
            tooltip_text = self._context_help_text_for("element", elem=elem)
            self._show_tooltip(self.canvas, tooltip_text)
            return
        if elem and not self._context_help_enabled:
            self._hide_tooltip()
        else:
            self._hide_tooltip()

    def _on_canvas_leave(self, event):
        self._hide_tooltip()
        if self.drag_mode in ("none", None) and str(self.canvas.cget("cursor")) != "":
            self.canvas.config(cursor="")

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
        # Re-render all canvas decorations at the new zoom so the surface,
        # background image, and border stay perfectly synchronized.
        self.renderer.draw_canvas_surface(self.CANVAS_W, self.CANVAS_H, self.CANVAS_BG)
        self.renderer.draw_canvas_background(
            self.CANVAS_BG_IMAGE, self.CANVAS_BG_IMAGE_MODE,
            self.CANVAS_BG_IMAGE_ANCHOR, self.CANVAS_W, self.CANVAS_H
        )
        self.renderer.draw_canvas_border(self.CANVAS_W, self.CANVAS_H)
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
                color = TOOLBOX_ACTIVE_COLOR if name == active_name else self._panel_bg
                frame.configure(bg=color)
                for child in frame.winfo_children():
                    child.configure(bg=color)

    def _reset_tool_colors(self):
        for name in ELEMENT_TYPES:
            frame = self._toolbox_buttons.get(name)
            if frame:
                frame.configure(bg=self._panel_bg)
                for child in frame.winfo_children():
                    child.configure(bg=self._panel_bg)

    def _build_property_inspector(self):
        colors = self._get_theme_colors()
        tk.Label(self.prop_frame, text="PROPERTIES",
                 font=("Segoe UI", 10, "bold"), bg=colors["panel_bg"],
                 fg=colors["panel_fg"]
                 ).pack(pady=(5, 6))
        self.prop_title_label = tk.Label(self.prop_frame,
                                          text="No element selected.",
                                          anchor="w", bg=colors["panel_bg"],
                                          fg=colors["panel_fg"]
                                          )
        self.prop_title_label.pack(anchor=tk.W, padx=6, pady=(0, 2),
                                    fill=tk.X
                                    )
        self.prop_context_var = tk.StringVar(value="Container: None")
        tk.Label(self.prop_frame, textvariable=self.prop_context_var,
                 fg=colors["muted_fg"], bg=colors["panel_bg"], anchor="w"
                 ).pack(anchor=tk.W, padx=6, pady=(0, 5),
                         fill=tk.X
                         )

        self.prop_scrollable = _VScrollFrame(self.prop_frame,
                                              bg=colors["panel_bg"]
                                              )
        self.prop_scrollable.pack(fill=tk.BOTH, expand=True)
        prop_rows_parent = self.prop_scrollable.inner

        self.prop_rows = []
        for i in range(20):
            frame = tk.Frame(prop_rows_parent, bg=colors["panel_bg"])
            lbl = tk.Label(frame, text="", width=13, anchor="w",
                           bg=colors["panel_bg"], fg=colors["panel_fg"
                                                         ])
            lbl.pack(side=tk.LEFT, padx=(2, 4))
            control_frame = tk.Frame(frame, bg=colors["panel_bg"])
            control_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.prop_rows.append({
                "frame": frame, "label": lbl, "control_frame": control_frame,
                "widget": None, "visible": False,
                "_shape": None, "_trace_id": None, "_combo_widget": None,
            }
            )