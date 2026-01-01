from textual.widgets import Static
from textual.reactive import reactive
from textual import events

from rich.console import RenderableType
from rich.text import Text

class BorderDragEvent(events.Message):
    """Message sent when border is dragged"""
    
    def __init__(self, border, delta: int, orient: str):
        super().__init__()
        self.border = border
        self.delta = delta
        self.orient = orient

class Border(Static):
    """Base class for borders"""
    DEFAULT_CSS = """
    Border {
        background: transparent;
    }
    
    Border.v {
        width: 1;
        height: 1fr;
        color: $primary;
    }
    
    Border.h {
        width: 1fr;
        height: 1;
        color: $primary;
    }
    
    Border.draggable:hover {
        color: $accent;
    }

    Border.draggable.active {
        color: $accent;
    }
    """
    
    is_dragging = reactive(False)
    is_active = reactive(False)

    def __init__(self, orient="v", draggable=False, title=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orient = orient
        self.draggable = draggable
        self.title = title
        self.drag_start = None
        self.add_class(orient)
        if draggable:
            self.add_class("draggable")

    def render(self) -> RenderableType:
        if self.orient == "h":
            char = "━" if (self.is_dragging or self.is_active) else "─"
            width = self.size.width
            if self.title:
                title_str = f"{self.title}"
                title_len = len(title_str)
                if title_len < width-2:
                    side_len = (width - title_len) // 2
                    line = char * side_len + title_str + char * (width - side_len - title_len)
                    return Text(line)
            return Text(char * width)
        else:
            char = "│"
            height = self.size.height
            return Text("\n".join([char] * height))
        
    def on_mouse_down(self, event: events.MouseDown) -> None:
        if self.draggable:
            self.is_dragging = True
            self.add_class("active")
            self.drag_start = (event.screen_x, event.screen_y)
            self.capture_mouse()

    def on_mouse_up(self, event: events.MouseUp) -> None:
        if self.draggable:
            self.is_dragging = False
            self.remove_class("active")
            self.drag_start = None
            self.release_mouse()

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if self.draggable and self.is_dragging and self.drag_start:
            if self.orient == "v":
                delta = event.screen_x - self.drag_start[0]
                if delta != 0:
                    self.post_message(BorderDragEvent(self, delta, "vertical"))
                    self.drag_start = (event.screen_x, event.screen_y)
            else:
                delta = self.drag_start[1] - event.screen_y
                if delta != 0:
                    self.post_message(BorderDragEvent(self, delta, "horizontal"))
                    self.drag_start = (event.screen_x, event.screen_y)

class Corner(Static):
    """A corner junction between borders"""
    DEFAULT_CSS = """
    Corner {
        width: 1;
        height: 1;
        background: transparent;
        color: $primary;
    }

    Corner.draggable.active {
        color: $accent;
    }
    """

    def __init__(self, position="top-left", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.position = position

    def render(self) -> RenderableType:
        corners = {
            "top": "─",
            "top-left": "┌",
            "top-middle-left": "┬",
            "top-middle-right": "┬",
            "top-right": "┐",
            "bottom": "─",
            "bottom-left": "└",
            "bottom-middle-left": "┴",
            "bottom-middle-right": "┴",
            "bottom-right": "┘",
            "middle-left": "├",
            "middle-middle-left": "┼",
            "middle-middle-right": "┼",
            "middle-right": "┤"
        }
        char = corners.get(self.position, "┼")
        return Text(char)