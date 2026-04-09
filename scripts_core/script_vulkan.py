from utils.utils import EXTRACT_PATH, download, get_game_directory_name, get_steam_appid, get_steamapps_directory, unzip_file
from pathlib import Path
import subprocess
import textwrap
import shutil
import glob
import os

VULKANRT_URL: str = "https://sdk.lunarg.com/sdk/download/1.4.341.0/windows/VulkanRT-X64-1.4.341.0-Installer.exe"
ICU_URL: str = "https://raw.githubusercontent.com/Ishidawg/LeShade/refs/heads/main/icu_dll/icu_dll.zip"

# Distination directories for download stuff
VULKANRT_PATH: str = os.path.join(EXTRACT_PATH, "vulkanrt.exe")
ICU_PATH: str = os.path.join(EXTRACT_PATH, "icu.zip")
ICU_DIR: str = os.path.join(EXTRACT_PATH, "ICU")

ADD_REG_PATH: str = os.path.join(EXTRACT_PATH, "leshade.reg")
REMOVE_REG_PATH: str = os.path.join(EXTRACT_PATH, "remove.reg")


class InstallVukan():
    def __init__(self, game_dir: str, remove: bool = False) -> None:
        super().__init__()

        self.executable_path: Path = Path(game_dir)
        self.game_name: str = get_game_directory_name(self.executable_path)
        self.steamapps_dir: str = get_steamapps_directory(self.executable_path)
        self.app_id: str = get_steam_appid(self.steamapps_dir, self.game_name)

        self.drive_c_path: str = os.path.join(
            self.steamapps_dir,
            "compatdata",
            self.app_id,
            "pfx",
            "drive_c"
        )

        self.system32_prefix: str = os.path.join(
            self.drive_c_path,
            "windows",
            "system32"
        )

        self.reshade_prefix: str = os.path.join(
            self.drive_c_path,
            "ProgramData",
            "ReShade"
        )

        if remove:
            os.makedirs(EXTRACT_PATH, exist_ok=True)
            self.create_remove_leshade_reg(REMOVE_REG_PATH, True)
            self.add_remove_registry_keys(self.app_id, REMOVE_REG_PATH, True)
            return

    def run(self) -> None:
        self.run_ICU()
        self.run_vulkanRT(self.app_id)
        self.run_reshade_actions(
            self.reshade_prefix, self.executable_path, self.app_id)

    def download_ICU(self) -> None:
        download(url=ICU_URL, file_name=ICU_PATH)

    def extract_icu(self) -> None:
        os.makedirs(ICU_DIR, exist_ok=True)
        unzip_file(ICU_PATH, ICU_DIR)

    def move_icu_files_to_sys32(self, system32_path: str) -> None:
        try:
            shutil.copytree(ICU_DIR, system32_path, dirs_exist_ok=True)
        except Exception as e:
            raise IOError(f"Failed to move ICU files to system32: {e}")

    def run_ICU(self) -> None:
        self.download_ICU()
        self.extract_icu()
        self.move_icu_files_to_sys32(self.system32_prefix)

    def download_vulkanRT(self) -> None:
        download(url=VULKANRT_URL, file_name=VULKANRT_PATH)

    def install_vulkanRT(self, app_id: str) -> None:
        wine_wrap_command: str = f"wine '{VULKANRT_PATH}' /S"

        full_command: list[str] = [
            "protontricks", "-c", wine_wrap_command, app_id]

        try:
            subprocess.run(full_command, check=True,
                           capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to install VulkanRT: {e.stderr}")
        except FileNotFoundError:
            raise Exception(
                f"You need to install protontricks or the command was not found.")

    def run_vulkanRT(self, steam_id: str) -> None:
        self.download_vulkanRT()
        self.install_vulkanRT(steam_id)

    def move_reshade_files(self, reshade_prefix: str) -> None:
        os.makedirs(reshade_prefix, exist_ok=True)

        reshade_files: list[str] = glob.glob(
            os.path.join(EXTRACT_PATH, "ReShade*"), recursive=True)

        for file in reshade_files:
            shutil.copy(file, reshade_prefix)

    def create_reshade_apps(self, reshade_prefix: str, game_executable_path: Path) -> None:
        reshade_apps: str = os.path.join(reshade_prefix, "ReShadeApps.ini")
        fix_game_exe_path: str = str(game_executable_path).replace("/", "\\")

        app_data: str = f"Apps=Z:{fix_game_exe_path}"

        if not os.path.exists(reshade_apps):
            try:
                with open(reshade_apps, "w") as file:
                    file.write(app_data)
            except FileExistsError as e:
                print(e)

    def create_remove_leshade_reg(self, reg_path: str, remove: bool = False) -> None:
        registry_add_content: str = textwrap.dedent(r"""
            Windows Registry Editor Version 5.00

            [HKEY_CURRENT_USER\Software\Khronos\Vulkan\ImplicitLayers]
            "C:\\ProgramData\\ReShade\\ReShade64.json"=dword:00000000

            [HKEY_LOCAL_MACHINE\Software\Khronos\Vulkan\ImplicitLayers]
            "C:\\ProgramData\\ReShade\\ReShade64.json"=dword:00000000

            [HKEY_LOCAL_MACHINE\Software\Wow6432Node\Khronos\Vulkan\ImplicitLayers]
            "C:\\ProgramData\\ReShade\\ReShade32.json"=dword:00000000

            [HKEY_CURRENT_USER\Software\Wine\DllOverrides]
            "vulkan-1"="native"
        """).strip()

        registry_remove_content: str = textwrap.dedent(r"""
            Windows Registry Editor Version 5.00

            [-HKEY_CURRENT_USER\Software\Khronos\Vulkan\ImplicitLayers]
            [-HKEY_LOCAL_MACHINE\Software\Khronos\Vulkan\ImplicitLayers]
            [-HKEY_LOCAL_MACHINE\Software\Wow6432Node\Khronos\Vulkan\ImplicitLayers]
            [HKEY_CURRENT_USER\Software\Wine\DllOverrides]
            "vulkan-1"=-
        """).strip()

        with open(reg_path, "w", encoding="utf-8") as file:
            if remove:
                file.write(registry_remove_content)
            else:
                file.write(registry_add_content)

    def add_remove_registry_keys(self, app_id: str, registry_path: str, remove: bool = False) -> None:
        reg_command: str = f"regedit /S {registry_path}"

        full_command: list[str] = ["protontricks", "-c", reg_command, app_id]

        try:
            subprocess.run(full_command, check=True,
                           capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            if remove:
                raise Exception(f"Failed to remove keys: {e.stderr}")
            else:
                raise Exception(f"Failed to write on registry: {e.stderr}")

    def run_reshade_actions(self, reshade_prefix: str, game_executable: Path, app_id: str) -> None:
        self.move_reshade_files(reshade_prefix)
        self.create_reshade_apps(reshade_prefix, game_executable)
        self.create_remove_leshade_reg(ADD_REG_PATH)
        self.add_remove_registry_keys(app_id, ADD_REG_PATH)
