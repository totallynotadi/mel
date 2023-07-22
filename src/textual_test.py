import melodine as melo
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Input, Static
from textual.color import Color

class Search(Static):

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search", id="search")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        results = melo.spotify.search(event.input.value, types=['tracks'])
        for result in results['tracks']:
            yield Static(result.name)

class MelodineApp(App):
    """A Textual app to manage stopwatches."""

    BINDINGS = [("/", "search", "Search"), ("q", "quit()", "Quit")]
    CSS_PATH = "melodine.css"

    def compose(self) -> ComposeResult:
        
        yield Header()
        yield Footer()
        yield Container(Search())

if __name__ == "__main__":
    app = MelodineApp()
    app.run()
