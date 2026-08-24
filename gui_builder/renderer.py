"""Canvas rendering responsibilities."""
from .dependencies import *
from .config import *
from .models import DesignElement

class CanvasRenderer:
    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self.zoom = 1.0

    def _scaled_font(self, font):
        z = getattr(self, "zoom", 1.0)
        if z == 1.0:
            return font
        if isinstance(font, (tuple, list)) and len(font) >= 2:
            try:
                size = int(round(abs(float(font[1])) * z)) or 1
                return (font[0], size) + tuple(font[2:])
            except (ValueError, TypeError):
                return font
        return font

    def _get_valid_color(self, color_name: str, fallback: str) -> str:
        if not color_name:
            return fallback
        try:
            self.canvas.winfo_rgb(color_name)
            return color_name
        except tk.TclError:
            return fallback

    def draw_grid(self, width: int, height: int) -> None:
        self.canvas.delete("grid")
        z = getattr(self, "zoom", 1.0)
        sw, sh = int(width * z), int(height * z)
        step = max(4, int(round(20 * z)))
        for x in range(0, sw + 1, step):
            self.canvas.create_line(x, 0, x, sh, fill="#E8E8E8",
                                     tags="grid"
                                     )
        for y in range(0, sh + 1, step):
            self.canvas.create_line(0, y, sw, y, fill="#E8E8E8",
                                     tags="grid"
                                     )
        self.canvas.tag_lower("grid")

    def draw_element(self, elem: DesignElement) -> None:
        z = getattr(self, "zoom", 1.0)
        x, y, w, h = int(elem.x * z), int(elem.y * z), int(
            elem.canvas_w * z
            ), int(elem.canvas_h * z)
        bg = self._get_valid_color(elem.props.get("bg"),
                                    ELEMENT_TYPES[elem.elem_type]["tile_bg"]
                                    )
        fg = self._get_valid_color(elem.props.get("fg"),
                                    ELEMENT_TYPES[elem.elem_type]["tile_fg"]
                                    )
        font = self._scaled_font(elem.props.get("font") or ("Segoe UI", 9))
        outline = "#FF6B35" if elem.selected else "#B0BEC5"
        width_outline = 2 if elem.selected else 1

        self.erase_element(elem)

        draw_func = getattr(self, f"_draw_{elem.elem_type.lower()}",
                             self._draw_fallback
                             )
        draw_func(elem, x, y, w, h, bg, fg, font, outline, width_outline)

        # The design canvas always shows every element regardless of its
        # Visible property (you need to be able to select/edit it either
        # way) -- but a dashed outline + small badge here makes it obvious
        # at a glance which ones won't actually appear when the exported
        # app starts (see CodeGenerator._is_visible / _place_line for the
        # runtime behavior).
        if str(elem.props.get("visible", "yes")).strip().lower() in (
                "no", "0", "false"
        ):
            self.canvas.create_rectangle(
                x, y, x + w, y + h, outline="#9E9E9E", width=2,
                dash=(4, 3), tags=("element", f"elem_{elem.elem_id}")
                )
            badge_w, badge_h = 48, 14
            bx, by = x + max(0, w - badge_w), y + max(0, h - badge_h)
            self.canvas.create_rectangle(
                bx, by, bx + badge_w, by + badge_h, fill="#616161",
                outline="", tags=("element", f"elem_{elem.elem_id}")
                )
            self.canvas.create_text(
                bx + badge_w / 2, by + badge_h / 2, text="HIDDEN",
                fill="white", font=("Segoe UI", 6, "bold"),
                tags=("element", f"elem_{elem.elem_id}")
                )

        elem.handle_ids = {}
        if elem.selected:
            mx, my = x + w // 2, y + h // 2
            handle_pts = {
                "NW": (x, y), "N": (mx, y), "NE": (x + w, y), "E": (x + w, my),
                "SE": (x + w, y + h), "S": (mx, y + h), "SW": (x, y + h),
                "W": (x, my),
            }
            for name, (hx, hy) in handle_pts.items():
                hid = self.canvas.create_rectangle(
                    hx - HANDLE_HALF, hy - HANDLE_HALF, hx + HANDLE_HALF,
                    hy + HANDLE_HALF,
                    fill="#FF6B35", outline="#FFFFFF", width=2,
                    tags=("handle", f"handle_{elem.elem_id}_{name}")
                )
                elem.handle_ids[name] = hid

            del_x, del_y = x + w + 15, y - 15
            hid_bg = self.canvas.create_rectangle(del_x - 9, del_y - 9,
                                                   del_x + 9, del_y + 9,
                                                   fill="#E53935",
                                                   outline="#FFFFFF",
                                                   width=2, tags=("handle",
                                                                  f"del_{elem.elem_id}")
                                                   )
            hid_l1 = self.canvas.create_line(del_x - 4, del_y - 4, del_x + 4,
                                              del_y + 4, fill="white",
                                              width=2, tags=("handle",
                                                             f"del_{elem.elem_id}")
                                             )
            hid_l2 = self.canvas.create_line(del_x - 4, del_y + 4, del_x + 4,
                                              del_y - 4, fill="white",
                                              width=2, tags=("handle",
                                                             f"del_{elem.elem_id}")
                                             )
            elem.handle_ids["DEL"] = hid_bg
            elem.handle_ids["DEL_L1"] = hid_l1
            elem.handle_ids["DEL_L2"] = hid_l2

            id_lbl_bg = self.canvas.create_rectangle(x + w // 2 - 20, y - 20,
                                                      x + w // 2 + 20, y - 6,
                                                      fill="#1976D2",
                                                      outline="#FFFFFF",
                                                      width=2,
                                                      tags=("handle",
                                                            f"id_{elem.elem_id}")
                                                     )
            id_lbl = self.canvas.create_text(x + w // 2, y - 15,
                                              text=f"ID:{elem.elem_id}",
                                              fill="white",
                                              font=("Segoe UI", 8, "bold"),
                                              tags=("handle",
                                                    f"id_{elem.elem_id}")
                                             )
            elem.handle_ids["ID_BG"] = id_lbl_bg
            elem.handle_ids["ID"] = id_lbl

    def _draw_label(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        justify = elem.props.get("justify", "center")
        anchor_map = {"left": "w", "center": "center", "right": "e"}
        anchor = anchor_map.get(justify, "center")
        self._render_text_on_canvas(elem, x, y, w, h, elem.display_label, fg,
                                     font, anchor=anchor
                                     )

    def _draw_entry(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        text = elem.props.get("textvariable") or elem.display_label
        self._render_text_on_canvas(elem, x + 4, y, w - 8, h, text, fg, font,
                                     anchor="w"
                                     )

    def _draw_button(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        self._render_text_on_canvas(elem, x, y, w, h, elem.display_label, fg,
                                     font
                                     )

    def _draw_radiobutton(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        cx = x + 20
        cy = y + h // 2
        r = 6
        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                 outline="#757575", fill=bg,
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )
        if elem.props.get("value") == 1:
            self.canvas.create_oval(cx - 3, cy - 3, cx + 3, cy + 3,
                                     fill="#1976D2",
                                     tags=("element", f"elem_{elem.elem_id}")
                                     )
        self._render_text_on_canvas(elem, x + 25, y, w - 25, h,
                                     elem.display_label, fg, font, anchor="w"
                                     )

    def _draw_checkbutton(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        cx = x + 16
        cy = y + h // 2
        size = 10
        self.canvas.create_rectangle(cx - size // 2, cy - size // 2,
                                      cx + size // 2, cy + size // 2,
                                      outline="#757575", fill=bg,
                                      tags=("element", f"elem_{elem.elem_id}")
                                     )
        if elem.props.get("onvalue") == 1:
            self.canvas.create_line(cx - 3, cy, cx, cy + 3, cx + 5, cy - 4,
                                     fill="#1976D2", width=2,
                                     tags=("element", f"elem_{elem.elem_id}")
                                     )
        self._render_text_on_canvas(elem, x + 25, y, w - 25, h,
                                     elem.display_label, fg, font, anchor="w"
                                     )

    def _draw_scale(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        track_y = y + h // 2
        track_len = w - 20
        self.canvas.create_line(x + 10, track_y, x + 10 + track_len, track_y,
                                 fill="#B0BEC5", width=4,
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )
        thumb_x = x + 10 + int(track_len * 0.3)
        self.canvas.create_oval(thumb_x - 6, track_y - 6, thumb_x + 6,
                                 track_y + 6, fill="#1976D2",
                                 outline="#1976D2",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )
        val = elem.props.get("to", 100) * 0.3
        self.canvas.create_text(x + w - 5, track_y - 10,
                                 text=str(int(val)), anchor="e",
                                 fill="#212121",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )

    def _draw_combobox(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        arrow_x = x + w - 18
        arrow_y = y + h // 2
        self.canvas.create_polygon(arrow_x - 5, arrow_y - 4, arrow_x + 5,
                                    arrow_y - 4, arrow_x, arrow_y + 4,
                                    fill="#757575",
                                    tags=("element", f"elem_{elem.elem_id}")
                                    )
        self._render_text_on_canvas(elem, x + 4, y, w - 22, h,
                                     elem.display_label, fg, font, anchor="w"
                                     )

    def _draw_spinbox(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        arrow_x = x + w - 16
        arrow_y = y + h // 2
        self.canvas.create_polygon(arrow_x - 6, arrow_y - 2, arrow_x + 6,
                                    arrow_y - 2, arrow_x, arrow_y - 8,
                                    fill="#757575",
                                    tags=("element", f"elem_{elem.elem_id}")
                                    )
        self.canvas.create_polygon(arrow_x - 6, arrow_y + 2, arrow_x + 6,
                                    arrow_y + 2, arrow_x, arrow_y + 8,
                                    fill="#757575",
                                    tags=("element", f"elem_{elem.elem_id}")
                                    )
        self._render_text_on_canvas(elem, x + 4, y, w - 20, h,
                                     elem.display_label, fg, font, anchor="w"
                                     )

    def _draw_listbox(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        for i in range(3):
            line_y = y + 12 + i * 20
            if line_y < y + h - 5:
                self.canvas.create_line(x + 5, line_y, x + w - 5, line_y,
                                         fill="#E0E0E0", tags=("element",
                                                               f"elem_{elem.elem_id}")
                                         )

    def _draw_text(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        for i in range(min(max(1, h // 22), 8)):
            line_y = y + 15 + i * 22
            if line_y < y + h - 5:
                self.canvas.create_line(x + 5, line_y, x + w - 5, line_y,
                                         fill="#E0E0E0", tags=("element",
                                                               f"elem_{elem.elem_id}")
                                         )

    def _draw_canvas(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        self.canvas.create_rectangle(x + 10, y + 10, x + w - 10, y + h - 10,
                                      outline="#B0BEC5",
                                      tags=("element", f"elem_{elem.elem_id}")
                                      )
        self.canvas.create_line(x + 15, y + 15, x + w - 15, y + h - 15,
                                 fill="#B0BEC5",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )

    def _draw_progressbar(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        value = elem.props.get("value", 40)
        max_val = elem.props.get("maximum", 100)
        orient = elem.props.get("orient", "horizontal")
        frac = min(1.0, max(0, value / max_val))
        if orient == "vertical":
            bar_h = int((h - 4) * frac)
            self.canvas.create_rectangle(x + 2, y + h - 2 - bar_h, x + w - 2,
                                          y + h - 2, fill="#1976D2",
                                          outline="", tags=("element",
                                                            f"elem_{elem.elem_id}")
                                          )
        else:
            bar_w = int((w - 4) * frac)
            self.canvas.create_rectangle(x + 2, y + 2, x + 2 + bar_w,
                                          y + h - 2, fill="#1976D2",
                                          outline="", tags=("element",
                                                            f"elem_{elem.elem_id}")
                                          )

    def _draw_scrollbar(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        slider_h = h // 3
        slider_y = y + (h - slider_h) // 2
        self.canvas.create_rectangle(x + 2, slider_y, x + w - 2,
                                      slider_y + slider_h, fill="#B0BEC5",
                                      outline="#78909C",
                                      tags=("element", f"elem_{elem.elem_id}")
                                      )

    def _draw_frame(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        relief = elem.props.get("relief", "groove")
        if relief == "groove":
            self._draw_groove_rect(elem, x, y, w, h, bg, outline, outline_w)
        elif relief == "raised":
            self._draw_raised_rect(elem, x, y, w, h, bg, outline, outline_w)
        elif relief == "sunken":
            self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        else:
            self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)

    def _draw_labelframe(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_groove_rect(elem, x, y, w, h, bg, outline, outline_w)
        text = elem.props.get("text", "LabelFrame")
        self.canvas.create_rectangle(x + 10, y - 6,
                                      x + min(w - 10, 10 + len(text) * 8),
                                      y + 6, fill=bg, outline="",
                                      tags=("element", f"elem_{elem.elem_id}")
                                      )
        self.canvas.create_text(x + 14, y, text=text, fill=fg, font=font,
                                 anchor="w",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )

    def _draw_notebook(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        self.canvas.create_rectangle(x, y + 26, x + w, y + h, fill=bg,
                                      outline="#B0BEC5",
                                      tags=("element", f"elem_{elem.elem_id}")
                                      )
        tabs = elem.props.get("tabs", ["Tab 1", "Tab 2"]) or ["Tab 1"]
        active = int(elem.props.get("active_tab", 0) or 0)
        active = max(0, min(active, len(tabs) - 1))
        tab_width = max(58, min(120, int(
            (w - 10) / max(1, min(len(tabs), 4))
            )
                                  )
                         )
        tab_x = x + 5
        for i, title in enumerate(tabs):
            if tab_x >= x + w - 4:
                break
            tw = min(tab_width, x + w - 4 - tab_x)
            fill = "#FFFFFF" if i == active else "#F5F5F5"
            text_fill = "#1976D2" if i == active else "#757575"
            self.canvas.create_rectangle(tab_x, y + 4, tab_x + tw, y + 26,
                                          fill=fill, outline="#B0BEC5",
                                          tags=("element",
                                                f"elem_{elem.elem_id}")
                                          )
            self.canvas.create_text(tab_x + tw / 2, y + 15,
                                     text=str(title), fill=text_fill,
                                     font=font,
                                     tags=("element", f"elem_{elem.elem_id}")
                                     )
            tab_x += tw + 3

    def _draw_panedwindow(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_groove_rect(elem, x, y, w, h, bg, outline, outline_w)
        orient = elem.props.get("orient", "horizontal")
        if orient == "vertical":
            sash_y = y + h // 2
            self.canvas.create_line(x + 10, sash_y, x + w - 10, sash_y,
                                     fill="#B0BEC5", width=2,
                                     tags=("element", f"elem_{elem.elem_id}")
                                     )
        else:
            sash_x = x + w // 2
            self.canvas.create_line(sash_x, y + 10, sash_x, y + h - 10,
                                     fill="#B0BEC5", width=2,
                                     tags=("element", f"elem_{elem.elem_id}")
                                     )

    def _draw_separator(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        orient = elem.props.get("orient", "horizontal")
        if orient == "vertical":
            self.canvas.create_line(x + w // 2, y, x + w // 2, y + h,
                                     fill="#B0BEC5", width=2,
                                     tags=("element", f"elem_{elem.elem_id}")
                                     )
        else:
            self.canvas.create_line(x, y + h // 2, x + w, y + h // 2,
                                     fill="#B0BEC5", width=2,
                                     tags=("element", f"elem_{elem.elem_id}")
                                     )

    def _draw_table(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        cols = elem.props.get("columns", "")
        if cols:
            columns = [c.strip() for c in cols.split(",") if c.strip()]
        else:
            columns = ["A", "B", "C"]
        n_cols = max(1, len(columns))
        col_w = w / n_cols
        row_h = 24
        self.canvas.create_rectangle(x, y, x + w, y + row_h, fill="#E3F2FD",
                                      outline="#B0BEC5",
                                      tags=("element", f"elem_{elem.elem_id}")
                                      )
        for i, col in enumerate(columns):
            self.canvas.create_line(x + (i + 1) * col_w, y,
                                     x + (i + 1) * col_w, y + row_h,
                                     fill="#B0BEC5",
                                     tags=("element", f"elem_{elem.elem_id}")
                                     )
            self.canvas.create_text(x + i * col_w + col_w / 2, y + row_h / 2,
                                     text=col, fill="#1976D2", font=font,
                                     tags=("element", f"elem_{elem.elem_id}")
                                     )
        rows = min(5, max(0, int(h - row_h) // 20))
        for r in range(rows):
            ry = y + row_h + r * 20
            self.canvas.create_rectangle(x, ry, x + w, ry + 20,
                                          outline="#E0E0E0",
                                          tags=("element",
                                                f"elem_{elem.elem_id}")
                                          )

    def _load_thumbnail(self, elem: DesignElement, path: str, w: int, h: int):
        """Load (and cache on the element) a canvas-ready PhotoImage for an
        Image element's configured file, or None if it can't be shown --
        no path set, Pillow isn't installed, or the file failed to load.
        The element holds the last PhotoImage in its own _image_tk field
        (see models.DesignElement) so Tk doesn't garbage-collect it out
        from under the canvas the moment this method returns.
        """
        if not path or not PIL_AVAILABLE:
            elem._image_tk = None
            elem._image_cache_key = None
            return None
        full_path = path if os.path.isabs(path) else os.path.join(BASE_DIR,
                                                                    path)
        cache_key = (full_path, w, h)
        if (getattr(elem, "_image_cache_key", None) == cache_key
                and elem._image_tk is not None):
            return elem._image_tk
        try:
            img = PILImage.open(full_path)
            img = img.convert("RGBA")
            target_w = max(1, int(round(float(w) - 8)))
            target_h = max(1, int(round(float(h) - 8)))
            keep_aspect = str(elem.props.get("keep_aspect", 1)) not in (
                "0", "False", "false", ""
            )
            if keep_aspect:
                img.thumbnail((target_w, target_h))
            else:
                img = img.resize((target_w, target_h), PILImage.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
        except Exception:
            elem._image_tk = None
            elem._image_cache_key = None
            return None
        elem._image_tk = photo
        elem._image_cache_key = cache_key
        return photo

    def _draw_image(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        path = elem.props.get("image_path", "")
        photo = self._load_thumbnail(elem, path, w, h)
        if photo is not None:
            self.canvas.create_image(
                x + w // 2, y + h // 2, image=photo,
                tags=("element", f"elem_{elem.elem_id}")
                )
            return

        # No usable image (nothing picked yet, Pillow missing, or the file
        # couldn't be loaded) -- draw a simple picture-frame glyph instead
        # of leaving the element looking broken/empty on the canvas.
        self.canvas.create_rectangle(
            x + 14, y + 14, x + w - 14, y + h - 14, outline="#B0BEC5",
            width=2, tags=("element", f"elem_{elem.elem_id}")
            )
        self.canvas.create_oval(
            x + 22, y + 22, x + 36, y + 36, outline="#B0BEC5", width=2,
            tags=("element", f"elem_{elem.elem_id}")
            )
        self.canvas.create_line(
            x + 18, y + h - 22, x + w * 0.42, y + h * 0.48,
            x + w * 0.62, y + h * 0.62, x + w - 18, y + h - 22,
            fill="#B0BEC5", width=2, smooth=True,
            tags=("element", f"elem_{elem.elem_id}")
            )
        if not path:
            label = "No image set"
        elif not PIL_AVAILABLE:
            label = "Pillow not installed"
        else:
            label = "Image not found"
        self.canvas.create_text(
            x + w // 2, y + h - 8, text=label, fill="#757575",
            font=("Segoe UI", 8), tags=("element", f"elem_{elem.elem_id}")
            )

    def _draw_calendar(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)

        initial = str(elem.props.get("initial_date", "") or "").strip()
        try:
            d = datetime.strptime(initial, "%Y-%m-%d") if initial else datetime.now()
        except (ValueError, TypeError):
            d = datetime.now()

        header_h = min(22, h * 0.2)
        self.canvas.create_rectangle(
            x, y, x + w, y + header_h, fill="#1976D2", outline="",
            tags=("element", f"elem_{elem.elem_id}")
            )
        self.canvas.create_text(
            x + w / 2, y + header_h / 2, text=d.strftime("%B %Y"),
            fill="white", font=("Segoe UI", 9, "bold"),
            tags=("element", f"elem_{elem.elem_id}")
            )

        weekdays = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        col_w = w / 7
        wd_y = y + header_h + 9
        for i, wd in enumerate(weekdays):
            self.canvas.create_text(
                x + i * col_w + col_w / 2, wd_y, text=wd, fill="#757575",
                font=("Segoe UI", 7, "bold"),
                tags=("element", f"elem_{elem.elem_id}")
                )

        first_of_month = d.replace(day=1)
        start_weekday = first_of_month.weekday()  # Monday = 0
        days_in_month = calendar.monthrange(d.year, d.month)[1]
        grid_top = wd_y + 10
        row_h = max(10, (y + h - grid_top - 4) / 6)

        row, col = 0, start_weekday
        for day in range(1, days_in_month + 1):
            cx = x + col * col_w + col_w / 2
            cy = grid_top + row * row_h + row_h / 2
            if cy <= y + h - 4:
                if day == d.day:
                    r = min(col_w, row_h) * 0.38
                    self.canvas.create_oval(
                        cx - r, cy - r, cx + r, cy + r, fill="#1976D2",
                        outline="", tags=("element", f"elem_{elem.elem_id}")
                        )
                    txt_fill = "white"
                else:
                    txt_fill = "#212121"
                self.canvas.create_text(
                    cx, cy, text=str(day), fill=txt_fill,
                    font=("Segoe UI", 7),
                    tags=("element", f"elem_{elem.elem_id}")
                    )
            col += 1
            if col > 6:
                col = 0
                row += 1

    def _draw_fallback(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        self._render_text_on_canvas(elem, x, y, w, h, elem.display_label, fg,
                                     font
                                     )

    def _draw_flat_rect(self, elem, x, y, w, h, fill, outline, outline_w):
        elem.rect_id = self.canvas.create_rectangle(
            x, y, x + w, y + h, fill=fill, outline=outline,
            width=outline_w,
            tags=("element", f"elem_{elem.elem_id}")
        )

    def _draw_sunken_rect(self, elem, x, y, w, h, fill, outline, outline_w):
        self.canvas.create_rectangle(x, y, x + w, y + h, fill=fill,
                                      outline=outline, width=outline_w,
                                      tags=("element", f"elem_{elem.elem_id}")
                                      )
        self.canvas.create_line(x + 1, y + 1, x + w - 2, y + 1,
                                 fill="#B0BEC5",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )
        self.canvas.create_line(x + 1, y + 1, x + 1, y + h - 2,
                                 fill="#B0BEC5",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )
        self.canvas.create_line(x + w - 2, y + 2, x + w - 2, y + h - 2,
                                 fill="#FFFFFF",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )
        self.canvas.create_line(x + 2, y + h - 2, x + w - 2, y + h - 2,
                                 fill="#FFFFFF",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )

    def _draw_raised_rect(self, elem, x, y, w, h, fill, outline, outline_w):
        self.canvas.create_rectangle(x, y, x + w, y + h, fill=fill,
                                      outline=outline, width=outline_w,
                                      tags=("element", f"elem_{elem.elem_id}")
                                      )
        self.canvas.create_line(x + 1, y + 1, x + w - 2, y + 1,
                                 fill="#FFFFFF",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )
        self.canvas.create_line(x + 1, y + 1, x + 1, y + h - 2,
                                 fill="#FFFFFF",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )
        self.canvas.create_line(x + w - 2, y + 2, x + w - 2, y + h - 2,
                                 fill="#B0BEC5",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )
        self.canvas.create_line(x + 2, y + h - 2, x + w - 2, y + h - 2,
                                 fill="#B0BEC5",
                                 tags=("element", f"elem_{elem.elem_id}")
                                 )

    def _draw_groove_rect(self, elem, x, y, w, h, fill, outline, outline_w):
        self.canvas.create_rectangle(x, y, x + w, y + h, fill=fill,
                                      outline=outline, width=outline_w,
                                      tags=("element", f"elem_{elem.elem_id}")
                                      )
        self.canvas.create_rectangle(x + 2, y + 2, x + w - 2, y + h - 2,
                                      outline="#B0BEC5", width=1,
                                      tags=("element", f"elem_{elem.elem_id}")
                                      )

    def _render_text_on_canvas(
            self, elem, x, y, w, h, text, color, font, anchor="center"
            ):
        if anchor == "center":
            elem.text_id = self.canvas.create_text(
                x + w // 2, y + h // 2, text=text, fill=color, font=font,
                tags=("element", f"elem_{elem.elem_id}")
            )
        elif anchor == "w":
            elem.text_id = self.canvas.create_text(
                x + 2, y + h // 2, text=text, fill=color, font=font,
                anchor="w",
                tags=("element", f"elem_{elem.elem_id}")
            )
        elif anchor == "e":
            elem.text_id = self.canvas.create_text(
                x + w - 2, y + h // 2, text=text, fill=color, font=font,
                anchor="e",
                tags=("element", f"elem_{elem.elem_id}")
            )

    def erase_element(self, elem: DesignElement) -> None:
        self.canvas.delete(f"elem_{elem.elem_id}")
        for hid in elem.handle_ids.values():
            self.canvas.delete(hid)
        elem.rect_id = 0
        elem.text_id = 0
        elem.handle_ids = {}

    def redraw_element(self, elem: DesignElement) -> None:
        self.erase_element(elem)
        self.draw_element(elem)

    def move_element(self, elem: DesignElement, dx: int, dy: int) -> None:
        """Translate an already-drawn element's existing canvas items in
        place, instead of erasing and recreating them. Used during
        interactive dragging so a mouse-move doesn't pay the cost of
        color/font revalidation and widget-specific shape reconstruction
        on every event. Safe because a pure move never changes size, text,
        or color — only position — so the existing items remain correct,
        just shifted. dx/dy are in logical (unzoomed) canvas units.
        """
        if dx == 0 and dy == 0:
            return
        z = getattr(self, "zoom", 1.0)
        sdx, sdy = dx * z, dy * z
        self.canvas.move(f"elem_{elem.elem_id}", sdx, sdy)
        for hid in elem.handle_ids.values():
            self.canvas.move(hid, sdx, sdy)

    def snap_to_grid(self, x: int, y: int) -> Tuple[int, int]:
        return int(round(x / GRID_SIZE) * GRID_SIZE), int(
            round(y / GRID_SIZE) * GRID_SIZE
            )