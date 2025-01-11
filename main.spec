# main.spec
# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_all

# Only include essential PyQt6 modules
hiddenimports = [
    'PyQt6.QtWidgets',
    'PyQt6.QtCore',
    'PyQt6.QtGui'
]

# Collect minimal PyQt6 dependencies
datas = []
binaries = []
for pkg in ['PyQt6']:
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
    'PIL'
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

# Remove unnecessary files from the bundle
def remove_from_list(source, patterns):
    for file in list(source):
        for pattern in patterns:
            if pattern in str(file):
                source.remove(file)
                break

# Files to exclude from the bundle
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

# Enable maximum compression
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None,
    level=9  # Maximum compression level
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
    strip=True,  # Strip symbols
    upx=True,    # Enable UPX compression
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=False,
    icon=None,
    # Additional options for size optimization
    compress=True,
    optimize=2,  # Python optimization level
)

if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='UserChromeLoader.app',
        icon=None,
        bundle_identifier='com.orbital.userchrome-loader',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSHighResolutionCapable': 'True',
            'LSMinimumSystemVersion': '10.13.0',
            # Add PythonPath to improve startup time
            'PythonPath': '@executable_path/../Resources/lib/python3.12'
        },
    )
