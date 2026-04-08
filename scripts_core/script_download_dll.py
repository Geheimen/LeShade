from utils.utils import download

URL_COMPILER = "https://github.com/Ishidawg/reshade-installer-linux/raw/main/d3dcompiler_dll"
URL_D3D8TO9 = "https://github.com/crosire/d3d8to9/releases/download/v1.13.0/d3d8.dll"


def download_d3d8to9(game_path: str) -> None:
    download(url=URL_D3D8TO9, game_path=game_path, file_name="d3d8.dll")


def download_hlsl_compiler(game_path: str, game_arch: str) -> bool | None:
    return download(url=URL_COMPILER, game_path=game_path,
                    game_arch=game_arch, file_name="d3dcompiler_47.dll")
