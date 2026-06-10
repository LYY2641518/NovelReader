from pathlib import Path
import sys


def get_resource_dir():
    # frozen PyInstaller / Nuitka / 打包工具 會加的標記：
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)
        exe_dir = Path(sys.executable).parent
        resources_dir = exe_dir.parent / "Resources"
        if resources_dir.exists():
            return resources_dir
        return exe_dir
    return Path(__file__).resolve().parent.parent.parent


def get_data_dir():
    if getattr(sys, "frozen", False):
        # Store downloads outside the application bundle for writable access.
        return Path.home() / ".novel_crawler"
    return Path(__file__).resolve().parent.parent.parent

RESOURCE_DIR = get_resource_dir()
DATA_DIR = get_data_dir()

FONT_TW_SERIF = str(RESOURCE_DIR / "font" / "SourceHanSerifTW-Light.ttf")