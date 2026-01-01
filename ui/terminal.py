# """
# Terminal pane - real PTY-based terminal with color support
# """

# from textual.reactive import reactive
# from textual import events
# from rich.text import Text
# from textual.containers import Container
# from textual.widget import Widget

# import asyncio
# import fcntl
# import os
# import pty
# import shlex
# import struct
# import termios

# import pyte

# class TerminalPane(Container):
#     """Bottom pane - real interactive terminal"""
#     DEFAULT_CSS = """
#     TerminalPane {
#         background: $background;
#     }

#     Terminal {
#         height: 1fr;
#         width: 1fr;
#         background: transparent;
#     }
#     """
    
#     BINDINGS = [
#         # Override app bindings when focused
#         ("q", "nothing", ""),
#         ("f", "nothing", ""),
#         ("c", "nothing", ""),
#         ("t", "nothing", ""),
#     ]

#     cols = reactive(80)
#     rows = reactive(11)
    
#     def __init__(self, *args, **kwargs):
#         # Remove title if passed by parent, Container doesn't use it
#         kwargs.pop('title', None)
#         super().__init__(*args, **kwargs)
#         self.data_or_disconnect = None
#         self.fd = None
#         self.p_out = None
#         self.recv_queue = asyncio.Queue()
#         self.send_queue = asyncio.Queue()
#         self.event = asyncio.Event()

#     def on_mount(self) -> None:
#         """Initialize PTY after widget is mounted"""
#         self.log("TerminalPane.on_mount() called")
#         self.fd = self.open_terminal()
#         self.p_out = os.fdopen(self.fd, "w+b", 0)
#         # Start async tasks after PTY is ready
#         self.log("Creating _run task")
#         asyncio.create_task(self._run())
#         self.log("Creating _send_data task")
#         asyncio.create_task(self._send_data())
#         self.log("Tasks created")

#     def compose(self):
#         """Compose terminal pane"""
#         yield Terminal(self.send_queue, self.recv_queue, ncol = self.cols, nrow = self.rows)

#     def on_resize(self, event: events.Resize) -> None:
#         """Handle resize events to adjust terminal size"""
#         new_cols = self.size.width
#         new_rows = self.size.height
#         if new_cols != self.cols or new_rows != self.rows:
#             self.cols = new_cols
#             self.rows = new_rows
#             asyncio.create_task(self.send_queue.put(["set_size", new_rows, new_cols, 567, 573]))

#     def open_terminal(self):
#         pid, fd = pty.fork()
#         if pid == 0:
#             argv = shlex.split("zsh")
#             # Use default sizes if widget not mounted yet
#             cols = self.size.width if self.size.width > 0 else 80
#             rows = self.size.height if self.size.height > 0 else 24
#             env = dict(
#                 TERM="linux",
#                 LC_ALL="en_US.UTF-8",
#                 COLUMNS=str(cols),
#                 LINES=str(rows)
#             )
#             os.execvpe(argv[0], argv, env)
#         return fd
    
#     async def _run(self):
#         self.log("_run() started")
#         loop = asyncio.get_running_loop()
#         def on_output():
#             try:
#                 data = self.p_out.read(65536).decode()
#                 self.data_or_disconnect = data
#                 self.log(f"_run: Read {len(data)} bytes")
#                 self.event.set()
#             except Exception as e:
#                 self.log(f"_run: Error {e}")
#                 loop.remove_reader(self.p_out)
#                 self.data_or_disconnect = None
#                 self.event.set()
#         loop.add_reader(self.p_out, on_output)
#         self.log("_run: Setup message queued")
#         await self.send_queue.put(["setup", {}])
#         while True:
#             msg = await self.recv_queue.get()
#             self.log(f"_run: Received {msg[0]}")
#             if msg[0] == "stdin":
#                 self.p_out.write(msg[1].encode())
#                 self.p_out.flush()
#             elif msg[0] == "set_size":
#                 winsize = struct.pack("HH", msg[1], msg[2])
#                 fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)

#     async def _send_data(self):
#         self.log("_send_data() started")
#         while True:
#             await self.event.wait()
#             self.event.clear()
#             if self.data_or_disconnect is None:
#                 self.log("_send_data: Disconnect")
#                 await self.send_queue.put(["disconnect", 1])
#             else:
#                 self.log(f"_send_data: Sending {len(self.data_or_disconnect)} bytes to stdout")
#                 await self.send_queue.put(["stdout", self.data_or_disconnect])

# class PyteDisplay:
#     def __init__(self, lines):
#         self.lines = lines

#     def __rich_console__(self, console, options):
#         yield from self.lines


# class Terminal(Widget, can_focus=True):
#     def __init__(self, recv_queue, send_queue, ncol, nrow):
#         self.ctrl_keys = {
#             "left": "\u001b[D",
#             "right": "\u001b[C",
#             "up": "\u001b[A",
#             "down": "\u001b[B",
#         }
#         self.recv_queue = recv_queue
#         self.send_queue = send_queue
#         self.nrow = nrow
#         self.ncol = ncol
#         self._display = PyteDisplay([Text()])
#         self._screen = pyte.Screen(self.ncol, self.nrow)
#         self.stream = pyte.Stream(self._screen)
#         asyncio.create_task(self.recv())
#         super().__init__()

#     def on_mount(self) -> None:
#         """Terminal mounting to screen"""
#         self.focus()

#     def render(self):
#         return self._display
    
#     async def on_key(self, event: events.Key) -> None:
#         char = self.ctrl_keys.get(event.key) or event.character
#         await self.send_queue.put(["stdin", char])

#     async def recv(self):
#         while True:
#             message = await self.recv_queue.get()
#             cmd = message[0]
#             if cmd == "setup":
#                 await self.send_queue.put(["set_size", self.nrow, self.ncol, 567, 573])
#             elif cmd == "stdout":
#                 chars = message[1]
#                 self.stream.feed(chars)
#                 lines = []
#                 for i, line in enumerate(self._screen.display):
#                     text = Text.from_ansi(line)
#                     x = self._screen.cursor.x
#                     if i == self._screen.cursor.y and x < len(text):
#                         cursor = text[x]
#                         cursor.stylize("reverse")
#                         new_text = text[:x]
#                         new_text.append(cursor)
#                         new_text.append(text[x + 1:])
#                         text = new_text
#                     lines.append(text)
#                 self._display = PyteDisplay(lines)
#                 self.refresh()

"""
Terminal pane - real PTY-based terminal with color support
"""

from textual.reactive import reactive
from textual import events
from rich.text import Text
from textual.containers import Container
from textual.widget import Widget

import asyncio
import fcntl
import os
import pty
import shlex
import struct
import termios

import pyte

class TerminalPane(Container):
    """Bottom pane - real interactive terminal"""
    DEFAULT_CSS = """
    TerminalPane {
        background: $background;
    }

    Terminal {
        height: 1fr;
        width: 1fr;
        background: transparent;
    }
    """
    
    BINDINGS = [
        # Override app bindings when focused
        ("f", "nothing", ""),
        ("c", "nothing", ""),
        ("t", "nothing", ""),
    ]

    cols = reactive(80)
    rows = reactive(11)
    
    def __init__(self, *args, **kwargs):
        # Remove title if passed by parent, Container doesn't use it
        kwargs.pop('title', None)
        super().__init__(*args, **kwargs)
        self.data_or_disconnect = None
        self.fd = None
        self.p_out = None
        self.recv_queue = asyncio.Queue()
        self.send_queue = asyncio.Queue()
        self.event = asyncio.Event()

    def on_mount(self) -> None:
        """Initialize PTY after widget is mounted"""
        self.log("TerminalPane.on_mount() called")
        self.fd = self.open_terminal()
        self.p_out = os.fdopen(self.fd, "w+b", 0)
        # Start async tasks after PTY is ready
        self.log("Creating _run task")
        asyncio.create_task(self._run())
        self.log("Creating _send_data task")
        asyncio.create_task(self._send_data())
        self.log("Tasks created")

    def compose(self):
        """Compose terminal pane"""
        yield Terminal(self.send_queue, self.recv_queue, ncol = self.cols, nrow = self.rows)

    def on_resize(self, event: events.Resize) -> None:
        """Handle resize events to adjust terminal size"""
        new_cols = self.size.width
        new_rows = self.size.height
        if new_cols != self.cols or new_rows != self.rows:
            self.cols = new_cols
            self.rows = new_rows
            asyncio.create_task(self.send_queue.put(["set_size", new_rows, new_cols, 567, 573]))

    def open_terminal(self):
        pid, fd = pty.fork()
        if pid == 0:
            argv = shlex.split("zsh")
            # Use default sizes if widget not mounted yet
            cols = self.size.width if self.size.width > 0 else 80
            rows = self.size.height if self.size.height > 0 else 24
            env = dict(
                TERM="xterm-256color",  # Changed from "linux" for better color support
                LC_ALL="en_US.UTF-8",
                COLUMNS=str(cols),
                LINES=str(rows)
            )
            os.execvpe(argv[0], argv, env)
        return fd
    
    async def _run(self):
        self.log("_run() started")
        loop = asyncio.get_running_loop()
        def on_output():
            try:
                data = self.p_out.read(65536).decode()
                self.data_or_disconnect = data
                self.log(f"_run: Read {len(data)} bytes")
                self.event.set()
            except Exception as e:
                self.log(f"_run: Error {e}")
                loop.remove_reader(self.p_out)
                self.data_or_disconnect = None
                self.event.set()
        loop.add_reader(self.p_out, on_output)
        self.log("_run: Setup message queued")
        await self.send_queue.put(["setup", {}])
        while True:
            msg = await self.recv_queue.get()
            self.log(f"_run: Received {msg[0]}")
            if msg[0] == "stdin":
                self.p_out.write(msg[1].encode())
                self.p_out.flush()
            elif msg[0] == "set_size":
                winsize = struct.pack("HH", msg[1], msg[2])
                fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)

    async def _send_data(self):
        self.log("_send_data() started")
        while True:
            await self.event.wait()
            self.event.clear()
            if self.data_or_disconnect is None:
                self.log("_send_data: Disconnect")
                await self.send_queue.put(["disconnect", 1])
            else:
                self.log(f"_send_data: Sending {len(self.data_or_disconnect)} bytes to stdout")
                await self.send_queue.put(["stdout", self.data_or_disconnect])

class PyteDisplay:
    def __init__(self, lines):
        self.lines = lines

    def __rich_console__(self, console, options):
        yield from self.lines


class Terminal(Widget, can_focus=True):
    def __init__(self, recv_queue, send_queue, ncol, nrow):
        self.ctrl_keys = {
            "left": "\u001b[D",
            "right": "\u001b[C",
            "up": "\u001b[A",
            "down": "\u001b[B",
        }
        self.recv_queue = recv_queue
        self.send_queue = send_queue
        self.nrow = nrow
        self.ncol = ncol
        self._display = PyteDisplay([Text()])
        # Use DiffScreen to preserve formatting attributes
        self._screen = pyte.DiffScreen(self.ncol, self.nrow)
        self.stream = pyte.Stream(self._screen)
        asyncio.create_task(self.recv())
        super().__init__()

    def on_mount(self) -> None:
        """Terminal mounting to screen"""
        self.focus()

    def render(self):
        return self._display
    
    async def on_key(self, event: events.Key) -> None:
        char = self.ctrl_keys.get(event.key) or event.character
        await self.send_queue.put(["stdin", char])

    async def recv(self):
        while True:
            message = await self.recv_queue.get()
            cmd = message[0]
            if cmd == "setup":
                await self.send_queue.put(["set_size", self.nrow, self.ncol, 567, 573])
            elif cmd == "stdout":
                chars = message[1]
                self.stream.feed(chars)
                lines = []
                for y in range(self._screen.lines):
                    line_text = Text()
                    for x in range(self._screen.columns):
                        char = self._screen.buffer[y][x]
                        # Build style string from character attributes
                        style_parts = []
                        if char.bold:
                            style_parts.append("bold")
                        if char.italics:
                            style_parts.append("italic")
                        if char.underscore:
                            style_parts.append("underline")
                        if char.strikethrough:
                            style_parts.append("strike")
                        if char.reverse:
                            style_parts.append("reverse")
                        
                        # Add foreground color
                        if char.fg != "default":
                            style_parts.append(char.fg)
                        
                        # Add background color
                        if char.bg != "default":
                            style_parts.append(f"on {char.bg}")
                        
                        style = " ".join(style_parts) if style_parts else None
                        line_text.append(char.data, style=style)
                    
                    # Add cursor if on this line
                    if y == self._screen.cursor.y:
                        x = self._screen.cursor.x
                        if x < len(line_text):
                            cursor = line_text[x]
                            cursor.stylize("reverse")
                            new_text = line_text[:x]
                            new_text.append(cursor)
                            new_text.append(line_text[x + 1:])
                            line_text = new_text
                    
                    lines.append(line_text)
                
                self._display = PyteDisplay(lines)
                self.refresh()