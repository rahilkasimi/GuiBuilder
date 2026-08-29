"""Runtime source for the GUI Builder's instrumentation-style widgets.

The designer itself renders these controls on the design canvas through
CanvasRenderer.  Generated applications receive the standalone source below
so exported/preview applications do not depend on the GUI Builder package.
"""

INSTRUMENTATION_RUNTIME_CODE = r'''
import math


def _builder_bool(value, default=False):
    text = str(value).strip().lower()
    if not text:
        return default
    return text in ("yes", "true", "1", "on")


def _builder_clamp(value, low, high):
    try:
        return max(low, min(high, float(value)))
    except (TypeError, ValueError):
        return low


def _builder_bright_color(color, brightness):
    """Apply brightness to #RRGGBB colors; leave named colors unchanged."""
    text = str(color or "")
    if len(text) == 7 and text.startswith("#"):
        try:
            factor = _builder_clamp(brightness, 0, 100) / 100.0
            rgb = [int(text[i:i + 2], 16) for i in (1, 3, 5)]
            rgb = [max(0, min(255, int(round(v * factor)))) for v in rgb]
            return "#%02X%02X%02X" % tuple(rgb)
        except (TypeError, ValueError):
            pass
    return text


class BuilderPushButton(tk.Frame):
    """Canvas-rendered push button with square/round and toggle/momentary modes."""

    def __init__(self, master, text="Push Button", shape="Square", style="Mechanical",
                 behavior="Momentary", default_state="Off", font=("Segoe UI", 9, "bold"),
                 fg="#FFFFFF",
                 bg="#1976D2", active_bg="#0D47A1", border_width=2,
                 command=None, width=None, height=None, **kwargs):
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        super().__init__(master, bg=bg, bd=0, highlightthickness=0, **kwargs)
        self.pack_propagate(False)
        self.text = str(text)
        self.shape = str(shape or "Square")
        self.style = str(style or "Mechanical")
        self.behavior = str(behavior or "Momentary")
        self.font = font if isinstance(font, (tuple, list)) else ("Segoe UI", 9, "bold")
        self.fg = str(fg or "#FFFFFF")
        self.bg = str(bg or "#1976D2")
        self.active_bg = str(active_bg or self.bg)
        try:
            self.border_width = max(0, int(border_width))
        except (TypeError, ValueError):
            self.border_width = 2
        self.command = command
        self._state = _builder_bool(default_state)
        self._listeners = []
        self._pressed = False
        self.canvas = tk.Canvas(self, bg=self.bg, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Leave>", self._on_leave)
        self.bind("<Configure>", lambda e: self._redraw())
        self.after_idle(self._redraw)
        self._redraw()

    def add_state_listener(self, callback):
        if callable(callback) and callback not in self._listeners:
            self._listeners.append(callback)

    def get_state(self):
        return bool(self._state)

    def set_state(self, value, notify=True):
        new_state = bool(value)
        changed = new_state != self._state
        self._state = new_state
        self._redraw()
        if notify and changed:
            for callback in list(self._listeners):
                try:
                    callback(self._state)
                except Exception:
                    pass

    def _on_press(self, event=None):
        self._pressed = True
        if self.behavior.strip().lower() == "momentary":
            self.set_state(True)
        self._redraw()

    def _on_release(self, event=None):
        was_pressed = self._pressed
        self._pressed = False
        if not was_pressed:
            return
        if self.behavior.strip().lower() == "toggle":
            self.set_state(not self._state)
        else:
            self.set_state(False)
        if callable(self.command):
            try:
                self.command()
            except TypeError:
                self.command(None)
        self._redraw()

    def _on_leave(self, event=None):
        if self.behavior.strip().lower() == "momentary" and self._pressed:
            self._pressed = False
            self.set_state(False)
            self._redraw()

    def _rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        r = max(2, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
        c = self.canvas
        c.create_rectangle(x1 + r, y1, x2 - r, y2, **kwargs)
        c.create_rectangle(x1, y1 + r, x2, y2 - r, **kwargs)
        c.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, **kwargs)
        c.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, **kwargs)
        c.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, **kwargs)
        c.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, **kwargs)

    def _redraw(self):
        if not self.winfo_exists():
            return
        c = self.canvas
        c.delete("all")
        w = max(10, c.winfo_width())
        h = max(10, c.winfo_height())
        pad = max(2, self.border_width)
        pressed = self._pressed or (self.behavior.strip().lower() == "toggle" and self._state)
        fill = self.active_bg if pressed else self.bg
        inset = 2 if pressed else 0
        x1, y1, x2, y2 = pad, pad + inset, w - pad, h - pad + inset

        if self.shape.strip().lower() == "round":
            c.create_oval(x1, y1, x2, y2, fill=fill, outline="#555555", width=max(1, pad))
            c.create_oval(x1 + 4, y1 + 4, x2 - 4, y2 - 4,
                          outline="#FFFFFF", width=1)
        elif self.style.strip().lower() == "mechanical":
            self._rounded_rect(x1, y1, x2, y2, radius=8,
                               fill=fill, outline="#4F4F4F", width=max(1, pad))
            if not pressed:
                c.create_line(x1 + 3, y1 + 2, x2 - 4, y1 + 2,
                              fill="#FFFFFF", width=1)
                c.create_line(x1 + 2, y1 + 3, x1 + 2, y2 - 4,
                              fill="#FFFFFF", width=1)
        else:
            c.create_rectangle(x1, y1, x2, y2, fill=fill,
                               outline="#555555", width=max(1, pad))

        c.create_text(w / 2, h / 2 + (2 if pressed else 0), text=self.text,
                      fill=self.fg, font=self.font)


class BuilderRadioButton(tk.Frame):
    """Canvas-rendered radio option supporting round/square indicators."""

    def __init__(self, master, text="Option", variable=None, value="1",
                 shape="Round", selected="No", font=("Segoe UI", 9), fg="#212121", bg="#F5F5F5",
                 active_fg="#1976D2", active_bg="#1976D2", command=None, width=None, height=None, **kwargs):
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        super().__init__(master, bg=bg, bd=0, highlightthickness=0, **kwargs)
        self.pack_propagate(False)
        self.text = str(text)
        self.variable = variable if variable is not None else tk.StringVar(value="")
        self.value = str(value)
        self.shape = str(shape or "Round")
        self.font = font if isinstance(font, (tuple, list)) else ("Segoe UI", 9)
        self.fg = str(fg or "#212121")
        self.bg = str(bg or "#F5F5F5")
        self.active_fg = str(active_fg or "#1976D2")
        self.active_bg = str(active_bg or self.active_fg)
        self.command = command
        self._listeners = []
        self._last_selected = False
        self.canvas = tk.Canvas(self, bg=self.bg, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self._on_click)
        self.variable.trace_add("write", self._on_variable_change)
        self.bind("<Configure>", lambda e: self._redraw())
        if _builder_bool(selected):
            try:
                self.variable.set(self.value)
            except Exception:
                pass
        self._redraw()

    def add_state_listener(self, callback):
        if callable(callback) and callback not in self._listeners:
            self._listeners.append(callback)

    def _on_variable_change(self, *args):
        selected = self.is_selected()
        self._redraw()
        if selected != self._last_selected:
            self._last_selected = selected
            for callback in list(self._listeners):
                try:
                    callback(selected)
                except Exception:
                    pass

    def is_selected(self):
        try:
            return str(self.variable.get()) == self.value
        except Exception:
            return False

    def select(self):
        try:
            self.variable.set(self.value)
        except Exception:
            pass

    def _on_click(self, event=None):
        self.select()
        if callable(self.command):
            try:
                self.command()
            except TypeError:
                self.command(None)

    def _redraw(self):
        if not self.winfo_exists():
            return
        c = self.canvas
        c.delete("all")
        w, h = max(20, c.winfo_width()), max(20, c.winfo_height())
        cx, cy = 12, h / 2
        selected = self.is_selected()
        shape = self.shape.strip().lower()
        if shape == "square":
            c.create_rectangle(cx - 7, cy - 7, cx + 7, cy + 7,
                                outline="#777777", fill=self.bg, width=1)
            if selected:
                c.create_rectangle(cx - 4, cy - 4, cx + 4, cy + 4,
                                    fill=self.active_bg, outline=self.active_bg)
        else:
            c.create_oval(cx - 7, cy - 7, cx + 7, cy + 7,
                          outline="#777777", fill=self.bg, width=1)
            if selected:
                c.create_oval(cx - 4, cy - 4, cx + 4, cy + 4,
                              fill=self.active_bg, outline=self.active_bg)
        text_color = self.active_fg if selected else self.fg
        c.create_text(26, cy, anchor="w", text=self.text, fill=text_color,
                      font=self.font)


_BUILDER_SEGMENTS = {
    "0": "abcdef", "1": "bc", "2": "abdeg", "3": "abcdg",
    "4": "bcfg", "5": "acdfg", "6": "acdefg", "7": "abc",
    "8": "abcdefg", "9": "abcdfg", "-": "g", " ": "",
}


class BuilderLEDDisplay(tk.Frame):
    """Seven-segment numeric display used for both single and multi-digit LEDs."""

    def __init__(self, master, value="0", digits=1, color="#00FF66", off_color="#16351F",
                 brightness=100, glow="Yes", leading_zeros="No", segment_width=4, digit_gap=12,
                 mode="Multi Digit", width=None, height=None, **kwargs):
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        super().__init__(master, bg=kwargs.pop("bg", "#101010"), bd=0, highlightthickness=0, **kwargs)
        self.pack_propagate(False)
        self.value = str(value)
        self.digits = max(1, int(digits or 1))
        self.color = str(color or "#00FF66")
        self.off_color = str(off_color or "#16351F")
        self.brightness = _builder_clamp(brightness, 0, 100)
        self.glow = _builder_bool(glow, True)
        self.leading_zeros = _builder_bool(leading_zeros, False)
        try:
            self.segment_width = max(1, int(segment_width))
        except (TypeError, ValueError):
            self.segment_width = 4
        try:
            self.digit_gap = max(0, int(digit_gap))
        except (TypeError, ValueError):
            self.digit_gap = 12
        self.mode = str(mode or "Multi Digit")
        self.canvas = tk.Canvas(self, bg=self["bg"], bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.bind("<Configure>", lambda e: self._redraw())
        self.after_idle(self._redraw)
        self._redraw()

    def set_value(self, value):
        self.value = str(value)
        self._redraw()

    def _format_chars(self):
        text = self.value.strip()
        if self.mode.lower().startswith("single"):
            return [(text[-1:] or "0")]
        if self.leading_zeros and text.replace("-", "").isdigit():
            sign = "-" if text.startswith("-") else ""
            digits = text[1:] if sign else text
            text = sign + digits.zfill(self.digits - (1 if sign else 0))
        else:
            text = text[-self.digits:]
        return list(text.rjust(self.digits))

    def _segment_points(self, x, y, w, h, seg):
        t = max(1, min(self.segment_width, int(min(w, h) * 0.16)))
        if seg == "a": return (x + t, y, x + w - t, y + t)
        if seg == "g": return (x + t, y + h / 2 - t / 2, x + w - t, y + h / 2 + t / 2)
        if seg == "d": return (x + t, y + h - t, x + w - t, y + h)
        if seg == "f": return (x, y + t, x + t, y + h / 2 - t / 2)
        if seg == "b": return (x + w - t, y + t, x + w, y + h / 2 - t / 2)
        if seg == "e": return (x, y + h / 2 + t / 2, x + t, y + h - t)
        if seg == "c": return (x + w - t, y + h / 2 + t / 2, x + w, y + h - t)
        return (x, y, x, y)

    def _redraw(self):
        if not self.winfo_exists():
            return
        c = self.canvas
        c.delete("all")
        w, h = max(30, c.winfo_width()), max(20, c.winfo_height())
        chars = self._format_chars()
        margin = max(3, int(w * 0.02))
        gap = self.digit_gap
        if len(chars) > 1:
            min_digit_w = 8
            max_gap = max(0, int((w - 2 * margin - min_digit_w * len(chars)) / (len(chars) - 1)))
            gap = min(gap, max_gap)
        digit_w = max(8, (w - 2 * margin - gap * max(0, len(chars) - 1)) / max(1, len(chars)))
        digit_h = max(12, h - 2 * margin)
        x = margin
        glow_width = max(1, int(self.segment_width + 4))
        for char in chars:
            active = _BUILDER_SEGMENTS.get(char.upper(), "")
            for seg in "abcdefg":
                x1, y1, x2, y2 = self._segment_points(x, margin, digit_w, digit_h, seg)
                is_on = seg in active
                color = _builder_bright_color(self.color, self.brightness) if is_on else self.off_color
                if is_on and self.glow:
                    c.create_rectangle(x1, y1, x2, y2,
                                       outline=color, fill=color,
                                       width=glow_width)
                c.create_rectangle(x1, y1, x2, y2,
                                   outline=color, fill=color,
                                   width=max(1, self.segment_width))
            x += digit_w + gap


class BuilderLEDIndicator(tk.Frame):
    """Small boolean LED indicator with color, shape, glow and brightness."""

    def __init__(self, master, state="Off", on_color="#00FF66", off_color="#16351F",
                 shape="Round", brightness=100, glow="Yes", border_width=1, bg="#E0E0E0", width=None, height=None, **kwargs):
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        super().__init__(master, bg=bg, bd=0, highlightthickness=0, **kwargs)
        self.pack_propagate(False)
        self.state = _builder_bool(state)
        self.on_color = str(on_color or "#00FF66")
        self.off_color = str(off_color or "#16351F")
        self.shape = str(shape or "Round")
        self.brightness = _builder_clamp(brightness, 0, 100)
        self.glow = _builder_bool(glow, True)
        try:
            self.border_width = max(0, int(border_width))
        except (TypeError, ValueError):
            self.border_width = 1
        self.canvas = tk.Canvas(self, bg=bg, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.bind("<Configure>", lambda e: self._redraw())
        self.after_idle(self._redraw)
        self._redraw()

    def set_state(self, value):
        self.state = bool(value)
        self._redraw()

    def get_state(self):
        return bool(self.state)

    def _redraw(self):
        if not self.winfo_exists():
            return
        c = self.canvas
        c.delete("all")
        w, h = max(12, c.winfo_width()), max(12, c.winfo_height())
        d = max(6, min(w, h) - 2)
        x1, y1 = (w - d) / 2, (h - d) / 2
        x2, y2 = x1 + d, y1 + d
        color = _builder_bright_color(self.on_color, self.brightness) if self.state else self.off_color
        if self.state and self.glow:
            for inset in (0, 2, 4):
                c.create_oval(x1 - inset, y1 - inset, x2 + inset, y2 + inset,
                              outline=color, width=1)
        if self.shape.strip().lower() == "square":
            c.create_rectangle(x1, y1, x2, y2, fill=color,
                               outline="#555555", width=max(1, self.border_width))
        else:
            c.create_oval(x1, y1, x2, y2, fill=color,
                          outline="#555555", width=max(1, self.border_width))


class BuilderGauge(tk.Frame):
    """Analog gauge/meter with configurable range, arc, ticks and needle."""

    def __init__(self, master, value=50, min_value=0, max_value=100,
                 start_angle=225, end_angle=-45, needle_color="#E53935",
                 arc_color="#1976D2", track_color="#D9D9D9", tick_color="#555555",
                 ticks=10, show_value="Yes", unit="", thickness=8, bg="#FFFFFF", width=None, height=None, **kwargs):
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        super().__init__(master, bg=bg, bd=0, highlightthickness=0, **kwargs)
        self.pack_propagate(False)
        self.value = value
        self.min_value = min_value
        self.max_value = max_value
        self.start_angle = float(start_angle)
        self.end_angle = float(end_angle)
        self.needle_color = needle_color
        self.arc_color = arc_color
        self.track_color = track_color
        self.tick_color = tick_color
        try: self.ticks = max(0, int(ticks))
        except (TypeError, ValueError): self.ticks = 10
        self.show_value = _builder_bool(show_value, True)
        self.unit = str(unit or "")
        try: self.thickness = max(1, int(thickness))
        except (TypeError, ValueError): self.thickness = 8
        self.canvas = tk.Canvas(self, bg=bg, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.bind("<Configure>", lambda e: self._redraw())
        self.after_idle(self._redraw)
        self._redraw()

    def set_value(self, value):
        self.value = value
        self._redraw()

    def _angle_for_value(self):
        lo, hi = float(self.min_value), float(self.max_value)
        ratio = 0.0 if hi == lo else _builder_clamp(self.value, lo, hi) - lo
        ratio = 0.0 if hi == lo else ratio / (hi - lo)
        return self.start_angle + ratio * (self.end_angle - self.start_angle)

    def _point(self, cx, cy, radius, angle):
        rad = math.radians(angle)
        return cx + radius * math.cos(rad), cy - radius * math.sin(rad)

    def _redraw(self):
        if not self.winfo_exists(): return
        c = self.canvas; c.delete("all")
        w, h = max(40, c.winfo_width()), max(40, c.winfo_height())
        pad = max(8, self.thickness + 4)
        size = min(w, h) - 2 * pad
        x1, y1 = (w - size) / 2, (h - size) / 2
        x2, y2 = x1 + size, y1 + size
        extent = self.end_angle - self.start_angle
        c.create_arc(x1, y1, x2, y2, start=self.start_angle, extent=extent,
                     style="arc", outline=self.track_color, width=self.thickness)
        value_angle = self._angle_for_value()
        value_extent = value_angle - self.start_angle
        c.create_arc(x1, y1, x2, y2, start=self.start_angle, extent=value_extent,
                     style="arc", outline=self.arc_color, width=self.thickness)
        cx, cy = w / 2, h / 2
        tick_outer = size / 2 - 2
        tick_inner = tick_outer - max(8, self.thickness + 4)
        for i in range(self.ticks + 1):
            ratio = i / self.ticks if self.ticks else 0
            angle = self.start_angle + ratio * (self.end_angle - self.start_angle)
            ox, oy = self._point(cx, cy, tick_outer, angle)
            ix, iy = self._point(cx, cy, tick_inner, angle)
            c.create_line(ix, iy, ox, oy, fill=self.tick_color, width=1)
        needle_len = size / 2 - 14
        nx, ny = self._point(cx, cy, needle_len, value_angle)
        c.create_line(cx, cy, nx, ny, fill=self.needle_color, width=max(2, self.thickness // 2))
        c.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill=self.needle_color, outline="")
        if self.show_value:
            try:
                txt = f"{float(self.value):g}{self.unit}"
            except (TypeError, ValueError):
                txt = f"{self.value}{self.unit}"
            c.create_text(cx, cy + size * 0.23, text=txt,
                          fill=self.tick_color, font=("Segoe UI", 10, "bold"))


class BuilderMeasurementDisplay(tk.Frame):
    """Composite value + unit + label display for dashboards and instruments."""

    def __init__(self, master, label="Temperature", value="24", unit="°C",
                 style="Modern", color="#1976D2", bg="#FFFFFF", decimal_places=0,
                 prefix="", suffix="", secondary_text="", secondary_color="#666666",
                 align="center", led_digits=3, width=None, height=None, **kwargs):
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        super().__init__(master, bg=bg, bd=0, highlightthickness=0, **kwargs)
        self.pack_propagate(False)
        self.label = str(label)
        self.value = str(value)
        self.unit = str(unit)
        self.style = str(style or "Modern")
        self.color = str(color or "#1976D2")
        self.bg = str(bg or "#FFFFFF")
        try: self.decimal_places = max(0, int(decimal_places))
        except (TypeError, ValueError): self.decimal_places = 0
        self.prefix = str(prefix or "")
        self.suffix = str(suffix or "")
        self.secondary_text = str(secondary_text or "")
        self.secondary_color = str(secondary_color or "#666666")
        self.align = str(align or "center")
        try: self.led_digits = max(1, int(led_digits))
        except (TypeError, ValueError): self.led_digits = 3
        self.canvas = tk.Canvas(self, bg=self.bg, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.bind("<Configure>", lambda e: self._redraw())
        self.after_idle(self._redraw)
        self._redraw()

    def set_value(self, value):
        self.value = str(value)
        self._redraw()

    def _formatted_value(self):
        try:
            num = float(self.value)
            if self.decimal_places:
                core = f"{num:.{self.decimal_places}f}"
            else:
                core = f"{num:g}"
        except (TypeError, ValueError):
            core = self.value
        return f"{self.prefix}{core}{self.suffix}"

    def _redraw(self):
        if not self.winfo_exists(): return
        c = self.canvas; c.delete("all")
        w, h = max(50, c.winfo_width()), max(30, c.winfo_height())
        anchor = {"left": "w", "right": "e"}.get(self.align.lower(), "center")
        tx = 8 if anchor == "w" else (w - 8 if anchor == "e" else w / 2)
        c.create_text(tx, 12, anchor=anchor, text=self.label, fill=self.secondary_color,
                      font=("Segoe UI", 9, "bold"))
        value_text = self._formatted_value()
        if self.style.lower() == "led":
            value_text = f"{value_text} {self.unit}".rstrip()
            c.create_text(tx, h * 0.52, anchor="center", text=value_text,
                          fill=self.color, font=("Consolas", max(14, int(h * 0.36)), "bold"))
        else:
            c.create_text(tx, h * 0.55, anchor="center", text=value_text,
                          fill=self.color, font=("Segoe UI", max(16, int(h * 0.42)), "bold"))
            c.create_text(tx + (w * 0.30 if anchor == "center" else 0), h * 0.80,
                          anchor="center", text=self.unit, fill=self.secondary_color,
                          font=("Segoe UI", max(8, int(h * 0.20))))
        if self.secondary_text:
            c.create_text(tx, h - 7, anchor="s", text=self.secondary_text,
                          fill=self.secondary_color,
                          font=("Segoe UI", max(7, int(h * 0.13))))
'''
