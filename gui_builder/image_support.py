"""Small runtime image helper for GuiBuilder generated applications."""
import os
import tkinter as tk
from PIL import Image, ImageTk

ANCHORS = {
    "top-left": (0,0), "top": (0.5,0), "top-right": (1,0),
    "left": (0,0.5), "center": (0.5,0.5), "right": (1,0.5),
    "bottom-left": (0,1), "bottom": (0.5,1), "bottom-right": (1,1),
}

def _path(path):
    path=str(path or "").strip()
    if not path: return ""
    if os.path.isabs(path): return path
    return os.path.join(os.path.dirname(__file__), path)

def _image(path, w, h, mode="Fit", anchor="Center"):
    img=Image.open(_path(path)).convert("RGBA")
    w=max(1,int(w)); h=max(1,int(h)); iw,ih=img.size
    m=str(mode or "Fit").lower(); a=str(anchor or "Center").lower()
    ox=oy=0
    if m=="stretch":
        img=img.resize((w,h),Image.Resampling.LANCZOS)
    elif m in ("fill","cover"):
        sc=max(w/iw,h/ih); nw=max(1,int(iw*sc)); nh=max(1,int(ih*sc))
        img=img.resize((nw,nh),Image.Resampling.LANCZOS)
        l=max(0,(nw-w)//2); t=max(0,(nh-h)//2); img=img.crop((l,t,l+w,t+h))
    elif m in ("fit","contain"):
        sc=min(w/iw,h/ih); nw=max(1,int(iw*sc)); nh=max(1,int(ih*sc))
        img=img.resize((nw,nh),Image.Resampling.LANCZOS); ox=(w-nw)//2; oy=(h-nh)//2
    elif m in ("tile","repeat"):
        base=Image.new("RGBA",(w,h),(0,0,0,0))
        for yy in range(0,h,img.height):
            for xx in range(0,w,img.width): base.alpha_composite(img,(xx,yy))
        img=base
    else:
        ax,ay=ANCHORS.get(a,ANCHORS["center"])
        ox=int(round((w-img.width)*ax)); oy=int(round((h-img.height)*ay))
        # Crop an oversized image to the widget rectangle rather than letting it bleed out.
        if img.width>w or img.height>h:
            left=max(0,min(img.width-w,-ox)); top=max(0,min(img.height-h,-oy))
            img=img.crop((left,top,left+min(w,img.width),top+min(h,img.height))); ox=max(0,ox); oy=max(0,oy)
    return ImageTk.PhotoImage(img), ox, oy

def apply_background(widget, path, mode="Fit", anchor="Center"):
    if not path: return
    try:
        widget._gb_image_path=path; widget._gb_image_mode=mode; widget._gb_image_anchor=anchor
        if hasattr(widget,"set_background_image"):
            widget.set_background_image(path,mode,anchor); return
        if isinstance(widget, tk.Canvas):
            def paint(_=None):
                photo,ox,oy=_image(path,widget.winfo_width(),widget.winfo_height(),mode,anchor)
                widget._gb_image_ref=photo; widget.delete("_gb_background")
                widget.create_image(ox,oy,image=photo,anchor="nw",tags="_gb_background"); widget.tag_lower("_gb_background")
            widget.bind("<Configure>",paint,add="+"); widget.after_idle(paint); return
        if isinstance(widget,(tk.Button,tk.Label,tk.Checkbutton,tk.Radiobutton)):
            def paint(_=None):
                photo,_,_=_image(path,widget.winfo_width(),widget.winfo_height(),mode,anchor)
                widget._gb_image_ref=photo; widget.configure(image=photo,compound=getattr(widget,"_gb_compound","center"))
            widget.bind("<Configure>",paint,add="+"); widget.after_idle(paint); return
        holder=getattr(widget,"_gb_holder",None)
        if holder is None:
            holder=tk.Label(widget,bd=0,highlightthickness=0)
            holder.place(x=0,y=0,relwidth=1,relheight=1); holder.lower(); widget._gb_holder=holder
        def paint(_=None):
            photo,_,_=_image(path,holder.winfo_width(),holder.winfo_height(),mode,anchor)
            holder._gb_image_ref=photo; holder.configure(image=photo); holder.lower()
        holder.bind("<Configure>",paint); holder.after_idle(paint)
    except Exception:
        pass

def apply_content(widget, anchor="center", compound="none"):
    try:
        widget._gb_compound=compound
        if anchor: widget.configure(anchor=anchor)
        if compound and compound!="none": widget.configure(compound=compound)
    except Exception:
        pass


class BuilderDateTimePicker(tk.Frame):
    """Compact combo-style date/time picker used by generated applications.

    The control itself contains only a read-only display and a drop-down
    button. Calendar/time editing happens in a popup, so the designer/runtime
    never shows a separate time box inside the element.
    """
    def __init__(self, master, display_format="Date & Time", custom_format="",
                 initial_value="", date_pattern="yyyy-mm-dd", time_format="24h",
                 font=("Segoe UI", 9), bg="#FFFFFF", fg="#212121", **kwargs):
        super().__init__(master, bg=bg, bd=1, relief="solid", highlightthickness=0, **kwargs)
        self._gb_bg = bg
        self._gb_fg = fg
        self._gb_font = font if isinstance(font, (tuple, list)) else ("Segoe UI", 9)
        self.display_format = str(display_format or "Date & Time")
        self.custom_format = str(custom_format or "")
        self.date_pattern = str(date_pattern or "yyyy-mm-dd")
        self.time_format = str(time_format or "24h")
        self.value = str(initial_value or "").strip()
        self._popup = None
        self._calendar = None
        self._display_var = tk.StringVar(value="")
        self._entry = tk.Entry(self, textvariable=self._display_var, state="readonly",
                               readonlybackground=bg, fg=fg, relief="flat",
                               bd=0, highlightthickness=0, font=self._gb_font)
        self._entry.pack(side="left", fill="both", expand=True, padx=(6, 0))
        self._button = tk.Button(self, text="▼", command=self._open_popup, relief="flat",
                                 bd=0, bg=bg, fg=fg, activebackground=bg,
                                 activeforeground=fg, padx=6, cursor="hand2", font=self._gb_font)
        self._button.pack(side="right", fill="y")
        self._entry.bind("<Button-1>", lambda _e: self._open_popup())
        self.bind("<Configure>", self._on_configure)
        self._refresh_display()

    def _on_configure(self, _event=None):
        try:
            self._entry.configure(font=self._gb_font)
            self._button.configure(font=self._gb_font)
        except Exception:
            pass

    def _format_pattern(self):
        if self.display_format == "Custom" and self.custom_format:
            return self._custom_pattern_to_strftime(self.custom_format)
        if self.display_format == "Date":
            return self._tk_date_pattern_to_strftime(self.date_pattern)
        if self.display_format == "Time":
            return "%H:%M:%S" if self.time_format == "24h" else "%I:%M:%S %p"
        date_fmt = self._tk_date_pattern_to_strftime(self.date_pattern)
        time_fmt = "%H:%M:%S" if self.time_format == "24h" else "%I:%M:%S %p"
        return f"{date_fmt} {time_fmt}"

    @staticmethod
    def _tk_date_pattern_to_strftime(pattern):
        p = str(pattern or "yyyy-mm-dd")
        return (p.replace("yyyy", "%Y").replace("YYYY", "%Y")
                 .replace("mm", "%m").replace("MM", "%m")
                 .replace("dd", "%d").replace("DD", "%d"))

    @classmethod
    def _custom_pattern_to_strftime(cls, pattern):
        # Accept both familiar date/time tokens (yyyy, dd, HH, hh, ss, AM/PM)
        # and native Python strftime directives.
        p = str(pattern or "").strip()
        if "%" in p:
            return p
        replacements = [
            ("yyyy", "%Y"), ("YYYY", "%Y"),
            ("dd", "%d"), ("DD", "%d"),
            ("hh", "%I"), ("HH", "%H"),
            ("mm", "%M"), ("MM", "%M"),
            ("ss", "%S"), ("SS", "%S"),
            ("a", "%p"), ("A", "%p"),
        ]
        for src, dst in replacements:
            p = p.replace(src, dst)
        return p

    def _parse_value(self):
        from datetime import datetime
        raw = self.value.strip().replace("T", " ")
        patterns = [
            "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
            "%d/%m/%Y %H:%M", "%d/%m/%Y", "%m/%d/%Y %H:%M", "%m/%d/%Y",
            "%d-%m-%Y %H:%M", "%d-%m-%Y", "%Y/%m/%d %H:%M", "%Y/%m/%d",
            "%H:%M:%S", "%H:%M", "%I:%M %p"
        ]
        for pat in patterns:
            try:
                return datetime.strptime(raw, pat)
            except ValueError:
                pass
        return datetime.now()

    def _refresh_display(self):
        try:
            dt = self._parse_value()
            self._display_var.set(dt.strftime(self._format_pattern()))
        except Exception:
            self._display_var.set(self.value)

    def _open_popup(self):
        if self._popup is not None and self._popup.winfo_exists():
            self._popup.lift(); return
        from datetime import datetime
        try:
            from tkcalendar import Calendar
        except Exception:
            return
        # Create the popup withdrawn so the window manager never paints it at
        # its default location (commonly 0,0).  We fully build/layout it,
        # calculate the final screen coordinates, set the geometry, and only
        # then map it.  This removes the visible jump when opening the picker.
        self._popup = tk.Toplevel(self)
        self._popup.withdraw()
        self._popup.title("Select date and time")
        self._popup.transient(self.winfo_toplevel())
        self._popup.resizable(False, False)
        self._popup.protocol("WM_DELETE_WINDOW", self._close_popup)
        dt = self._parse_value()
        cal = Calendar(self._popup, selectmode="day", date_pattern=self.date_pattern)
        cal.pack(padx=8, pady=(8, 4))
        try: cal.selection_set(dt.date())
        except Exception: pass
        self._calendar = cal

        bottom = tk.Frame(self._popup)
        bottom.pack(fill="x", padx=8, pady=(2, 8))
        pattern = self._format_pattern()
        needs_time = self.display_format in ("Date & Time", "Custom", "Time") and any(x in pattern for x in ("%H", "%I", "%M", "%S"))
        if needs_time:
            tk.Label(bottom, text="Time").pack(side="left")
            h0 = dt.hour
            if self.time_format == "12h" and "%H" not in pattern:
                hour_display = ((h0 - 1) % 12) + 1
                self._hour_var = tk.StringVar(value=f"{hour_display:02d}")
                self._ampm_var = tk.StringVar(value="PM" if h0 >= 12 else "AM")
                tk.Spinbox(bottom, from_=1, to=12, width=3, textvariable=self._hour_var, format="%02.0f").pack(side="left", padx=3)
            else:
                self._hour_var = tk.StringVar(value=f"{h0:02d}")
                tk.Spinbox(bottom, from_=0, to=23, width=3, textvariable=self._hour_var, format="%02.0f").pack(side="left", padx=3)
            tk.Label(bottom, text=":").pack(side="left")
            self._minute_var = tk.StringVar(value=f"{dt.minute:02d}")
            tk.Spinbox(bottom, from_=0, to=59, width=3, textvariable=self._minute_var, format="%02.0f").pack(side="left")
            if self.time_format == "12h" and "%H" not in pattern:
                tk.Label(bottom, text=" ").pack(side="left")
                tk.OptionMenu(bottom, self._ampm_var, "AM", "PM").pack(side="left")
        tk.Button(bottom, text="OK", command=self._accept_popup, width=8).pack(side="right")
        self._popup.bind("<Escape>", lambda _e: self._close_popup())

        # Position the popup before mapping it.  update_idletasks() gives the
        # final requested size while the window is still withdrawn, so there
        # is no intermediate (0,0) paint.
        try:
            self._popup.update_idletasks()
            x = self.winfo_rootx()
            y = self.winfo_rooty() + self.winfo_height()
            self._popup.geometry(f"+{x}+{y}")
            self._popup.deiconify()
            self._popup.grab_set()
            self._popup.focus_force()
        except tk.TclError:
            self._close_popup()

    def _accept_popup(self):
        from datetime import datetime
        dt = self._parse_value()
        try:
            if self._calendar is not None:
                d = self._calendar.selection_get()
                dt = datetime.combine(d, dt.time())
            if hasattr(self, "_hour_var"):
                raw_hour = int(self._hour_var.get())
                minute = max(0, min(59, int(self._minute_var.get())))
                if hasattr(self, "_ampm_var"):
                    hour = raw_hour % 12
                    if self._ampm_var.get().upper() == "PM":
                        hour += 12
                else:
                    hour = max(0, min(23, raw_hour))
                dt = dt.replace(hour=hour, minute=minute)
            self.value = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass
        self._refresh_display()
        self._close_popup()
        self.event_generate("<<DateTimeChanged>>")

    def _close_popup(self):
        p = self._popup
        self._popup = None
        self._calendar = None
        if p is not None:
            try: p.grab_release()
            except Exception: pass
            try: p.destroy()
            except Exception: pass

    def get(self):
        return self.value
