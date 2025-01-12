import os
import sys
import platform
from typing import cast

def get_meipass() -> str:
    """Get PyInstaller's _MEIPASS attribute safely"""
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    if hasattr(sys, '_MEIPASS'):
        return cast(str, getattr(sys, '_MEIPASS'))
    return os.path.abspath(".")

def setup_qt_environment() -> None:
    """Setup Qt environment variables for frozen applications"""
    if not hasattr(sys, 'frozen'):
        return

    if platform.system().lower() == 'linux':
        meipass = get_meipass()
        qt_plugin_path = os.path.join(meipass, 'PyQt6', 'Qt6', 'plugins')
        qt_font_path = os.path.join(meipass, 'PyQt6', 'Qt6', 'lib', 'fonts')

        if os.path.exists(qt_plugin_path):
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = qt_plugin_path

        if os.path.exists(qt_font_path):
            os.environ['QT_QPA_FONTDIR'] = qt_font_path

if __name__ == '__main__':
    setup_qt_environment()
