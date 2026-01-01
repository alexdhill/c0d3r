from textual.widgets import Static
from rich.console import RenderableType
from rich.text import Text

class Pane(Static):
    DEFAULT_CSS = """
        Pane {
            height: 1fr;
            width: 1fr;
            overflow: hidden;
        }
    """

    def __init__(self, title: str, min_width: int = 10, min_height: int = 3, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pane_title = title
        self.min_width = min_width
        self.min_height = min_height
    
    def render(self) -> RenderableType:
        """Render just the content, no borders"""
        width = self.size.width
        height = self.size.height
        
        content_lines = self.get_content_lines(width, height)
        lines = []
        
        for line in content_lines:
            line_str = str(line) if not isinstance(line, str) else line
            lines.append(line_str.ljust(width)[:width])
        
        # Pad to exact height
        while len(lines) < height:
            lines.append(" " * width)
        
        return Text("\n".join(lines[:height]))
    
    def get_content_lines(self, width: int, height: int) -> list[str]:
        """Override this to provide content - returns list of strings"""
        return [""] * height