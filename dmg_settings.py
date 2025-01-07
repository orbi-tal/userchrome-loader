from os.path import exists, expanduser

application = defines.get('app', 'dist/UserChromeLoader.app')
appname = os.path.basename(application)

format = defines.get('format', 'UDBZ')
size = defines.get('size', '100M')

files = [application]

symlinks = {'Applications': '/Applications'}

badge_icon = None
icon_locations = {
    appname:        (140, 120),
    'Applications': (500, 120)
}

background = 'buildsupport/dmg-background.png'
icon_size = 80
text_size = 12
window_rect = ((100, 100), (640, 280))
default_view = 'icon-view'
