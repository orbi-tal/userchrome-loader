# -*- mode: python ; coding: utf-8 -*-
import platform
from PyInstaller.utils.hooks import collect_all

def get_platform():
    return platform.system().lower()

# Platform specific configurations
PLATFORM_CONFIG = {
    'linux': {
        'strip': True,
        'upx': True,
        'upx_exclude': ['libQt6Core.so.6'],
        'console': False,
        'disable_windowed_traceback': True,
        'argv_emulation': False,
    },
    'windows': {
        'strip': True,
        'upx': True,
        'console': False,
        'disable_windowed_traceback': True,
        'argv_emulation': False,
    },
    'darwin': {
        'strip': True,
        'upx': True,
        'console': False,
        'disable_windowed_traceback': True,
        'argv_emulation': True,
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
for pkg in ['PyQt6', 'libarchive']:
    data, bin, hidden = collect_all(pkg)
    datas.extend(data)
    binaries.extend(bin)
    HIDDEN_IMPORTS.extend(hidden)

# Modules to exclude
EXCLUDES = [
    # Basic Python modules
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
    # Unused Qt modules
    'PyQt6.QtBluetooth',
    'PyQt6.QtDBus',
    'PyQt6.QtDesigner',
    'PyQt6.QtHelp',
    'PyQt6.QtMultimedia',
    'PyQt6.QtMultimediaWidgets',
    'PyQt6.QtNetwork',
    'PyQt6.QtNfc',
    'PyQt6.QtOpenGL',
    'PyQt6.QtOpenGLWidgets',
    'PyQt6.QtPdf',
    'PyQt6.QtPdfWidgets',
    'PyQt6.QtPositioning',
    'PyQt6.QtPrintSupport',
    'PyQt6.QtQml',
    'PyQt6.QtQuick',
    'PyQt6.QtQuick3D',
    'PyQt6.QtQuickWidgets',
    'PyQt6.QtRemoteObjects',
    'PyQt6.QtSensors',
    'PyQt6.QtSerialPort',
    'PyQt6.QtSpatialAudio',
    'PyQt6.QtSql',
    'PyQt6.QtSvg',
    'PyQt6.QtSvgWidgets',
    'PyQt6.QtTest',
    'PyQt6.QtTextToSpeech',
    'PyQt6.QtWebChannel',
    'PyQt6.QtWebSockets',
    'PyQt6.QtXml'
]

def remove_from_list(source, patterns):
    """Remove unnecessary files based on patterns"""
    to_remove = []
    for name, path, typ in source:
        if any(pattern in str(name) for pattern in patterns):
            to_remove.append((name, path, typ))

    for item in to_remove:
        source.remove(item)

def remove_linux_libraries(binaries):
    """Remove unnecessary Linux-specific libraries"""
    if get_platform() != 'linux':
        return binaries

    exclude_patterns = [
        'libicu',
        'libmysqlclient',
        'libodbc',
        'libpq',
        'libldap',
        'libsasl2',
        'libgnutls',
        'libhogweed',
        'libtasn1',
        'libp11-kit',
        'libnettle',
        'libxml2',
        'libxcb-glx'
    ]

    # Keep the third element (type) in the tuple
    return [(name, path, typ) for name, path, typ in binaries
            if not any(pattern in name for pattern in exclude_patterns)]

# Create Analysis object
a = Analysis(
    ['src/gui.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime-hook.py'],
    excludes=EXCLUDES,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove unnecessary Qt components
exclude_patterns = [
    'QtNetwork',
    'QtQml',
    'QtQuick',
    'QtSql',
    'QtTest',
    'QtDBus',
    'Qt6Pdf',
    'QtSvg',
    'QtPrintSupport'
]

remove_from_list(a.binaries, exclude_patterns)
remove_from_list(a.datas, exclude_patterns)

# Platform-specific optimizations
current_platform = get_platform()
if current_platform == 'linux':
    a.binaries = remove_linux_libraries(a.binaries)

# Create PYZ archive
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None,
    level=9  # Maximum compression
)

# Create executable with platform-specific options
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
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    compress=True,
    optimize=2,
    **PLATFORM_CONFIG[current_platform]
)

# Create macOS bundle if on Darwin
if current_platform == 'darwin':
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
