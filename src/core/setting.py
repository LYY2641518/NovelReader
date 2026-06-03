from pathlib import Path
import sys

def get_base_dir():
    #frozen PyInstaller / Nuitka / 打包工具 會加的標記：
    if getattr(sys, "frozen", False):
        # PyInstaller / mobile frozen app
        return Path(sys.executable).parent
    else:
        return Path(__file__).resolve().parent.parent.parent

BASE_DIR = get_base_dir()

FONT_TW_SERIF = str(BASE_DIR / "font" / "SourceHanSerifTW-Light.ttf")

print(type(FONT_TW_SERIF))
print(FONT_TW_SERIF)