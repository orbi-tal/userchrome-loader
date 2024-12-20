from PyInstaller.utils.hooks import collect_all

# Add any packages that need special handling
datas, binaries, hiddenimports = collect_all('configparser')
