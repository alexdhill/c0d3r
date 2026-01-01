from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive

from ui.borders import BorderDragEvent, Corner, Border
from ui.pane import Pane
from ui.terminal import TerminalPane


import asyncio
import fcntl
import os
import pty
import shlex
import struct
import termios

class PrimaryWindow(Container):
    """The primary editor window"""
    files_width = reactive(35)
    chat_width = reactive(35)
    terminal_height = reactive(11)

    DEFAULT_CSS = """
    PrimaryWindow {
        height: 100%;
        width: 100%;
    }

    #top-panes {
        min-height: 12;
        height: 1fr;
        width: 100%;
    }

    #panel-left {
        width: 35;
        min-width: 25;
    }

    #files_pane {
        # background: $primary;
        width: 100%;
        height: 100%;
    }

    #panel-middle {
        width: 1fr;
        min-width: 83;
    }

    #editor_pane {
        min-width: 83;
        height: 1fr;
        width: 1fr;
    }

    #panel-right {
        width: 35;
        min-width: 25;
    }

    #chat_pane {
        height: 1fr;
        width: 1fr;
    }

    #bottom-panes {
        min-height: 11;
        height: 11;
        width: 1fr;
    }

    #top-border, #middle-border, #bottom-border {
        height: 1;
        width: 1fr;
    }

    #terminal_pane {
        height: 1fr;
        width: 1fr;
    }
    """

    def __init__(self, show_files: bool = True, show_chat: bool = True, show_terminal: bool = True, *args, **kwargs):
        super().__init__()
        self.show_files = reactive(show_files)
        self.show_chat = reactive(show_chat)
        self.show_terminal = reactive(show_terminal)

    def compose(self):
        """Compose the primary window layout"""
        with Vertical(id='top-panes'):
            with Horizontal(id="top-border"):
                if (self.show_files):
                    with Horizontal(id="panel-left"):
                        yield Corner('top-left')
                        yield Border(orient='h', title="File Explorer")
                with Horizontal(id="panel-middle"):
                    yield Corner('top-middle-left', classes="left-border")
                    yield Border(orient='h', title="Text Editor")
                    yield Corner('top-middle-right', classes="right-border")
                if (self.show_chat):
                    with Horizontal(id="panel-right"):
                        yield Border(orient='h', title="Copilot Chat")
                        yield Corner('top-right')

            with Horizontal(id="primary-panes"):
                if (self.show_files):
                    with Horizontal(id="panel-left"):
                        yield Border()
                        yield Pane(id="files_pane", title="File Explorer")
                with Horizontal(id="panel-middle"):
                    yield Border(draggable=True, classes="left-border", id='files-bound')
                    yield Pane(id="editor_pane", title="Text Editor")
                    yield Border(draggable=True, classes="right-border", id='chat-bound')
                if (self.show_chat):
                    with Horizontal(id="panel-right"):
                        yield Pane(id="chat_pane", title="Chat")
                        yield Border()

            with Horizontal(id="middle-border"):
                if (self.show_files):
                    with Horizontal(id="panel-left"):
                        yield Corner('middle-left')
                        yield Border(orient='h', draggable=True, id="term-bound")
                with Horizontal(id="panel-middle"):
                    yield Corner('bottom-middle-left')
                    yield Border(orient='h', draggable=True, title="Terminal", id="term-bound")
                    yield Corner('bottom-middle-right')
                if (self.show_chat):
                    with Horizontal(id="panel-right"):
                        yield Border(orient='h', draggable=True, id="term-bound")
                        yield Corner('middle-right')

        with Vertical(id='bottom-panes'):
            with Horizontal():
                yield Border()
                yield TerminalPane(id="terminal_pane", title="Terminal")
                yield Border()

            with Horizontal(id="bottom-border"):
                yield Corner('bottom-left')
                yield Border(orient='h')
                yield Corner('bottom-right')

    def on_border_drag_event(self, message: BorderDragEvent) -> None:
        """Handle border dragging"""
        border_id = message.border.id
        
        if border_id == "files-bound":
            # Resize file explorer
            new_width = max(25, self.files_width + message.delta)
            self.files_width = new_width
            file_explorer = self.query("#panel-left")
            for pane in file_explorer:
                pane.styles.width = new_width
        
        elif border_id == "chat-bound":
            # Resize chat pane
            new_width = max(30, self.chat_width - message.delta)
            self.chat_width = new_width
            chat_pane = self.query("#panel-right")
            for pane in chat_pane:
                pane.styles.width = new_width
        
        elif border_id in ["term-bound"]:
            # Resize terminal (any of the horizontal borders above it)
            new_height = max(11, self.terminal_height + message.delta)
            self.terminal_height = new_height
            terminal = self.query_one("#bottom-panes")
            terminal.styles.height = new_height