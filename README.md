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

# userChrome Loader GUI

A user-friendly tool to manage custom CSS files for Zen Browser.

## Features

- Import CSS files in multiple ways:
  - Single CSS files
  - Entire mod folders
  - Directly from GitHub repositories
  - From direct URL links
- Comprehensive import management:
  - Enable/disable specific imports
  - Remove individual imports or all at once
  - Organize imports in subfolders
- Automatic update checking:
  - Check for updates on GitHub-hosted mods
  - Easy one-click updates
  - Update notifications
- Profile management:
  - Support for multiple profiles
  - Automatic profile detection
- Cross-platform support:
  - Windows, macOS, Linux
  - Standard and Flatpak installations on Linux

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
   - Application checks if profile is in use

2. **Importing CSS**
   - Multiple import methods available:
     - Single CSS file import
     - Mod folder import
     - Direct URL import
     - GitHub repository import

   - For single files:
     - Select local CSS file or paste URL
     - File is validated and copied to chrome directory

   - For mod folders:
     - Select local folder or GitHub repository URL
     - Choose organization method:
       - Direct copy to chrome directory
       - Create subfolder for organization
     - Supports modular structures with multiple CSS files

   - For GitHub imports:
     - Paste repository URL
     - Automatically detects main CSS file
     - Downloads and organizes additional resources
     - Tracks version for updates

3. **Managing Imports**
   - View all current imports with status
   - Enable/disable specific imports
   - Remove individual imports and associated files
   - Check for updates on URL-based imports
   - Batch update available mods
   - Remove all imports with cleanup

4. **Update Management**
   - Check for updates on imported mods
   - View available updates with changelogs
   - Select which mods to update
   - Automatic backup before updating
   - Version tracking for each mod

## Troubleshooting

1. **Application doesn't start**
   - Ensure Zen Browser is not running when modifying profiles
   - Check if you have necessary permissions in your profile directory
   - For URL imports, check internet connectivity

2. **Changes not visible**
   - Restart Zen Browser to apply changes
   - Ensure the CSS file is properly imported in userChrome.css
   - Check if the import is enabled in the manage imports section

3. **URL Import Issues**
   - Verify the URL is accessible
   - For GitHub repositories, ensure they're public
   - Check if the repository contains valid CSS files

4. **Update Check Problems**
   - Ensure internet connectivity
   - Verify the original import source is still available
   - Check if you have write permissions for updates

5. **Linux-specific issues**
   - For Flatpak installations, ensure proper permissions for ~/.var/app/
   - For standard installations, check ~/.zen/ permissions
   - SELinux or AppArmor might need configuration
