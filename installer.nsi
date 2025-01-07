!define PRODUCT_NAME "UserChrome Loader"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "orbi-tal"
!define PRODUCT_WEB_SITE "https://github.com/orbi-tal/userchrome-loader"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\userchrome-loader.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"

SetCompressor lzma
Name "${PRODUCT_NAME}"
OutFile "UserChromeLoader-Setup.exe"
InstallDir "$PROGRAMFILES64\UserChrome Loader"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    SetOverwrite ifnewer
    File "dist\userchrome-loader.exe"
    CreateDirectory "$SMPROGRAMS\UserChrome Loader"
    CreateShortCut "$SMPROGRAMS\UserChrome Loader\UserChrome Loader.lnk" "$INSTDIR\userchrome-loader.exe"
    CreateShortCut "$DESKTOP\UserChrome Loader.lnk" "$INSTDIR\userchrome-loader.exe"
SectionEnd
