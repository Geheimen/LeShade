from os.path import isfile
from scripts_core.script_manager import read_boolean_flags, update_manager, read_manager_content
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget
)
from PySide6.QtCore import Qt
import shutil
import glob
import os

from scripts_core.script_vulkan import VULKANRT_PATH, InstallVukan


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

        self.btn_uninstall = QPushButton("Uninstall")

        self.btn_uninstall.clicked.connect(self.on_uninstall_clicked)

        # add widgets
        layout.addWidget(label_description)
        layout.addWidget(self.game_list)
        layout.addWidget(self.btn_uninstall)
        self.setLayout(layout)

    def on_uninstall_clicked(self) -> None:
        self.uninstall_reshade(
            self.game_list, self.games_dir)

    def add_items(self, games: list[str], widget_list: QListWidget):
        index: int = 1

        for game in games:
            newItem: QListWidgetItem = QListWidgetItem()
            newItem.setText(game)
            widget_list.insertItem(index, newItem)

            index = index + 1

    def uninstall_reshade(self, widget_list: QListWidget, dir_list: list[str]):
        try:
            current_row: int = widget_list.currentRow()
            game_path: str = dir_list[current_row]

            shaders_dir: str = os.path.join(game_path, "reshade-shaders")

            # I dont remember what I did to this string be a bool
            have_hlsl_compiler: str = read_boolean_flags(
                current_row, "hlsl_compiler")

            is_vulkan: str = read_boolean_flags(current_row, "vulkan")

            remove_files_complete: list[str] = [
                "opengl32.dll", "d3d8.dll", "d3d9.dll", "d3d10.dll", "d3d11.dll", "dxgi.dll"]
            if not have_hlsl_compiler:
                remove_files_complete.append("d3dcompiler_47.dll")

            remove_files_pattern: list[str] = [
                "ReShade*.*",
                "reshade*.*",
                "renodx*.*"
            ]

            if os.path.exists(game_path):
                if os.path.exists(shaders_dir):
                    shutil.rmtree(shaders_dir)

                for file in remove_files_complete:
                    if file in os.listdir(game_path):
                        os.remove(os.path.join(game_path, file))

                for pattern in remove_files_pattern:
                    file_match: str = os.path.join(game_path, pattern)
                    glob_result: list[str] = glob.glob(file_match)

                    for file_found in glob_result:
                        if os.path.exists(file_found):
                            os.remove(file_found)

                if is_vulkan:
                    reshade_dir: str = read_manager_content(
                        "reshade_pfx_dir")[current_row]
                    system32_dir: str = read_manager_content(
                        "system32_pfx_dir")[current_row]
                    vulkanrt_dir: str = read_manager_content(
                        "vulkanrt_pfx_dir")[current_row]

                    if reshade_dir and os.path.exists(reshade_dir):
                        shutil.rmtree(reshade_dir)

                    if vulkanrt_dir and os.path.exists(vulkanrt_dir):
                        shutil.rmtree(vulkanrt_dir)

                    if system32_dir and os.path.exists(system32_dir):
                        icu_file_path: str = ""

                        icu_files: list[str] = ["derb.exe", "genbrk.exe", "genccode.exe", "genu.exe",
                                                "gencmn.exe", "gencnval.exe", "gendict.exe", "gennorm2.exe",
                                                "genrb.exe", "gensprep.exe", "icudt.dll", "icudt78.dll",
                                                "icuexportdata.exe", "icuin.dll", "icuin78.dll", "icuinfo.exe",
                                                "icuio.dll", "icuio78.dll", "icupkg.exe", "icutest.exe",
                                                "icutest78.exe", "icutu.dll", "icutu78.dll", "icuuc.dll",
                                                "icuuc78.dll", "makeconv.exe", "pkgdata.exe", "testplug.dll",
                                                "uconv.exe"]

                        for file in icu_files:
                            icu_file_path = os.path.join(system32_dir, file)

                            if os.path.isfile(icu_file_path):
                                os.remove(icu_file_path)

                    InstallVukan(game_path, True)

            # Remove game from list and reset
            widget_list.takeItem(current_row)
            widget_list.updateEditorData()
            widget_list.reset()

            # update the values so we can get the correct game_path
            update_manager(current_row)
            self.games = read_manager_content("game")
            self.games_dir = read_manager_content("dir")
        except IndexError as e:
            print(e)
