from textual import on
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import SelectionList, Button
from textual.events import Mount
from textual.widgets.selection_list import Selection


class SelectionList(App):

    CSS_PATH = "selection_list.tcss"

    def __init__(self, options: list[str]):
        super().__init__()
        self.languages = options
        self.selected_options = []

    def compose(self) -> ComposeResult:
        selections = [Selection(language, language.lower().replace(
            ' ', '_'), initial_state=True) for language in self.languages]
        yield Vertical(
            SelectionList[str](*selections),
            Button(label="Confirm", id="confirm_button")
        )

    def on_mount(self) -> None:
        self.query_one(
            SelectionList).border_title = "Choose Which Languages to Benchmark (Compile)"

    @on(Mount)
    @on(SelectionList.SelectedChanged)
    def update_selected(self) -> None:
        self.selected_options = self.query_one(SelectionList).selected

        if len(self.selected_options) <= 0:
            self.query_one(Button).disabled = True
        else:
            self.query_one(Button).disabled = False

    @on(Button.Pressed, "#confirm_button")
    def confirm_selection(self) -> None:
        self.exit()

    def get_selected(self) -> list[str]:
        return self.selected_options
