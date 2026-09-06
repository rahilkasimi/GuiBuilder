"""Runtime source for the GUI Builder's instrumentation-style widgets.

The designer itself renders these controls on the design canvas through
CanvasRenderer.  Generated applications receive the standalone source below
so exported/preview applications do not depend on the GUI Builder package.
"""

INSTRUMENTATION_RUNTIME_CODE = r'''
import math
import os
import tkinter as tk
from PIL import Image, ImageTk


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




def _builder_draw_background(owner, canvas):
    path=str(getattr(owner,"_background_image","") or "")
    if not path: return
    try:
        full=path if os.path.isabs(path) else os.path.join(os.path.dirname(__file__),path)
        img=Image.open(full).convert("RGBA"); w=max(1,canvas.winfo_width()); h=max(1,canvas.winfo_height()); iw,ih=img.size
        mode=str(getattr(owner,"_background_image_mode","Fit") or "Fit").lower()
        if mode=="stretch": img=img.resize((w,h),Image.Resampling.LANCZOS)
        elif mode in ("fill","cover"):
            sc=max(w/iw,h/ih); nw=max(1,int(iw*sc)); nh=max(1,int(ih*sc)); img=img.resize((nw,nh),Image.Resampling.LANCZOS); l=max(0,(nw-w)//2); t=max(0,(nh-h)//2); img=img.crop((l,t,l+w,t+h))
        elif mode in ("fit","contain"):
            sc=min(w/iw,h/ih); img=img.resize((max(1,int(iw*sc)),max(1,int(ih*sc))),Image.Resampling.LANCZOS)
        elif mode in ("tile","repeat"):
            base=Image.new("RGBA",(w,h),(0,0,0,0))
            for yy in range(0,h,img.height):
                for xx in range(0,w,img.width): base.alpha_composite(img,(xx,yy))
            img=base
        photo=ImageTk.PhotoImage(img); owner._background_image_ref=photo; canvas.create_image(w/2,h/2,image=photo,anchor="center",tags="_builder_bg"); canvas.tag_lower("_builder_bg")
    except Exception:
        pass

def _builder_int(value, default=0, minimum=None, maximum=None):
    try:
        result = int(float(value))
    except (TypeError, ValueError):
        result = default
    if minimum is not None:
        result = max(minimum, result)
    if maximum is not None:
        result = min(maximum, result)
    return result
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
        self._background_image = ""
        self._background_image_mode = "Fit"
        self._background_image_anchor = "Center"
        self._background_image_ref = None
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
        self.bind("<Map>", lambda e: self.after_idle(self._redraw))
        self.after(25, self._redraw)
        self.after(100, self._redraw)
        self.after_idle(self._redraw)
        self._redraw()

    def set_background_image(self, path, mode="Fit", anchor="Center"):
        self._background_image=path or ""; self._background_image_mode=mode or "Fit"; self._background_image_anchor=anchor or "Center"; self._redraw()

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
        _builder_draw_background(self,c)
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
        self._background_image = ""
        self._background_image_mode = "Fit"
        self._background_image_anchor = "Center"
        self._background_image_ref = None
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
        self.bind("<Map>", lambda e: self.after_idle(self._redraw))
        self.after(25, self._redraw)
        self.after(100, self._redraw)
        self.after_idle(self._redraw)
        if _builder_bool(selected):
            try:
                self.variable.set(self.value)
            except Exception:
                pass
        self._redraw()

    def set_background_image(self, path, mode="Fit", anchor="Center"):
        self._background_image=path or ""; self._background_image_mode=mode or "Fit"; self._background_image_anchor=anchor or "Center"; self._redraw()

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
        _builder_draw_background(self,c)
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
    """Seven-segment numeric display used for single and multi-digit LEDs.

    The display uses a fixed digit geometry derived from widget height.  The
    number of configured digit slots therefore remains stable across values
    and across Run Preview vs. external Python execution.  The complete
    digit bank is centered in the available widget instead of stretching each
    digit to fill the canvas width.
    """

    def __init__(self, master, value="0", digits=1, color="#00FF66", off_color="#16351F",
                 brightness=100, glow="Yes", leading_zeros="No", segment_width=4, digit_gap=12,
                 decimal_places=0, mode="Multi Digit", width=None, height=None, **kwargs):
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        super().__init__(master, bg=kwargs.pop("bg", "#101010"), bd=0, highlightthickness=0, **kwargs)
        self.pack_propagate(False)
        self._background_image = ""
        self._background_image_mode = "Fit"
        self._background_image_anchor = "Center"
        self._background_image_ref = None
        self.value = str(value)
        try:
            self.digits = max(1, int(digits or 1))
        except (TypeError, ValueError):
            self.digits = 1
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
        try:
            self.decimal_places = max(0, int(decimal_places))
        except (TypeError, ValueError):
            self.decimal_places = 0
        self.mode = str(mode or "Multi Digit")
        self.canvas = tk.Canvas(self, bg=self["bg"], bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.bind("<Configure>", lambda e: self._redraw())
        self.bind("<Map>", lambda e: self.after_idle(self._redraw))
        self.after(25, self._redraw)
        self.after(100, self._redraw)
        self.after_idle(self._redraw)

    def set_background_image(self, path, mode="Fit", anchor="Center"):
        self._background_image=path or ""; self._background_image_mode=mode or "Fit"; self._background_image_anchor=anchor or "Center"; self._redraw()

    def set_value(self, value):
        self.value = str(value)
        self._redraw()

    def _format_chars(self):
        text = self.value.strip()
        if self.decimal_places > 0:
            try:
                text = f"{float(text):.{self.decimal_places}f}"
            except (TypeError, ValueError):
                pass
        if self.mode.lower().startswith("single"):
            return [(text[-1:] or "0", False)]

        negative = text.startswith("-")
        sign = "-" if negative else ""
        raw = text[1:] if negative else text
        raw_digits = [ch for ch in raw if ch.isdigit()]
        if self.leading_zeros and raw_digits:
            target = max(1, self.digits - (1 if negative else 0))
            raw_digits = list("".join(raw_digits).zfill(target))
        if not raw_digits:
            raw_digits = ["0"]

        decimals = set()
        digit_index = 0
        for ch in raw:
            if ch == "." and digit_index > 0:
                decimals.add(digit_index - 1)
            elif ch.isdigit():
                digit_index += 1

        actual = []
        if sign:
            actual.append(("-", False))
        actual.extend((digit, idx in decimals) for idx, digit in enumerate(raw_digits))
        actual = actual[-self.digits:]

        # Physical slots are fixed by the configured digit count.  Unused
        # positions are blank/off but still occupy their full digit geometry.
        # Numeric content is right-aligned, which is the conventional behavior
        # for calculator/instrument displays.
        padding = max(0, self.digits - len(actual))
        return [(" ", False)] * padding + actual

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
        _builder_draw_background(self,c)
        cw, ch = c.winfo_width(), c.winfo_height()
        if cw <= 1 or ch <= 1:
            self.after(50, self._redraw)
            return

        pad = max(4, int(min(cw, ch) * 0.06))
        digit_h = max(16, ch - 2 * pad)
        # Seven-segment aspect ratio is intentionally fixed rather than
        # expanding to consume the whole widget width. This is what keeps
        # digits stable in external Python execution too.
        aspect = 0.62
        digit_w = max(10, int(round(digit_h * aspect)))
        chars = self._format_chars()
        if self.mode.lower().startswith("multi"):
            slot_count = max(1, self.digits + (1 if chars and chars[0][0] == "-" else 0))
        else:
            slot_count = max(1, len(chars))

        gap = self.digit_gap
        required_w = slot_count * digit_w + max(0, slot_count - 1) * gap
        available_w = max(1, cw - 2 * pad)
        if required_w > available_w and slot_count > 1:
            # Preserve actual digit size as far as possible. Only reduce the
            # user gap when the configured bank cannot fit.
            gap = max(1, int((available_w - slot_count * digit_w) / max(1, slot_count - 1)))
            required_w = slot_count * digit_w + max(0, slot_count - 1) * gap
        if required_w > available_w:
            # Very small widgets: scale the entire bank uniformly as a last
            # resort, while retaining the configured number of slots.
            scale = available_w / float(required_w)
            digit_w = max(8, int(digit_w * scale))
            digit_h = max(12, int(digit_h * scale))
            gap = max(1, int(gap * scale)) if slot_count > 1 else 0
            required_w = slot_count * digit_w + max(0, slot_count - 1) * gap

        x = (cw - required_w) / 2
        y = (ch - digit_h) / 2
        glow_width = max(1, int(self.segment_width))
        active_color = _builder_bright_color(self.color, self.brightness)
        for char, has_decimal in chars:
            active = _BUILDER_SEGMENTS.get(char.upper(), "")
            for seg in "abcdefg":
                x1, y1, x2, y2 = self._segment_points(x, y, digit_w, digit_h, seg)
                color = active_color if seg in active else self.off_color
                if seg in active and self.glow:
                    c.create_rectangle(x1, y1, x2, y2, outline=color, fill=color,
                                       width=max(1, glow_width), tags="led-segment")
                else:
                    c.create_rectangle(x1, y1, x2, y2, outline=color, fill=color,
                                       width=max(1, self.segment_width), tags="led-segment")
            if has_decimal:
                # The decimal belongs in the inter-digit gap when possible.
                # It is deliberately larger than the previous tiny bottom
                # corner dot and is vertically centered around the lower half.
                dot_r = max(3.0, min(digit_w, digit_h) * 0.075)
                gap_center_x = x + digit_w + gap / 2
                if gap < dot_r * 2.2:
                    gap_center_x = x + digit_w - dot_r - 2
                dot_x = min(cw - dot_r - 1, max(dot_r + 1, gap_center_x))
                dot_y = y + digit_h - max(dot_r + 3, digit_h * 0.16)
                c.create_oval(dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r,
                              fill=active_color, outline=active_color, tags="led-decimal")
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
        self._background_image = ""
        self._background_image_mode = "Fit"
        self._background_image_anchor = "Center"
        self._background_image_ref = None
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
        self.bind("<Map>", lambda e: self.after_idle(self._redraw))
        self.after(25, self._redraw)
        self.after(100, self._redraw)
        self.after_idle(self._redraw)
        self._redraw()

    def set_background_image(self, path, mode="Fit", anchor="Center"):
        self._background_image=path or ""; self._background_image_mode=mode or "Fit"; self._background_image_anchor=anchor or "Center"; self._redraw()

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
        _builder_draw_background(self,c)
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
        self._background_image = ""
        self._background_image_mode = "Fit"
        self._background_image_anchor = "Center"
        self._background_image_ref = None
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
        self.bind("<Map>", lambda e: self.after_idle(self._redraw))
        self.after(25, self._redraw)
        self.after(100, self._redraw)
        self.after_idle(self._redraw)
        self._redraw()

    def set_background_image(self, path, mode="Fit", anchor="Center"):
        self._background_image=path or ""; self._background_image_mode=mode or "Fit"; self._background_image_anchor=anchor or "Center"; self._redraw()

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
class BuilderMeasurementDisplay(tk.Frame):
    """Composite measurement display with deterministic, pixel-based layout."""

    def __init__(self, master, label="Temperature", value="24", unit="°C",
                 style="Modern", color="#1976D2", bg="#FFFFFF", decimal_places=0,
                 prefix="", suffix="", secondary_text="", secondary_color="#666666",
                 align="center", led_digits=3, width=None, height=None,
                 label_font=("Segoe UI", 9, "bold"), label_font_size=None, label_color="#666666",
                 value_font=("Segoe UI", 34, "bold"), value_font_size=None, value_color=None,
                 unit_font=("Segoe UI", 12), unit_font_size=None, unit_color="#666666",
                 secondary_font=("Segoe UI", 10), secondary_font_size=None,
                 secondary_text_color=None, unit_gap=18, **kwargs):
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        super().__init__(master, bg=bg, bd=0, highlightthickness=0, **kwargs)
        self.pack_propagate(False)
        self._background_image = ""
        self._background_image_mode = "Fit"
        self._background_image_anchor = "Center"
        self._background_image_ref = None
        self.label = str(label)
        self.value = str(value)
        self.unit = str(unit)
        self.style = str(style or "Modern")
        self.bg = str(bg or "#FFFFFF")
        self.decimal_places = _builder_int(decimal_places, 0, minimum=0)
        self.prefix = str(prefix or "")
        self.suffix = str(suffix or "")
        self.secondary_text = str(secondary_text or "")
        self.align = str(align or "center").strip().lower()
        self.led_digits = max(1, _builder_int(led_digits, 3, minimum=1))
        self.label_font = label_font if isinstance(label_font, (tuple, list)) else ("Segoe UI", 9, "bold")
        self.value_font = value_font if isinstance(value_font, (tuple, list)) else ("Segoe UI", 34, "bold")
        self.unit_font = unit_font if isinstance(unit_font, (tuple, list)) else ("Segoe UI", 12)
        self.secondary_font = secondary_font if isinstance(secondary_font, (tuple, list)) else ("Segoe UI", 10)
        # The Font tuple contains both family and size and is the sole source
        # of truth for new projects. The *_font_size arguments remain accepted
        # only for backward compatibility with older generated code.
        self.label_color = str(label_color or secondary_color or "#666666")
        self.value_color = str(value_color or color or "#1976D2")
        self.unit_color = str(unit_color or secondary_color or "#666666")
        self.secondary_text_color = str(secondary_text_color or secondary_color or "#666666")
        self.color = self.value_color  # legacy alias
        try: self.unit_gap = max(0, int(unit_gap))
        except (TypeError, ValueError): self.unit_gap = 18
        self.canvas = tk.Canvas(self, bg=self.bg, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.bind("<Configure>", lambda e: self._redraw())
        self.bind("<Map>", lambda e: self.after_idle(self._redraw))
        self.after(25, self._redraw)
        self.after(100, self._redraw)
        self.after_idle(self._redraw)

    @staticmethod
    def set_background_image(self, path, mode="Fit", anchor="Center"):
        self._background_image=path or ""; self._background_image_mode=mode or "Fit"; self._background_image_anchor=anchor or "Center"; self._redraw()

    @staticmethod
    def _font_size(font_value, default):
        try:
            size = int(round(abs(float(font_value[1]))))
            return size or default
        except (TypeError, ValueError, IndexError):
            return default

    @staticmethod
    def _font_family(font_value, default):
        try:
            family = str(font_value[0]).strip()
            return family or default
        except (TypeError, IndexError):
            return default

    @staticmethod
    def _font_options(font_value):
        try:
            opts = tuple(font_value[2:])
            return opts
        except (TypeError, IndexError):
            return ()

    def _pixel_font(self, font_value, size, fallback_family):
        family = self._font_family(font_value, fallback_family)
        options = self._font_options(font_value)
        # Negative Tk font size means pixels, not points. This makes external
        # execution consistent with Run Preview and Windows/Linux DPI scaling.
        return (family, -max(1, int(size)), *options)

    def set_value(self, value):
        self.value = str(value)
        self._redraw()

    def _formatted_value(self):
        try:
            num = float(self.value)
            core = f"{num:.{self.decimal_places}f}" if self.decimal_places else f"{num:g}"
        except (TypeError, ValueError):
            core = self.value
        return f"{self.prefix}{core}{self.suffix}"

    def _band_x(self, width, anchor):
        pad = max(8, int(width * 0.05))
        if anchor == "w":
            return pad
        if anchor == "e":
            return width - pad
        return width / 2

    def set_label(self, text):
        self.label = str(text)
        self._redraw()

    def set_unit(self, text):
        self.unit = str(text)
        self._redraw()

    def set_secondary_text(self, text):
        self.secondary_text = str(text)
        self._redraw()

    def _redraw(self):
        if not self.winfo_exists():
            return
        c = self.canvas
        c.delete("all")
        _builder_draw_background(self,c)
        w, h = c.winfo_width(), c.winfo_height()
        if w <= 1 or h <= 1:
            self.after(50, self._redraw)
            return

        # Use a common anchor for each row so left/right/center alignment is
        # coherent across the entire composite display.
        anchor = {"left": "w", "right": "e"}.get(self.align, "center")
        x = self._band_x(w, anchor)
        usable_w = max(1, w - 2 * max(8, int(w * 0.05)))

        # Reserve stable vertical bands. Font sizes are reduced only when a
        # specific line would exceed the available width; they never collapse
        # to a tiny default because of point/pixel DPI differences.
        label_size = max(1, self._font_size(self.label_font, 9))
        value_size = max(1, self._font_size(self.value_font, 34))
        unit_size = max(1, self._font_size(self.unit_font, 12))
        secondary_size = max(1, self._font_size(self.secondary_font, 10))
        label_font = self._pixel_font(self.label_font, label_size, "Segoe UI")
        value_font = self._pixel_font(self.value_font, value_size, "Segoe UI")
        unit_font = self._pixel_font(self.unit_font, unit_size, "Segoe UI")
        secondary_font = self._pixel_font(self.secondary_font, secondary_size, "Segoe UI")

        label_text = self.label
        value_text = self._formatted_value()
        unit_text = self.unit
        secondary_text = self.secondary_text

        def fit_font(text, base_font, min_size=8):
            if not text:
                return base_font
            current = base_font
            for _ in range(40):
                bbox = c.bbox(c.create_text(-10000, -10000, text=text, font=current))
                c.delete("all")
                width = 0 if not bbox else bbox[2] - bbox[0]
                if width <= usable_w or abs(int(current[1])) <= min_size:
                    return current
                current = (current[0], int(current[1] + 1) if current[1] < 0 else int(current[1] - 1), *current[2:])
            return current

        # Since bbox measurement itself creates canvas items, perform it before
        # the final four text items and redraw after choosing the sizes.
        label_font = fit_font(label_text, label_font, 7)
        value_font = fit_font(value_text, value_font, 12)
        unit_font = fit_font(unit_text, unit_font, 7)
        secondary_font = fit_font(secondary_text, secondary_font, 7)

        top = max(8, int(h * 0.08))
        label_y = top
        value_y = int(h * (0.40 if self.style.lower() == "led" else 0.46))
        unit_y = value_y + max(unit_size // 2, self.unit_gap)
        if secondary_text:
            secondary_y = h - max(6, int(h * 0.07))
            # Keep the unit and secondary row from colliding in short widgets.
            unit_y = min(unit_y, secondary_y - max(secondary_size, unit_size) - 4)
        else:
            secondary_y = None

        c.create_text(x, label_y, anchor=anchor, text=label_text,
                      fill=self.label_color, font=label_font)
        c.create_text(x, value_y, anchor=anchor, text=value_text,
                      fill=self.value_color, font=value_font)
        if unit_text:
            c.create_text(x, unit_y, anchor=anchor, text=unit_text,
                          fill=self.unit_color, font=unit_font)
        if secondary_text:
            c.create_text(x, secondary_y, anchor="s", text=secondary_text,
                          fill=self.secondary_text_color, font=secondary_font)
'''
