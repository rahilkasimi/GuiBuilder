"""Domain model for a design element."""
from .dependencies import *
import copy
from .config import *

@dataclass
class DesignElement:
    elem_type: str
    x: int
    y: int
    props: Dict[str, Any] = field(default_factory=dict)
    elem_id: int = 0
    selected: bool = False
    canvas_w: float = 0.0
    canvas_h: float = 0.0
    rect_id: int = 0
    text_id: int = 0
    handle_ids: Dict[str, int] = field(default_factory=dict)
    # handler_code was removed: event-handler bodies now live exclusively
    # in the user-owned module (main_app.py), never duplicated onto the
    # element model. See CodeMixin._ensure_handler_stub() /
    # CodeGenerator.generate_user_module_scaffold().
    parent_id: Optional[int] = None
    parent_tab: Optional[int] = None
    _image_tk: Any = None
    # (path, w, h) the cached _image_tk thumbnail was built for -- lets
    # CanvasRenderer._load_thumbnail skip re-decoding the file on every
    # redraw (drag, resize, unrelated property edits) and only reload it
    # when the Image element's file or on-canvas size actually changed.
    _image_cache_key: Any = None
    _image_bg_cache: Any = None

    def __deepcopy__(self, memo):
        """Copy only persistent design state. Runtime Tk objects and image
        caches are intentionally excluded from clipboard/undo copies."""
        result = DesignElement(
            elem_type=self.elem_type,
            x=self.x, y=self.y,
            props=copy.deepcopy(self.props, memo),
            elem_id=self.elem_id,
            selected=self.selected,
            canvas_w=self.canvas_w, canvas_h=self.canvas_h,
            parent_id=self.parent_id, parent_tab=self.parent_tab,
        )
        result.rect_id = 0
        result.text_id = 0
        result.handle_ids = {}
        result._image_tk = None
        result._image_cache_key = None
        result._image_bg_cache = None
        return result

    def clone_persistent(self):
        """Return a clipboard-safe copy containing only project state."""
        return DesignElement(
            elem_type=self.elem_type, x=self.x, y=self.y,
            props=copy.deepcopy(self.props), elem_id=self.elem_id,
            selected=self.selected, canvas_w=self.canvas_w, canvas_h=self.canvas_h,
            parent_id=self.parent_id, parent_tab=self.parent_tab,
        )

    def __post_init__(self):
        if self.canvas_w == 0:
            self.canvas_w = ELEMENT_TYPES[self.elem_type]["default_size"][0]
        if self.canvas_h == 0:
            self.canvas_h = ELEMENT_TYPES[self.elem_type]["default_size"][1]
        self.canvas_w = round(float(self.canvas_w), 2)
        self.canvas_h = round(float(self.canvas_h), 2)

        # Lightweight, predictable defaults for the shared image/content styling.
        # Existing project values are preserved; only missing values are filled.
        self.props.setdefault("image_path", "")
        self.props.setdefault("image_mode", "Fit")
        self.props.setdefault("image_anchor", "Center")
        if self.elem_type in {"Label", "Button", "Checkbutton", "Radiobutton"}:
            self.props.setdefault("content_anchor", "center")
            self.props.setdefault("compound", "none")

        if self.elem_type == "Notebook":
            tabs = self.props.get("tabs")
            if not isinstance(tabs, list) or not tabs:
                self.props["tabs"] = ["Tab 1", "Tab 2"]
            self.props["active_tab"] = max(0, min(
                int(self.props.get("active_tab", 0) or 0),
                len(self.props.get("tabs", ["Tab 1"])) - 1
                )
                                            )

    @property
    def display_label(self) -> str:
        """Return the complete text shown for the element on the design canvas.

        The design canvas used to truncate text to 15 characters and append
        an ellipsis.  That was only a presentation shortcut, but it changed
        the actual on-canvas representation of the user's configured text
        and made the designer disagree with the Run Preview.  Keep the full
        value here; sizing/wrapping/clipping belongs to the renderer/widget
        geometry, not to the model value itself.
        """
        text_val = self.props.get("text")
        if text_val is not None:
            return str(text_val)
        if self.props.get("default_text") is not None:
            return str(self.props["default_text"])
        return self.elem_type

    def contains_point(self, px: int, py: int) -> bool:
        top = self.y - 14 if self.elem_type == "LabelFrame" else self.y
        return (
                    self.x <= px <= self.x + self.canvas_w and top <= py <= self.y + self.canvas_h)

    def handle_positions(self) -> Dict[str, Tuple[int, int]]:
        x, y, w, h = self.x, self.y, self.canvas_w, self.canvas_h
        mx, my = x + w // 2, y + h // 2
        return {
            "NW": (x, y), "N": (mx, y), "NE": (x + w, y), "E": (x + w, my),
            "SE": (x + w, y + h), "S": (mx, y + h), "SW": (x, y + h),
            "W": (x, my),
        }

    def hit_handle(self, px: int, py: int) -> Optional[str]:
        x, y, w = self.x, self.y, self.canvas_w
        del_x, del_y = x + w + 15, y - 15
        if abs(px - del_x) <= 10 and abs(py - del_y) <= 10:
            return "DEL"

        for name, (hx, hy) in self.handle_positions().items():
            if abs(px - hx) <= HANDLE_HALF + 2 and abs(py - hy) <= HANDLE_HALF + 2:
                return name
        return None

    def to_dict(self) -> Dict:
        return {
            "elem_type": self.elem_type,
            "x": self.x,
            "y": self.y,
            "canvas_w": self.canvas_w,
            "canvas_h": self.canvas_h,
            "props": self.props,
            "parent_id": self.parent_id,
            "parent_tab": self.parent_tab,
            "elem_id": self.elem_id,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "DesignElement":
        # JSON has no tuple type, so any prop that started life as a Python
        # tuple (font = (family, size[, weight])) comes back as a list after
        # a save/load or undo/redo round-trip through json.dumps/loads.
        # Normalize it back to a tuple here -- the one place all such
        # round-trips pass through -- so every other reader of
        # elem.props["font"] (the property panel, CodeGenerator) can assume
        # a consistent shape instead of each having to handle both.
        props = dict(data["props"])
        font_val = props.get("font")
        if isinstance(font_val, list):
            props["font"] = tuple(font_val)
        elem = cls(
            elem_type=data["elem_type"],
            x=data["x"],
            y=data["y"],
            props=props,
            elem_id=data.get("elem_id", 0),
            canvas_w=data["canvas_w"],
            canvas_h=data["canvas_h"],
            parent_id=data.get("parent_id"),
            parent_tab=data.get("parent_tab"),
        )
        return elem
