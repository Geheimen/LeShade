import shutil
from utils.utils import EXTRACT_PATH, generic_download
from zipfile import BadZipFile, ZipFile
from pathlib import Path
import subprocess
import os
import re

VULKANRT_URL: str = "https://sdk.lunarg.com/sdk/download/1.4.341.0/windows/VulkanRT-X64-1.4.341.0-Installer.exe"
# ICU_URL: str = "https://github.com/unicode-org/icu/releases/download/release-78.3/icu4c-78.3-Win64-MSVC2022.zip"
ICU_URL: str = "https://github.com/Ishidawg/reshade-installer-linux/raw/main/icu_dll"

# Distination directories for download stuff
VULKANRT_PATH: str = os.path.join(EXTRACT_PATH, "vulkanrt.exe")
ICU_PATH: str = os.path.join(EXTRACT_PATH, "ICU")
ICU_DIR: str = os.path.join(EXTRACT_PATH, "ICU")


class InstallVukan():

    def __init__(self, game_dir: str) -> None:
        super().__init__()

        self.executable_path: Path = Path(game_dir)
        self.game_name: str = self.get_game_directory_name(
            self.executable_path)
        self.steamapps_dir: str = self.get_steamapps_directory(
            self.executable_path)
        self.app_id: str = self.get_steam_appid(
            self.steamapps_dir, self.game_name)
        self.system32_prefix: str = ""

        print(self.executable_path)
        print(self.game_name)
        print(self.steamapps_dir)
        print(self.app_id)

        # Download VULKANRT
        self.download_vulkanRT()

        # Download, extract and move ICU
        self.download_ICU()
        # self.extract_icu()
        self.move_icu_files_to_sys32(self.steamapps_dir, self.app_id)

        # Install vulkanRT
        self.install_vulkanRT(self.app_id)

    def download_vulkanRT(self) -> None:
        if os.path.exists(VULKANRT_PATH):
            return

        generic_download(VULKANRT_URL, VULKANRT_PATH)

    def download_ICU(self) -> None:
        if os.path.exists(ICU_DIR) or os.path.exists(ICU_PATH):
            return

        generic_download(ICU_URL, ICU_PATH)

    def extract_icu(self) -> None:
        os.makedirs(ICU_DIR, exist_ok=True)

        try:
            with ZipFile(ICU_PATH, "r") as zip_file:
                zip_file.extractall(ICU_DIR)
        except Exception as e:
            raise BadZipFile(f"Failed to unzip: {e}")

    def move_icu_files_to_sys32(self, steamapps_dir, app_id) -> None:
        system32_path: str = os.path.join(
            steamapps_dir, "compatdata", app_id, "pfx", "drive_c", "windows", "system32")

        try:
            shutil.copytree(ICU_DIR, system32_path, dirs_exist_ok=True)
        except Exception as e:
            raise IOError(f"Failed to move ICU files to system32: {e}")

    def install_vulkanRT(self, app_id: str) -> None:
        wine_wrap_command: str = f"wine {VULKANRT_PATH} /S"

        full_command: list[str] = [
            "protontricks", "-c", wine_wrap_command, app_id]

        try:
            run = subprocess.run(full_command, check=True,
                                 capture_output=True, text=True)

            print("VulkanRT Installed!")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to install VulkanRT: {e.stderr}")
        except FileNotFoundError:
            raise Exception(f"You need to install protontricks or the command was not found.\nOn arch: sudo pacman -S protontricks\nOn Ubuntu and Debian-Based System: sudo apt install protontricks -y\nOn Fedora: sudo dnf install https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm && sudo dnf install protontricks -y")

    def get_game_directory_name(self, executable_path: Path) -> str:
        split_path: tuple[str, ...] = executable_path.parts
        common_index: int = split_path.index("common")
        directory_name: str = split_path[common_index + 1]

        return directory_name

    def get_steamapps_directory(self, executable_path: Path) -> str:
        steam_apps: str = ""

        for parent in executable_path.parents:
            if parent.name == "steamapps":
                steam_apps = str(parent)
                break

        if not steam_apps:
            raise ValueError("Error: steamapps dir was not found")

        return steam_apps

    def get_steam_appid(self, steamapps_dir: str, game_name: str) -> str:
        app_id: str = ""

        for manifest_file in Path(steamapps_dir).glob("appmanifest_*.acf"):
            try:
                manifest_data: str = manifest_file.read_text(
                    encoding='utf-8', errors='ignore')

                pattern = rf'"installdir"\s+"{re.escape(game_name)}"'

                if re.search(pattern, manifest_data, re.IGNORECASE):
                    match = re.search(
                        r'appmanifest_(\d+)\.acf', manifest_file.name)

                    if match:
                        app_id = match.group(1)
                        break
            except Exception as e:
                raise Exception(f"Error getting the app_id: {e}")

        if not app_id:
            raise ValueError("Error: app_id is empty")

        return app_id
