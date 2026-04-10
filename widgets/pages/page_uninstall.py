from scripts_core.script_manager import update_manager, read_manager_content
from scripts_core.script_uninstall import UninstallWorker
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QProgressBar
)
from PySide6.QtCore import QThread, Qt, Slot


class PageUninstall(QWidget):

    def __init__(self):
        super().__init__()

        self.games: list[str] = read_manager_content("game")
        self.games_dir: list[str] = read_manager_content("dir")

        # create layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # create widgets
        label_description = QLabel("Select a game and click uninstall")
        label_description.setStyleSheet("font-size: 12pt; font-weight: 100")
        label_description.setWordWrap(True)

        self.game_list = QListWidget(self)
        self.game_list.setUpdatesEnabled(True)
        self.add_items(self.games, self.game_list)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.btn_uninstall = QPushButton("Uninstall")
        self.btn_uninstall.clicked.connect(self.on_uninstall_clicked)

        # add widgets
        layout.addWidget(label_description)
        layout.addWidget(self.game_list)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.btn_uninstall)
        self.setLayout(layout)

    def add_items(self, games: list[str], widget_list: QListWidget):
        index: int = 1

        for game in games:
            newItem: QListWidgetItem = QListWidgetItem()
            newItem.setText(game)
            widget_list.insertItem(index, newItem)

            index = index + 1

    def on_uninstall_clicked(self) -> None:
        current_row: int = self.game_list.currentRow()

        # Try to prevent crashes IF the user click on uninstall without selecting anything. But I doubt
        if current_row < 0:
            return

        self.start_uninstalling(current_row)

    def start_uninstalling(self, current_row: int) -> None:
        self.btn_uninstall.setEnabled(False)

        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFormat("Uninstalling...")

        game_path: str = self.games_dir[current_row]

        self.uninstall_thread: QThread = QThread()
        self.uninstall_worker: UninstallWorker = UninstallWorker(
            current_row, game_path)

        self.uninstall_worker.moveToThread(self.uninstall_thread)

        # started is a default signal, not a custom by me
        self.uninstall_thread.started.connect(self.uninstall_worker.run)

        self.uninstall_worker.finished.connect(self.on_uninstall_finished)
        self.uninstall_worker.error.connect(self.on_uninstall_error)

        self.uninstall_worker.finished.connect(self.uninstall_thread.quit)
        self.uninstall_worker.finished.connect(
            self.uninstall_worker.deleteLater)
        self.uninstall_thread.finished.connect(
            self.uninstall_thread.deleteLater)

        self.uninstall_thread.start()

    @Slot(str)
    def on_uninstall_error(self, message: str) -> None:
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(f"Error: {message}")
        self.progress_bar.setEnabled(True)

    @Slot(bool)
    def on_uninstall_finished(self, success: bool) -> None:
        if success:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("Uninstalled!")

            self.btn_uninstall.setEnabled(True)

            current_row: int = self.game_list.currentRow()

            self.game_list.takeItem(current_row)
            self.game_list.updateEditorData()
            self.game_list.reset()
            update_manager(current_row)

            self.games = read_manager_content("game")
            self.games_dir = read_manager_content("dir")
