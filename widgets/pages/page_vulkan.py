from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
)
from PySide6.QtCore import Qt


class PageVulkan(QWidget):
    def __init__(self, game_param: str | None = None):
        super().__init__()

        self.clipboard = QApplication.clipboard()

        self.game_name: str | None = game_param

        # create layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout_steam = QHBoxLayout()

        layout_steam.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Set style
        style_code = "color: #E83C91; padding: 5px; font-style: italic;"
        style_font = "font 12pt; font-weight: 600; padding: 5px; margin: 5px;"

        # create widgets
        label_description = QLabel(
            f"<html><strong>{self.game_name}</strong> uses Vulkan as rendering api, so you need to set environment varibles on steam launch options. Remember, this only works with Steam.</hmtl>")
        label_description.setStyleSheet("font-size: 12pt; font-weight: 100")
        label_description.setWordWrap(True)
        label_description.setAlignment(Qt.AlignmentFlag.AlignJustify)

        self.steam_command = QLabel(
            f"<html><strong>Steam: <span style='{style_code}'>WINEDLLOVERRIDES='vulkan-1=n' %command%</span></strong></html>")
        self.steam_command.setStyleSheet(style_font)
        self.btn_steam = QPushButton("Copy")

        self.btn_steam.clicked.connect(lambda: self.copy_command())

        # add widgets
        layout.addWidget(label_description)
        layout.addSpacing(12)

        layout_steam.addWidget(self.steam_command)
        layout_steam.addWidget(self.btn_steam)

        layout.addLayout(layout_steam)

        self.setLayout(layout)

    def copy_command(self) -> None:
        self.clipboard.setText('WINEDLLOVERRIDES="vulkan-1=n" %command%')
