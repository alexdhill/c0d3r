from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual.theme import Theme
from textual.reactive import reactive

from ui.primary_window import PrimaryWindow

dracula_theme = Theme(
    name="full-dracula",
    primary="#BD93F9",
    secondary="#FF79C6",
    accent="#FFB86C",
    foreground="#F8F8F2",
    background="#282A36",
    success="#50FA7B",
    warning="#F1FA8C",
    error="#FF5555",
    surface="#6272A4",
    panel="#6272A4",
    dark=True,
    variables={
        "block-cursor-text-style": "none",
        "footer-key-foreground": "#FF79C6",
        "input-selection-background": "#FF79C6 30%",
    },
)

class C0D3R(App):
    '''
    The application controller
    '''
    BINDINGS = [
        ('f', 'toggle_files', 'Toggle file explorer'),
        ('c', 'toggle_chat', 'Toggle chat window'),
        ('ctrl+`', 'toggle_terminal', 'Toggle terminal window'),
        ('cmd+s', 'save_file', 'Save open file'),
        # ('cmd+,', 'open_settings', 'Open settings'),
    ]
    def __init__(self):
        super().__init__()
        self.show_files = reactive(True)
        self.show_chat = reactive(True)
        self.show_terminal = reactive(True)

    def on_mount(self):
        """Set the theme on mount"""
        self.register_theme(dracula_theme)
        self.theme = "full-dracula"

    def compose(self):
        """Create the textual app"""
        yield Header()
        yield PrimaryWindow(
            show_files=self.show_files,
            show_chat=self.show_chat,
            show_terminal=self.show_terminal
        )
        yield Footer()

    def action_toggle_files(self):
        """Toggle the file explorer"""
        self.show_files = not self.show_files

    def action_toggle_chat(self):
        """Toggle the chat window"""
        self.show_chat = not self.show_chat

    def action_toggle_terminal(self):
        """Toggle the terminal window"""
        self.show_terminal = not self.show_terminal

    def action_save_file(self):
        """Save the currently open file"""
        pass

    def action_open_settings(self):
        """Open the settings window"""
        pass

if __name__ == "__main__":
    app = C0D3R()
    app.run()