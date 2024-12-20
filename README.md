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

# UserChrome Loader for Zen Browser

A user-friendly tool to manage UserChrome CSS files for Zen Browser.

## Features

- Import single CSS files or entire folders
- Manage existing imports (enable/disable)
- Support for multiple profiles
- Automatic backup creation
- Cross-platform support (Windows, macOS, Linux)
- Support for both standard and Flatpak installations on Linux

## Installation

### From Source
```bash
pip install .
```

### From Releases
Download the appropriate binary for your platform from the Releases page.

## Usage

Simply run:
```bash
userchrome-loader
```

The tool will guide you through the process of:
1. Selecting your Zen Browser profile
2. Importing CSS files
3. Managing existing imports

## Development

Requirements:
- Python 3.10 or higher
- Dependencies listed in requirements.txt

To set up development environment:
```bash
pip install -r requirements.txt
```
