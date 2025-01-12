import os
import sys
import platform
from typing import cast

def get_meipass() -> str:
    """Get PyInstaller's _MEIPASS attribute safely"""
    if hasattr(sys, '_MEIPASS'):
        return cast(str, getattr(sys, '_MEIPASS'))
    return os.path.abspath(".")

def setup_qt_environment() -> None:
    """Setup Qt environment variables for frozen applications"""
    if not hasattr(sys, 'frozen'):
        return

    meipass = get_meipass()

    if platform.system().lower() == 'linux':
        # Set Qt plugin path
        qt_plugin_path = os.path.join(meipass, 'PyQt6', 'Qt6', 'plugins')
        if os.path.exists(qt_plugin_path):
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = qt_plugin_path

        # Set library path to find ICU and other libraries
        lib_path = os.path.join(meipass, 'PyQt6', 'Qt6', 'lib')
        if os.path.exists(lib_path):
            current_lib_path = os.environ.get('LD_LIBRARY_PATH', '')
            if current_lib_path:
                os.environ['LD_LIBRARY_PATH'] = f"{lib_path}:{current_lib_path}"
            else:
                os.environ['LD_LIBRARY_PATH'] = lib_path

if __name__ == '__main__':
    setup_qt_environment()
