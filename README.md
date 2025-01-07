# userChrome Loader
This is a template intended to make it easier for end-users to manually load and manage custom CSS.

## Setup Instructions

1. If you already have custom CSS in your **userChrome.css** file, back it up by copying the contents to a new CSS file indside the **chrome/** folder.

   - If you don't have any custom CSS in your userChrome.css file, skip this step.

2. Copy the **userChrome.css** file from this repo into your own userChrome.css file.

   - You can keep manual customizations in this file, however, uCL only uses it for import rules to call mods.

3. When you find a customization you want to add, copy the contents to a new folder inside **chrome/**.

   - Make sure the new folder and CSS file have unique names.

4. Add the **@import** rule to **userChrome.css** with the path to the new CSS file made in the last step.

*Examples:*

@import "chrome/example/example.css";

@import "chrome/example-2/example-mod2.css";

## Why Use uCL?

Orginizing custom CSS into their own files and folders will significantly aid users in customization and file management, as well as troubleshooting bugs by enabling easier isolation of custom CSS through @import rules.

This also allows Mod creaters to make their customizations more modular, allowing end users to pick and choose which features they want to add.

## Mod Creators / CSS Wizards:
Now when you upload some CSS with the intention of sharing, you can orginize your project folder structure by feauture with Modules. See [Natsumi Browser](https://github.com/greeeen-dev/natsumi-browser/tree/main) for the ideal project structure.

```
mod
|- mod.css
|- modules
   |- module1.css
   |- module2.css
userChrome.css
```

## Further Examples:

Here's what your **chrome** folder should look like, with some example mods already in place:

![image](https://github.com/user-attachments/assets/3306ce43-fafe-406c-9a7f-dba00bac2fe0)

And here's an example of **userChrome.css**

```
/* === Load custom files === */

@import "userchrome-loader/Cohesion/Cohesion.css";
@import "userchrome-loader/natsumi/config.css";
@import "userchrome-loader/natsumi/preload.css";
@import "userchrome-loader/natsumi/patches.css";
@import "userchrome-loader/natsumi/base-ui.css";
@import "userchrome-loader/natsumi/tab-groups.css";
@import "userchrome-loader/natsumi/horizontal-tabs.css";
@import "userchrome-loader/natsumi/natsumi-urlbar.css";
@import "userchrome-loader/natsumi/natsumi-loading.css";
@import "userchrome-loader/natsumi/ui-tweaks.css";

/* === Other custom CSS === */
. . .
```

# UserChrome Loader GUI

A user-friendly tool to manage UserChrome CSS files for Zen Browser.

## Features

- Import single CSS files or entire folders
- Manage existing imports (enable/disable/remove)
- Support for multiple profiles
- Automatic backup creation
- Cross-platform support (Windows, macOS, Linux)
- Support for both standard and Flatpak installations on Linux

## Quick Start (Python Scripts)

Requirements:
- Python 3.12 or higher

```bash
# Clone the repository
git clone https://github.com/orbi-tal/userchrome-loader.git
cd userchrome-loader

# Run the GUI directly
python src/gui.py

# Or run the CLI version
python src/main.py
```

## Building from Source

Requirements:
- Python 3.12 or higher
- pip (Python package installer)

```bash
# Clone the repository
git clone https://github.com/orbi-tal/userchrome-loader.git
cd userchrome-loader

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or activate.csh, or activate.fish for fish shell

# Install dependencies
pip install PyQt6 PyQt6-sip pyinstaller
pip install -r requirements.txt

# Run directly
python src/gui.py

# Or build executable
pyinstaller --clean main.spec

# Run the built executable
./dist/userchrome-loader
```

## Usage

1. **Profile Selection**
   - Select between standard or Flatpak installation (Linux only)
   - Choose which profile to modify

2. **Importing CSS**
   - Choose between importing a single CSS file or a mod folder
   - For single files:
     - Select your CSS file
     - The file will be copied to your chrome directory
   - For mod folders:
     - Select a folder containing CSS files
     - Choose organization method (direct copy or subfolder)

3. **Managing Imports**
   - View all current imports
   - Enable/disable specific imports
   - Remove imports and their associated files
   - Remove all imports at once

4. **Backup Features**
   - Automatic backup of existing userChrome.css
   - Option to import backup as a new CSS file

## Troubleshooting

1. **Application doesn't start**
   - Ensure Zen Browser is not running when modifying profiles
   - Check if you have the necessary permissions in your profile directory

2. **Changes not visible**
   - Restart Zen Browser to apply changes
   - Ensure the CSS file is properly imported in userChrome.css

3. **Linux-specific issues**
   - For Flatpak installations, ensure proper permissions for ~/.var/app/
   - For standard installations, check ~/.zen/ permissions
