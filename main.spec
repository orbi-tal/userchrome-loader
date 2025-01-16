import os
import platform
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

def get_platform():
    return platform.system().lower()

def get_python_dll():
    """Get the Python DLL path for Windows"""
    if get_platform() != 'windows':
        return []

    # Get Python DLL name
    python_dll = f'python{sys.version_info.major}{sys.version_info.minor}.dll'

    # Search paths for the DLL
    search_paths = [
        sys.base_prefix,
        os.path.join(sys.base_prefix, 'DLLs'),
        os.path.join(sys.base_prefix, 'Library', 'bin'),
        os.path.dirname(sys.executable),
    ]

    # Find the DLL
    for path in search_paths:
        dll_path = Path(path) / python_dll
        if dll_path.exists():
            return [(str(dll_path), '.')]

    return []

# Platform specific configurations
PLATFORM_CONFIG = {
    'linux': {
        'upx': True,
        'upx_args': ['--best', '--lzma'],
        'console': False,
        'disable_windowed_traceback': False,
    },
    'windows': {
        'upx': True,
        'upx_args': ['--best', '--lzma'],
        'console': False,
        'disable_windowed_traceback': False,
    },
    'darwin': {
        'upx': True,
        'upx_args': ['--best', '--lzma'],
        'console': False,
        'disable_windowed_traceback': False,
    }
}

# Required modules for all platforms
HIDDEN_IMPORTS = [
    'PyQt6.QtWidgets',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'pycurl',
    'libarchive',
    'json',
    'configparser',
    'platform',
    'shutil',
    'tempfile',
    'datetime',
    'urllib.parse'
]

# Collect dependencies
datas = []
binaries = []

# Add Python DLL for Windows
binaries.extend(get_python_dll())

# Collect package dependencies
for pkg in ['PyQt6', 'libarchive']:
    data, bin, hidden = collect_all(pkg)
    datas.extend(data)
    binaries.extend(bin)
    HIDDEN_IMPORTS.extend(hidden)

# Modules to exclude
EXCLUDES = [
    'tkinter',
    'unittest',
    'email',
    'html',
    'http',
    'xml',
    'pydoc',
    'doctest',
    '_testcapi',
    'distutils',
    'pkg_resources',
    'PIL',
]

a = Analysis(
    ['src/gui.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='userchrome-loader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    **PLATFORM_CONFIG[get_platform()]
)

if get_platform() == 'darwin':
    app = BUNDLE(
        exe,
        name='userchrome-loader.app',
        icon=None,
        bundle_identifier='com.orbital.userchrome-loader',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSHighResolutionCapable': 'True',
            'LSMinimumSystemVersion': '10.13.0',
            'PythonPath': '@executable_path/../Resources/lib/python3.12'
        },
    )
