"""Canvas rendering responsibilities."""
from .dependencies import *
from .config import *
from .models import DesignElement

class CanvasRenderer:
    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self.zoom = 1.0

    def _image_path(self, path):
        path=str(path or "").strip()
        return path if os.path.isabs(path) else os.path.join(BASE_DIR,path) if path else ""

    def _load_background_image(self, elem, path, w, h):
        if not path or not PIL_AVAILABLE: return None
        full=self._image_path(path); mode=str(elem.props.get("image_mode","Fit")).lower(); anchor=str(elem.props.get("image_anchor","Center")).lower()
        key=(full,int(w),int(h),mode,anchor); cache=getattr(elem,"_image_bg_cache",None)
        if cache and cache[0]==key: return cache[1]
        try:
            img=PILImage.open(full).convert("RGBA"); tw=max(1,int(w)); th=max(1,int(h)); iw,ih=img.size; ox=oy=0
            if mode=="stretch": img=img.resize((tw,th),PILImage.Resampling.LANCZOS)
            elif mode in ("fill","cover"):
                sc=max(tw/iw,th/ih); nw=max(1,int(iw*sc)); nh=max(1,int(ih*sc)); img=img.resize((nw,nh),PILImage.Resampling.LANCZOS); l=max(0,(nw-tw)//2); t=max(0,(nh-th)//2); img=img.crop((l,t,l+tw,t+th))
            elif mode in ("fit","contain"):
                sc=min(tw/iw,th/ih); nw=max(1,int(iw*sc)); nh=max(1,int(ih*sc)); img=img.resize((nw,nh),PILImage.Resampling.LANCZOS); ox=(tw-nw)//2; oy=(th-nh)//2
            elif mode in ("tile","repeat"):
                base=PILImage.new("RGBA",(tw,th),(0,0,0,0))
                for yy in range(0,th,img.height):
                    for xx in range(0,tw,img.width): base.alpha_composite(img,(xx,yy))
                img=base
            else:
                spots={"top-left":(0,0),"top":((tw-img.width)//2,0),"top-right":(tw-img.width,0),"left":(0,(th-img.height)//2),"center":((tw-img.width)//2,(th-img.height)//2),"right":(tw-img.width,(th-img.height)//2),"bottom-left":(0,th-img.height),"bottom":((tw-img.width)//2,th-img.height),"bottom-right":(tw-img.width,th-img.height)}
                ox,oy=spots.get(anchor,spots["center"])
                if img.width>tw or img.height>th:
                    l=max(0,min(img.width-tw,-ox)); t=max(0,min(img.height-th,-oy)); img=img.crop((l,t,l+min(tw,img.width),t+min(th,img.height))); ox=oy=0
            photo=ImageTk.PhotoImage(img); elem._image_bg_cache=(key,photo,ox,oy); return photo
        except Exception:
            elem._image_bg_cache=None; return None

    def _draw_background_image(self, elem, x, y, w, h):
        path=elem.props.get("image_path","")
        if not path: return
        photo=self._load_background_image(elem,path,w,h)
        if photo is None: return
        c=getattr(elem,"_image_bg_cache",None); ox,oy=(c[2],c[3]) if c else (0,0)
        self.canvas.create_image(x+ox,y+oy,image=photo,anchor="nw",tags=("element",f"elem_{elem.elem_id}","background_image"))

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

    def _apply_brightness(self, color_name, brightness):
        text = str(color_name or "")
        if len(text) == 7 and text.startswith("#"):
            try:
                factor = max(0.0, min(100.0, float(brightness))) / 100.0
                rgb = [int(text[i:i+2], 16) for i in (1, 3, 5)]
                rgb = [max(0, min(255, int(round(v * factor)))) for v in rgb]
                return "#%02X%02X%02X" % tuple(rgb)
            except (TypeError, ValueError):
                pass
        return text

    def draw_canvas_background(self, path, mode="Fit", anchor="Center", width=1, height=1):
        self.canvas.delete("canvas_background")
        if not path or not PIL_AVAILABLE: return
        class _CanvasProxy: pass
        proxy=_CanvasProxy(); proxy.props={"image_mode":mode,"image_anchor":anchor}; proxy._image_bg_cache=None
        z=max(0.01, float(getattr(self, "zoom", 1.0)))
        draw_w=max(1, int(round(float(width) * z)))
        draw_h=max(1, int(round(float(height) * z)))
        photo=self._load_background_image(proxy,path,draw_w,draw_h)
        if photo is None: return
        c=proxy._image_bg_cache; self._canvas_bg_ref=photo
        self.canvas.create_image(c[2],c[3],image=photo,anchor="nw",tags=("canvas_background",))
        # Layer order: surface < background image < elements < border.
        self.canvas.tag_lower("canvas_background")
        self.canvas.tag_raise("canvas_background", "canvas_surface")
        self.canvas.tag_raise("canvas_border")

    def draw_canvas_border(self, width: float, height: float) -> None:
        self.canvas.delete("canvas_border")
        z = getattr(self, "zoom", 1.0)
        w, h = int(width * z), int(height * z)
        if w < 2 or h < 2:
            return
        self.canvas.create_rectangle(1, 1, max(1, w - 1), max(1, h - 1), outline="#607D8B", width=2, tags="canvas_border")
        self.canvas.tag_raise("canvas_border")

    def draw_canvas_surface(self, width: float, height: float, color: str) -> None:
        self.canvas.delete("canvas_surface")
        z=getattr(self, "zoom", 1.0)
        self.canvas.create_rectangle(0,0,int(width*z),int(height*z),fill=color,outline="",tags=("canvas_surface",))
        self.canvas.tag_lower("canvas_surface")

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
        self._draw_background_image(elem,x,y,w,h)

        draw_method_name = f"_draw_{elem.elem_type.lower()}"
        if elem.elem_type == "RadioButton":
            # The legacy "Radiobutton" element retains its existing renderer;
            # the new RadioButton element uses the richer square/round renderer.
            draw_method_name = "_draw_radiobuttonplus"
        draw_func = getattr(self, draw_method_name, self._draw_fallback)
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
        bw = self._configured_border_width(elem, outline_w)
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, bw)
        justify = elem.props.get("justify", "center")
        anchor_map = {"left": "w", "center": "center", "right": "e"}
        anchor = anchor_map.get(justify, "center")
        self._render_text_on_canvas(elem, x, y, w, h, elem.display_label, fg,
                                     font, anchor=anchor
                                     )

    def _draw_linklabel(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        # A LinkLabel is a Label that reads as clickable: no border chrome,
        # left-aligned text in the configured (by default blue/underlined)
        # font/color -- the same visual cue a WinForms LinkLabel gives.
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, 0)
        self._render_text_on_canvas(elem, x + 2, y, w - 4, h,
                                     elem.display_label, fg, font, anchor="w"
                                     )

    def _draw_statusbar(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        # Docked bottom bar: sunken bevel, left-aligned text -- the usual
        # look for an application status bar. No background-image support
        # is offered for this element (see config.py's per-type exclusion).
        bw = self._configured_border_width(elem, outline_w)
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, bw)
        self._render_text_on_canvas(elem, x + 6, y, w - 12, h,
                                     elem.display_label, fg, font, anchor="w"
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

    _SEGMENTS = {
        "0": "abcdef", "1": "bc", "2": "abdeg", "3": "abcdg",
        "4": "bcfg", "5": "acdfg", "6": "acdefg", "7": "abc",
        "8": "abcdefg", "9": "abcdfg", "-": "g", " ": "",
    }

    def _draw_pushbutton(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        shape = str(elem.props.get("shape", "Square")).strip().lower()
        style = str(elem.props.get("style", "Mechanical")).strip().lower()
        active = str(elem.props.get("default_state", "Off")).strip().lower() in ("on", "yes", "1", "true")
        fill = self._get_valid_color(
            elem.props.get("active_bg") if active else bg,
            bg if not active else "#0D47A1"
        )
        if shape == "round":
            self.canvas.create_oval(
                x + 2, y + 2, x + w - 2, y + h - 2,
                fill=fill, outline=outline, width=outline_w,
                tags=("element", f"elem_{elem.elem_id}")
            )
            self.canvas.create_oval(
                x + 7, y + 7, x + w - 7, y + h - 7,
                outline="#FFFFFF", width=1,
                tags=("element", f"elem_{elem.elem_id}")
            )
        elif style == "mechanical":
            self._draw_raised_rect(elem, x, y, w, h, fill, outline, outline_w)
            if not active:
                self.canvas.create_line(x + 4, y + 3, x + w - 5, y + 3,
                                        fill="#FFFFFF", width=1,
                                        tags=("element", f"elem_{elem.elem_id}"))
        else:
            self._draw_flat_rect(elem, x, y, w, h, fill, outline, outline_w)
        self._render_text_on_canvas(elem, x, y, w, h, elem.display_label, fg, font)

    def _draw_radiobuttonplus(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        cx, cy = x + 13, y + h // 2
        selected = str(elem.props.get("selected", "No")).strip().lower() in ("yes", "1", "true")
        shape = str(elem.props.get("shape", "Round")).strip().lower()
        active_bg = self._get_valid_color(elem.props.get("active_bg"), "#1976D2")
        if shape == "square":
            self.canvas.create_rectangle(cx - 7, cy - 7, cx + 7, cy + 7,
                                          outline="#777777", fill=bg, width=1,
                                          tags=("element", f"elem_{elem.elem_id}"))
            if selected:
                self.canvas.create_rectangle(cx - 4, cy - 4, cx + 4, cy + 4,
                                              fill=active_bg, outline=active_bg,
                                              tags=("element", f"elem_{elem.elem_id}"))
        else:
            self.canvas.create_oval(cx - 7, cy - 7, cx + 7, cy + 7,
                                    outline="#777777", fill=bg, width=1,
                                    tags=("element", f"elem_{elem.elem_id}"))
            if selected:
                self.canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4,
                                        fill=active_bg, outline=active_bg,
                                        tags=("element", f"elem_{elem.elem_id}"))
        self._render_text_on_canvas(elem, x + 25, y, w - 25, h,
                                    elem.display_label, fg, font, anchor="w")

    def _draw_leddigit(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_leddisplay_common(elem, x, y, w, h, bg, outline, outline_w, digits=1)

    def _draw_leddisplay(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        try:
            digits = max(1, int(elem.props.get("digits", 3) or 3))
        except (TypeError, ValueError):
            digits = 3
        self._draw_leddisplay_common(elem, x, y, w, h, bg, outline, outline_w, digits=digits)

    def _draw_leddisplay_common(self, elem, x, y, w, h, bg, outline, outline_w, digits=1):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        value = str(elem.props.get("value", "0")).strip()
        try:
            decimal_places = max(0, int(elem.props.get("decimal_places", 0) or 0))
        except (TypeError, ValueError):
            decimal_places = 0
        if decimal_places > 0:
            try:
                value = f"{float(value):.{decimal_places}f}"
            except (TypeError, ValueError):
                pass
        if elem.elem_type == "LEDDigit":
            chars = [(value[-1:] or "0", False)]
        else:
            negative = value.startswith("-")
            sign = "-" if negative else ""
            raw = value[1:] if negative else value
            raw_digits = [ch for ch in raw if ch.isdigit()]
            leading = str(elem.props.get("leading_zeros", "No")).strip().lower() in ("yes", "1", "true")
            if leading and raw_digits:
                raw_digits = list(("".join(raw_digits)).zfill(max(1, digits - (1 if negative else 0))))
            else:
                raw_digits = raw_digits[-digits:]
            if not raw_digits:
                raw_digits = ["0"]
            decimals = set()
            di = 0
            for ch in raw:
                if ch == "." and di > 0:
                    decimals.add(di - 1)
                elif ch.isdigit():
                    di += 1
            chars = []
            if sign:
                chars.append(("-", False))
            chars.extend((d, i in decimals) for i, d in enumerate(raw_digits))

        led_color = self._apply_brightness(
            self._get_valid_color(elem.props.get("color"), "#00FF66"),
            elem.props.get("brightness", 100)
        )
        off_color = self._get_valid_color(elem.props.get("off_color"), "#16351F")
        try:
            gap = max(0, int(elem.props.get("digit_gap", 12) or 12))
        except (TypeError, ValueError):
            gap = 12
        margin = max(3, int(min(w, h) * 0.06))
        # Keep each digit at a stable seven-segment aspect ratio. The designer
        # therefore previews the same physical proportions used by the runtime
        # widget instead of stretching one digit across the entire element.
        digit_h = max(12, h - 2 * margin)
        digit_w = max(8, int(round(digit_h * 0.62)))
        slot_count = max(1, len(chars))
        required_w = slot_count * digit_w + max(0, slot_count - 1) * gap
        available_w = max(1, w - 2 * margin)
        if required_w > available_w and slot_count > 1:
            gap = max(1, int((available_w - slot_count * digit_w) / max(1, slot_count - 1)))
            required_w = slot_count * digit_w + max(0, slot_count - 1) * gap
        if required_w > available_w:
            scale = available_w / float(required_w)
            digit_w = max(8, int(digit_w * scale))
            digit_h = max(12, int(digit_h * scale))
            gap = max(1, int(gap * scale)) if slot_count > 1 else 0
            required_w = slot_count * digit_w + max(0, slot_count - 1) * gap
        start_x = x + max(0, (w - required_w) / 2)
        start_y = y + max(0, (h - digit_h) / 2)
        try:
            seg_w = max(1, int(elem.props.get("segment_width", 4) or 4))
        except (TypeError, ValueError):
            seg_w = 4
        for i, (char, has_decimal) in enumerate(chars):
            dx = start_x + i * (digit_w + gap)
            active = self._SEGMENTS.get(char.upper(), "")
            t = max(1, min(seg_w, int(min(digit_w, digit_h) * 0.16)))
            boxes = {
                "a": (dx + t, start_y, dx + digit_w - t, start_y + t),
                "g": (dx + t, start_y + digit_h / 2 - t / 2, dx + digit_w - t, start_y + digit_h / 2 + t / 2),
                "d": (dx + t, start_y + digit_h - t, dx + digit_w - t, start_y + digit_h),
                "f": (dx, start_y + t, dx + t, start_y + digit_h / 2 - t / 2),
                "b": (dx + digit_w - t, start_y + t, dx + digit_w, start_y + digit_h / 2 - t / 2),
                "e": (dx, start_y + digit_h / 2 + t / 2, dx + t, start_y + digit_h - t),
                "c": (dx + digit_w - t, start_y + digit_h / 2 + t / 2, dx + digit_w, start_y + digit_h - t),
            }
            for seg, box in boxes.items():
                color = led_color if seg in active else off_color
                self.canvas.create_rectangle(*box, fill=color, outline=color,
                                              width=max(1, seg_w),
                                              tags=("element", f"elem_{elem.elem_id}"))
            if has_decimal:
                dot_r = max(3.0, min(digit_w, digit_h) * 0.075)
                dot_x = dx + digit_w + gap / 2
                if gap < dot_r * 2.2:
                    dot_x = dx + digit_w - dot_r - 2
                dot_x = min(x + w - dot_r - 1, max(x + dot_r + 1, dot_x))
                dot_y = start_y + digit_h - max(dot_r + 3, digit_h * 0.16)
                self.canvas.create_oval(dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r,
                                        fill=led_color, outline=led_color,
                                        tags=("element", f"elem_{elem.elem_id}"))

    def _draw_ledindicator(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        state = str(elem.props.get("state", "Off")).strip().lower() in ("on", "yes", "1", "true")
        color = self._get_valid_color(
            elem.props.get("on_color") if state else elem.props.get("off_color"),
            "#00FF66" if state else "#16351F"
        )
        if state:
            color = self._apply_brightness(color, elem.props.get("brightness", 100))
        d = max(8, min(w, h) - 4)
        cx, cy = x + w / 2, y + h / 2
        if state and str(elem.props.get("glow", "Yes")).strip().lower() in ("yes", "1", "true"):
            for inset in (0, 3, 5):
                self.canvas.create_oval(cx - d / 2 - inset, cy - d / 2 - inset,
                                        cx + d / 2 + inset, cy + d / 2 + inset,
                                        outline=color, width=1,
                                        tags=("element", f"elem_{elem.elem_id}"))
        shape = str(elem.props.get("shape", "Round")).strip().lower()
        if shape == "square":
            self.canvas.create_rectangle(cx - d / 2, cy - d / 2, cx + d / 2, cy + d / 2,
                                          fill=color, outline="#555555", width=1,
                                          tags=("element", f"elem_{elem.elem_id}"))
        else:
            self.canvas.create_oval(cx - d / 2, cy - d / 2, cx + d / 2, cy + d / 2,
                                    fill=color, outline="#555555", width=1,
                                    tags=("element", f"elem_{elem.elem_id}"))

    def _draw_gauge(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        try:
            mn, mx = float(elem.props.get("min_value", 0)), float(elem.props.get("max_value", 100))
            val = float(elem.props.get("value", 50))
            start = float(elem.props.get("start_angle", 225))
            end = float(elem.props.get("end_angle", -45))
            ticks = max(0, int(elem.props.get("ticks", 10) or 10))
            thickness = max(1, int(elem.props.get("thickness", 8) or 8))
        except (TypeError, ValueError):
            mn, mx, val, start, end, ticks, thickness = 0, 100, 50, 225, -45, 10, 8
        size = max(20, min(w, h) - 20)
        x1, y1 = x + (w - size) / 2, y + (h - size) / 2
        x2, y2 = x1 + size, y1 + size
        track = self._get_valid_color(elem.props.get("track_color"), "#D9D9D9")
        arc = self._get_valid_color(elem.props.get("arc_color"), "#1976D2")
        needle = self._get_valid_color(elem.props.get("needle_color"), "#E53935")
        tick = self._get_valid_color(elem.props.get("tick_color"), "#555555")
        extent = end - start
        self.canvas.create_arc(x1, y1, x2, y2, start=start, extent=extent,
                               style="arc", outline=track, width=thickness,
                               tags=("element", f"elem_{elem.elem_id}"))
        ratio = 0 if mx == mn else max(0, min(1, (val - mn) / (mx - mn)))
        ang = start + ratio * extent
        self.canvas.create_arc(x1, y1, x2, y2, start=start, extent=ang-start,
                               style="arc", outline=arc, width=thickness,
                               tags=("element", f"elem_{elem.elem_id}"))
        cx, cy = x + w / 2, y + h / 2
        import math
        for i in range(ticks + 1):
            r = i / ticks if ticks else 0
            a = start + r * extent
            rad = math.radians(a)
            ro, ri = size / 2 - 2, size / 2 - thickness - 8
            ox, oy = cx + ro * math.cos(rad), cy - ro * math.sin(rad)
            ix, iy = cx + ri * math.cos(rad), cy - ri * math.sin(rad)
            self.canvas.create_line(ix, iy, ox, oy, fill=tick, width=1,
                                    tags=("element", f"elem_{elem.elem_id}"))
        rad = math.radians(ang)
        nl = size / 2 - 15
        nx, ny = cx + nl * math.cos(rad), cy - nl * math.sin(rad)
        self.canvas.create_line(cx, cy, nx, ny, fill=needle, width=max(2, thickness // 2),
                                tags=("element", f"elem_{elem.elem_id}"))
        self.canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill=needle, outline="",
                                tags=("element", f"elem_{elem.elem_id}"))
        if str(elem.props.get("show_value", "Yes")).strip().lower() in ("yes", "1", "true"):
            unit = str(elem.props.get("unit", ""))
            self.canvas.create_text(cx, y + h * 0.80, text=f"{val:g}{unit}",
                                    fill=tick, font=("Segoe UI", 8, "bold"),
                                    tags=("element", f"elem_{elem.elem_id}"))

    def _draw_measurementdisplay(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, outline_w)
        label = str(elem.props.get("label", "Measurement"))
        value = str(elem.props.get("value", "0"))
        unit = str(elem.props.get("unit", ""))
        prefix = str(elem.props.get("prefix", ""))
        suffix = str(elem.props.get("suffix", ""))
        secondary = str(elem.props.get("secondary_text", ""))
        value_color = self._get_valid_color(elem.props.get("value_color", elem.props.get("color")), "#1976D2")
        label_color = self._get_valid_color(elem.props.get("label_color"), self._get_valid_color(elem.props.get("secondary_color"), "#666666"))
        unit_color = self._get_valid_color(elem.props.get("unit_color"), self._get_valid_color(elem.props.get("secondary_color"), "#666666"))
        secondary_color = self._get_valid_color(elem.props.get("secondary_text_color", elem.props.get("secondary_color")), "#666666")
        style = str(elem.props.get("style", "Modern")).strip().lower()
        align = str(elem.props.get("align", "center")).strip().lower()
        if align == "left":
            anchor, tx = "w", x + max(8, int(w * .05))
        elif align == "right":
            anchor, tx = "e", x + w - max(8, int(w * .05))
        else:
            anchor, tx = "center", x + w / 2

        def normalize_font(value, fallback):
            if isinstance(value, list):
                return tuple(value)
            if isinstance(value, tuple):
                return value
            return fallback

        lf = normalize_font(elem.props.get("label_font"), ("Segoe UI", 9, "bold"))
        vf = normalize_font(elem.props.get("value_font"), ("Segoe UI", 34, "bold"))
        uf = normalize_font(elem.props.get("unit_font"), ("Segoe UI", 12))
        sf = normalize_font(elem.props.get("secondary_font"), ("Segoe UI", 10))

        def font_base_size(value, fallback):
            try:
                return max(1, abs(int(float(value[1]))))
            except (TypeError, ValueError, IndexError):
                return fallback

        # Font family and size are controlled by the single Font property.
        # Use negative Tk sizes so Canvas text is pixel-sized consistently.
        lf = (lf[0], -font_base_size(lf, 9), *lf[2:])
        vf = (vf[0], -font_base_size(vf, 34), *vf[2:])
        uf = (uf[0], -font_base_size(uf, 12), *uf[2:])
        sf = (sf[0], -font_base_size(sf, 10), *sf[2:])
        display_value = f"{prefix}{value}{suffix}"

        # Fit each row independently so no alignment mode can push text past
        # the element boundary.
        content_w = max(10, w - max(8, int(w * .10)))
        def fit(f, text, minimum=7):
            if not text:
                return f
            size = abs(int(f[1]))
            while size > minimum:
                self.canvas.create_text(-10000, -10000, text=text, font=f)
                item = self.canvas.find_all()[-1]
                bb = self.canvas.bbox(item)
                self.canvas.delete(item)
                if not bb or (bb[2] - bb[0]) <= content_w:
                    break
                size -= 1
                f = (f[0], -size, *f[2:])
            return f
        lf = fit(lf, label)
        vf = fit(vf, display_value, 12)
        uf = fit(uf, unit)
        sf = fit(sf, secondary)

        top = y + max(8, int(h * .09))
        value_y = y + int(h * (.43 if style == "led" else .46))
        try:
            unit_gap = max(0, int(float(elem.props.get("unit_gap", 18) or 18)))
        except (TypeError, ValueError):
            unit_gap = 18
        unit_y = value_y + max(10, unit_gap)
        secondary_y = y + h - max(6, int(h * .07))
        if secondary:
            unit_y = min(unit_y, secondary_y - max(12, abs(int(sf[1]))) - 4)

        self.canvas.create_text(tx, top, anchor=anchor, text=label, fill=label_color, font=lf,
                                tags=("element", f"elem_{elem.elem_id}"))
        self.canvas.create_text(tx, value_y, anchor=anchor, text=display_value, fill=value_color, font=vf,
                                tags=("element", f"elem_{elem.elem_id}"))
        if unit:
            self.canvas.create_text(tx, unit_y, anchor=anchor, text=unit, fill=unit_color, font=uf,
                                    tags=("element", f"elem_{elem.elem_id}"))
        if secondary:
            self.canvas.create_text(tx, secondary_y, anchor="s", text=secondary, fill=secondary_color, font=sf,
                                    tags=("element", f"elem_{elem.elem_id}"))

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

    def _draw_datetimepicker(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, outline_w)
        display_format = str(elem.props.get("display_format", "Date & Time") or "Date & Time")
        text = "Date & Time" if display_format == "Date & Time" else display_format
        if display_format == "Date":
            text = str(elem.props.get("date_pattern", "yyyy-mm-dd"))
        elif display_format == "Time":
            text = "12:30 PM" if str(elem.props.get("time_format", "24h")) == "12h" else "12:30:00"
        elif display_format == "Custom":
            text = str(elem.props.get("custom_format", "Custom format")) or "Custom format"
        self.canvas.create_text(
            x + 8, y + h / 2, text=text, anchor="w", fill=fg,
            font=self._scaled_font(font), tags=("element", f"elem_{elem.elem_id}")
        )
        ax = x + w - max(24, h) / 2
        self.canvas.create_polygon(
            ax - 4, y + h / 2 - 2, ax + 4, y + h / 2 - 2,
            ax, y + h / 2 + 4, fill=fg, outline="",
            tags=("element", f"elem_{elem.elem_id}")
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

    def _draw_datetimepicker(self, elem, x, y, w, h, bg, fg, font, outline, outline_w):
        """Render DateTimePicker as a compact combo-style field in the designer."""
        bw = max(1, outline_w)
        self._draw_sunken_rect(elem, x, y, w, h, bg, outline, bw)
        pad = max(5, int(h * 0.20))
        button_w = max(24, int(h * 0.95))
        display_format = str(elem.props.get("display_format", "Date & Time") or "Date & Time")
        sample = {
            "Date": "09/05/2026",
            "Date & Time": "09/05/2026 14:30",
            "Time": "14:30",
            "Custom": "Custom format",
        }.get(display_format, "09/05/2026 14:30")
        self._render_text_on_canvas(elem, x + pad, y, max(1, w - button_w - 2*pad), h,
                                    str(elem.props.get("display_preview", sample) or sample), fg,
                                    font, anchor="w")
        bx = x + w - button_w
        self.canvas.create_rectangle(bx, y + 1, x + w - 1, y + h - 1,
                                     fill=bg, outline="", tags=("element", f"elem_{elem.elem_id}"))
        cx, cy = bx + button_w/2, y + h/2
        self.canvas.create_polygon(cx-4, cy-2, cx+4, cy-2, cx, cy+3, fill=fg,
                                   outline="", tags=("element", f"elem_{elem.elem_id}"))

    def _draw_fallback(
            self, elem, x, y, w, h, bg, fg, font, outline, outline_w
            ):
        bw = self._configured_border_width(elem, outline_w)
        self._draw_flat_rect(elem, x, y, w, h, bg, outline, bw)
        self._render_text_on_canvas(elem, x, y, w, h, elem.display_label, fg,
                                     font
                                     )

    def _configured_border_width(self, elem, default_width=1):
        """Return the designer-visible border width, honoring legacy aliases."""
        raw = elem.props.get("border_width", elem.props.get("bd", ""))
        try:
            value = int(float(raw)) if str(raw).strip() else int(default_width)
        except (TypeError, ValueError):
            value = int(default_width)
        return max(0, value)

    def _draw_flat_rect(self, elem, x, y, w, h, fill, outline, outline_w):
        fill = "" if elem.props.get("image_path") else fill
        elem.rect_id = self.canvas.create_rectangle(
            x, y, x + w, y + h, fill=fill, outline=outline,
            width=outline_w,
            tags=("element", f"elem_{elem.elem_id}")
        )

    def _draw_sunken_rect(self, elem, x, y, w, h, fill, outline, outline_w):
        fill = "" if elem.props.get("image_path") else fill
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
        fill = "" if elem.props.get("image_path") else fill
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