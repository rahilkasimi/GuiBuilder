"""Domain model for a design element."""
from .dependencies import *
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
    handler_code: str = ""
    parent_id: Optional[int] = None
    parent_tab: Optional[int] = None
    _image_tk: Any = None
    # (path, w, h) the cached _image_tk thumbnail was built for -- lets
    # CanvasRenderer._load_thumbnail skip re-decoding the file on every
    # redraw (drag, resize, unrelated property edits) and only reload it
    # when the Image element's file or on-canvas size actually changed.
    _image_cache_key: Any = None

    def __post_init__(self):
        if self.canvas_w == 0:
            self.canvas_w = ELEMENT_TYPES[self.elem_type]["default_size"][0]
        if self.canvas_h == 0:
            self.canvas_h = ELEMENT_TYPES[self.elem_type]["default_size"][1]
        self.canvas_w = round(float(self.canvas_w), 2)
        self.canvas_h = round(float(self.canvas_h), 2)
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
        text_val = self.props.get("text")
        if text_val is not None:
            label = str(text_val)
        elif self.props.get("default_text") is not None:
            label = str(self.props["default_text"])
        else:
            label = self.elem_type
        return (label[:15] + "…") if len(label) > 15 else label

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
            "handler_code": self.handler_code,
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
            handler_code=data.get("handler_code", ""),
            parent_id=data.get("parent_id"),
            parent_tab=data.get("parent_tab"),
        )
        return elem
