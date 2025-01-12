# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_all

# Include all required modules
hiddenimports = [
    'PyQt6.QtWidgets',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'pycurl',
    'libarchive',
    'libarchive.public',
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
    hiddenimports.extend(hidden)

# Exclude unnecessary modules
excludes = [
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

a = Analysis(
    ['src/gui.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove unnecessary files
def remove_from_list(source, patterns):
    for file in list(source):
        for pattern in patterns:
            if pattern in str(file):
                source.remove(file)
                break

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

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None,
    level=9
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
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=False,
    icon=None,
    compress=True,
    optimize=2,
)

if sys.platform == 'darwin':
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
