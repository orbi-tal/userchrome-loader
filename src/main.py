""" UserChrome Loader
Provides a User-Friendly way to load Userchrome Scripts for Zen Browser
"""

from pathlib import Path
import os
import sys
import configparser
import re
import subprocess
import platform
import shutil
from dataclasses import dataclass
from typing import TypeAlias, Final
from typing_extensions import TypeGuard
from collections.abc import Mapping

# Type aliases
ProfileDict: TypeAlias = dict[str, str | bool]
StrDict: TypeAlias = dict[str, str]
StrList: TypeAlias = list[str]
StrSet: TypeAlias = set[str]
Installation = tuple[str, str]

@dataclass
class FileOperationResult:
    success: bool
    message: str = ""
    data: str | None = None  # Add back the data field

@dataclass
class Main:
    """ Main Class for UC Loader"""
    MAX_FILE_SIZE: Final[int] = 10 * 1024 * 1024  # 10MB

    def __init__(self, installation_type: str | None = None) -> None:
        self.home_dir: str = str(Path.home())
        self.zen_dir: str = ""
        self.profiles_ini_path: str = ""
        self.imported_files: set[str] = set()
        self.installation_type: str | None = installation_type

    def is_valid_profile(self, profile: Mapping[str, str]) -> TypeGuard[ProfileDict]:
        """Type guard to validate profile structure"""
        required_keys = {'name', 'path', 'display_name', 'is_default'}
        return all(key in profile for key in required_keys)

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to remove problematic characters"""
        return "".join(c for c in filename if c.isalnum() or c in ".-_ ")

    def check_path_length(self, path: str) -> bool:
        """Check if path length is valid for the current platform"""
        if sys.platform == 'win32' and len(path) > 260:
            print(f"Warning: Path exceeds Windows maximum length: {path}")
            return False
        return True

    def check_file_permissions(self, path: str) -> bool:
        """Check if we have necessary permissions for the file/directory"""
        if os.path.exists(path):
            if not os.access(path, os.W_OK):
                print(f"Error: No write permission for {path}")
                return False
            if not os.access(path, os.R_OK):
                print(f"Error: No read permission for {path}")
                return False
        return True

    def select_installation(self) -> str:
        """Allow user to select between Flatpak and standard installation"""
        if self.installation_type:
            return self.installation_type

        if not sys.platform.startswith('linux'):
            return 'standard'

        flatpak_path = os.path.join(
            self.home_dir,
            '.var',
            'app',
            'io.github.zen_browser.zen',
            '.zen',
            'profiles.ini'
        )

        standard_path = os.path.join(
            self.home_dir,
            '.zen',
            'profiles.ini'
        )

        installations: list[Installation] = []
        if os.path.exists(flatpak_path):
            installations.append(('flatpak', flatpak_path))
        if os.path.exists(standard_path):
            installations.append(('standard', standard_path))

        if not installations:
            print("No Zen Browser installation found")
            return 'standard'

        if len(installations) == 1:
            print(f"Found {installations[0][0]} installation")
            return installations[0][0]

        print("\nMultiple Zen Browser installations found:")
        for i, (install_type, path) in enumerate(installations, 1):
            print(f"{i}. {install_type.capitalize()} Installation ({path})")

        while True:
            try:
                choice = input("\nSelect installation (enter number): ")
                index = int(choice) - 1
                if 0 <= index < len(installations):
                    return installations[index][0]
                print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a number.")

    def setup_paths(self):
        """Set up paths based on OS and installation type"""
        if os.name == 'nt':  # Windows
            self.profiles_ini_path = os.path.join(
                self.home_dir,
                'AppData',
                'Roaming',
                'Zen',
                'profiles.ini'
            )

        elif sys.platform == 'darwin':  # macOS
            # Try modern macOS path first
            modern_path = os.path.join(
                self.home_dir,
                'Library',
                'Application Support',
                'Zen',
                'profiles.ini'
            )
            # Fallback to older macOS path
            legacy_path = os.path.join(
                self.home_dir,
                'Library',
                'Zen',
                'profiles.ini'
            )

            if os.path.exists(modern_path):
                self.profiles_ini_path = modern_path
            else:
                self.profiles_ini_path = legacy_path

        elif sys.platform.startswith('linux'):  # Linux
            installation = self.select_installation()

            if installation == 'flatpak':
                self.profiles_ini_path = os.path.join(
                    self.home_dir,
                    '.var',
                    'app',
                    'io.github.zen_browser.zen',
                    '.zen',
                    'profiles.ini'
                )
            else:  # standard
                self.profiles_ini_path = os.path.join(
                    self.home_dir,
                    '.zen',
                    'profiles.ini'
                )

        else:
            raise NotImplementedError(f"Operating system {sys.platform} is not supported")

        # Set zen_dir based on profiles.ini location
        self.zen_dir = os.path.dirname(self.profiles_ini_path)

        # Verify the profiles.ini exists
        if not os.path.exists(self.profiles_ini_path):
            print(f"Warning: profiles.ini not found at {self.profiles_ini_path}")

    def select_profile(self, profiles: list[dict[str, str | bool]]) -> dict[str, str | bool] | None:
        """Allow user to select a profile if multiple profiles exist"""
        if not profiles:
            return None

        if len(profiles) == 1:
            profile = profiles[0]
            print("\nSelected Profile Details:")
            print(f"Display Name: {profile['display_name']}")
            print(f"Path: {profile['path']}")
            print(f"Default Profile: {'Yes' if profile['is_default'] else 'No'}")
            return profile

        print("\nAvailable profiles:")
        # Find default profile
        default_profile = next((p for p in profiles if p['is_default']), None)

        for i, profile in enumerate(profiles, 1):
            default_marker = " (Default)" if profile['is_default'] else ""
            print(f"{i}. {profile['display_name']}{default_marker}")

        while True:
            try:
                choice = input("\nSelect profile (enter number or press Enter for default): ").strip()
                selected_profile = None

                if choice == "" and default_profile:
                    selected_profile = default_profile
                else:
                    index = int(choice) - 1
                    if 0 <= index < len(profiles):
                        selected_profile = profiles[index]

                if selected_profile:
                    print("\nSelected Profile:")
                    print(f"Display Name: {selected_profile['display_name']}")
                    print(f"Path: {selected_profile['path']}")
                    print(f"Default Profile: {selected_profile['is_default']}")
                    return selected_profile

                print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a number or press Enter for default profile.")

    def get_profile_info(self) -> list[dict[str,str | bool]]:
        """Get Zen Browser profile information from profiles.ini"""
        if not os.path.exists(self.profiles_ini_path):
            print("profiles.ini not found")
            return []

        config = configparser.ConfigParser()
        try:
            _ = config.read(self.profiles_ini_path)

            return [
                {
                    'name': os.path.basename(path),
                    'path': os.path.join(self.zen_dir, path) if is_relative else path,
                    'display_name': config.get(section, 'Name',
                        fallback=os.path.basename(path).split('.')[0]),
                    'is_default': config.get(section, 'Default', fallback=False)
                }
                for section in config.sections()
                if section.startswith('Profile')
                and (path := config.get(section, 'Path', fallback=None))
                and (is_relative := config.getboolean(section, 'IsRelative', fallback=True))
            ]

        except Exception as e:
            print(f"Error reading profiles.ini: {e}")
            return []

    def get_existing_files(self, source_folder: str, destination: str) -> list[str]:
        """Get list of files that already exist in destination"""
        existing_files: list[str] = []
        try:
            for root, _, files in os.walk(source_folder, followlinks=True):
                if os.path.islink(root):
                    print(f"Warning: Symlink detected at {root}")
                    continue

                for file in files:
                    if not file.endswith('.css'):
                        continue

                    rel_path = os.path.relpath(os.path.join(root, file), source_folder)
                    dest_file = os.path.join(destination, rel_path)

                    # Check for case-insensitive conflicts
                    dest_dir = os.path.dirname(dest_file)
                    if os.path.exists(dest_dir):
                        existing_names = [f.lower() for f in os.listdir(dest_dir)]
                        if os.path.basename(dest_file).lower() in existing_names:
                            existing_files.append(rel_path)

        except Exception as e:
            print(f"Error checking existing files: {e}")
            return []

        return existing_files

    def check_circular_imports(self, css_path: str, visited: set[str] | None = None) -> bool:
        """Check for circular imports in CSS files"""
        if visited is None:
            visited = set()

        if not os.path.exists(css_path):
            return False

        if css_path in visited:
            print(f"Warning: Circular import detected in {css_path}")
            return True

        visited.add(css_path)
        # Rest of method remains the same

        try:
            with open(css_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(css_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            except Exception:
                return False

        # Find all @import statements
        import_lines = [line.strip() for line in content.splitlines()
                       if line.strip().startswith('@import')]

        for line in import_lines:
            # Extract the imported file path
            match = re.search(r"url\(['\"](.+?)['\"]", line)
            if match:
                imported_path = match.group(1)
                full_path = os.path.join(os.path.dirname(css_path), imported_path)

                if self.check_circular_imports(full_path, visited):
                    return True

        return False

    def generate_import_path(self, data: str | None, organization: str, folder_name: str) -> str | None:
        """Generate import path based on organization type"""
        if not data:
            return None

        if organization == "2":
            return f"@import url('{folder_name}/{data}');\n"
        return f"@import url('{data}');\n"

    def read_userchrome(self, userchrome_path: str) -> tuple[str, bool]:
        """Read userChrome.css and check if it only contains imports"""
        content = ""
        try:
            with open(userchrome_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(userchrome_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                print("Warning: File not UTF-8 encoded, used latin-1 encoding")
            except Exception as e:
                print(f"Error reading file: {e}")
                return "", True

        lines = [line.strip() for line in content.splitlines() if line.strip()]
        only_imports = all(line.startswith('@import') for line in lines)

        # Check for circular imports
        imports = [line for line in lines if line.startswith('@import')]
        for imp in imports:
            if imp in self.imported_files:
                print(f"Warning: Potential circular import detected: {imp}")
            self.imported_files.add(imp)

        return content, only_imports

    def handle_backup(self, chrome_dir: str, userchrome_path: str) -> str:
        """Handle backing up existing userChrome.css"""
        backup_path = os.path.join(chrome_dir, 'userChrome_backup.css')

        if not self.check_file_permissions(chrome_dir):
            return ""

        try:
            # Check if backup already exists
            backup_counter = 1
            while os.path.exists(backup_path):
                backup_path = os.path.join(chrome_dir, f'userChrome_backup_{backup_counter}.css')
                backup_counter += 1

            shutil.copy2(userchrome_path, backup_path)
            print(f"Backup created at: {os.path.basename(backup_path)}")

            while True:
                response = input("Would you like to import the backup CSS? (y/n): ").lower()
                if response == 'y':
                    return f"@import url('{os.path.basename(backup_path)}');\n"
                elif response == 'n':
                    return ""
                print("Please enter 'y' for yes or 'n' for no")

        except Exception as e:
            print(f"Error creating backup: {e}")
            return ""

    def get_import_type(self) -> str:
        """Get user's choice for import type"""
        prompt = (
                "\nWhat would you like to import?\n"
                "1. Single CSS file\n"
                "2. Folder of CSS files\n"
                "Choose (1-2): "
            )
        while True:
                import_type = input(prompt).strip()
                return import_type

    def get_file_path(self) -> str | None:
        """Get file path using native OS file dialog"""
        system = platform.system()

        try:
            if system == 'Windows':
                # PowerShell command for Windows file picker
                cmd = '''powershell -command "& {
                    Add-Type -AssemblyName System.Windows.Forms
                    $f = New-Object System.Windows.Forms.OpenFileDialog
                    $f.Filter = 'CSS files (*.css)|*.css|All files (*.*)|*.*'
                    $f.ShowDialog()
                    $f.FileName
                }"'''
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                return result.stdout.strip()

            elif system == 'Darwin':  # macOS
                cmd = ['osascript', '-e',
                      'POSIX path of (choose file with prompt "Select CSS file" of type {"css", "public.plain-text"})']
                result = subprocess.run(cmd, capture_output=True, text=True)
                return result.stdout.strip()

            else:  # Linux
                try:
                    import gi
                    gi.require_version('Gtk', '3.0')
                    from gi.repository import Gtk

                    dialog = Gtk.FileChooserDialog(
                        title="Select CSS file to import",
                        action=Gtk.FileChooserAction.OPEN
                    )

                    # Add buttons using the recommended method
                    dialog.add_buttons(
                        "Cancel", Gtk.ResponseType.CANCEL,
                        "Open", Gtk.ResponseType.OK
                    )

                    filter_css = Gtk.FileFilter()
                    filter_css.set_name("CSS files")
                    filter_css.add_pattern("*.css")
                    dialog.add_filter(filter_css)

                    filter_all = Gtk.FileFilter()
                    filter_all.set_name("All files")
                    filter_all.add_pattern("*")
                    dialog.add_filter(filter_all)

                    response = dialog.run()
                    file_path = None

                    if response == Gtk.ResponseType.OK:
                        file_path = dialog.get_filename()

                    dialog.destroy()
                    while Gtk.events_pending():
                        Gtk.main_iteration()

                    return file_path

                except Exception as e:
                    print(f"Error with Linux file dialog: {e}")
                    return None

        except subprocess.SubprocessError as e:
            print(f"Error opening file dialog: {e}")
            return None

    def get_folder_path(self) -> str | None:
        """Get folder path using native file dialog for each OS"""
        if sys.platform == 'win32':  # Windows
            try:
                import ctypes
                from ctypes.wintypes import BROWSEINFO, LPARAM, LPCSTR, LPCWSTR, HWND

                BIF_RETURNONLYFSDIRS = 0x00000001
                BIF_USENEWUI = 0x00000050

                BFFM_INITIALIZED = 1
                MAX_PATH = 260

                shell32 = ctypes.windll.shell32
                ole32 = ctypes.windll.ole32

                ole32.CoInitialize(None)

                bi = BROWSEINFO()
                bi.lpszTitle = "Select folder containing CSS files"
                bi.ulFlags = BIF_RETURNONLYFSDIRS | BIF_USENEWUI

                pidl = shell32.SHBrowseForFolderW(ctypes.byref(bi))
                if pidl:
                    path = ctypes.create_unicode_buffer(MAX_PATH)
                    shell32.SHGetPathFromIDListW(pidl, path)
                    shell32.CoTaskMemFree(pidl)
                    return path.value
                return None

            except ImportError:
                print("Could not load Windows API")
                # Fallback to command line
                return input("Please enter folder path: ")

        elif sys.platform == 'darwin':  # macOS
            try:
                from AppKit import NSOpenPanel, NSApp

                panel = NSOpenPanel.alloc().init()
                panel.setCanChooseDirectories_(True)
                panel.setCanChooseFiles_(False)
                panel.setAllowsMultipleSelection_(False)
                panel.setTitle_("Select folder containing CSS files")

                if panel.runModal() == 1:
                    return str(panel.URLs()[0].path())
                return None

            except ImportError:
                print("AppKit not available")
                # Fallback to command line
                return input("Please enter folder path: ")

        else:  # Linux
            try:
                import gi
                gi.require_version('Gtk', '3.0')
                from gi.repository import Gtk
                dialog = Gtk.FileChooserDialog(
                    title="Select folder containing CSS files",
                    action=Gtk.FileChooserAction.SELECT_FOLDER
                )

                # Add buttons using the recommended method
                dialog.add_buttons(
                    "Cancel", Gtk.ResponseType.CANCEL,
                    "Select", Gtk.ResponseType.OK
                )

                response = dialog.run()
                folder_path = None

                if response == Gtk.ResponseType.OK:
                    folder_path = dialog.get_filename()

                dialog.destroy()
                while Gtk.events_pending():
                    Gtk.main_iteration()

                return folder_path

            except (ImportError, ValueError):
                print("GTK not available. Please install python3-gi package")
                # Fallback to command line
                return input("Please enter folder path: ")

        return None

    def handle_single_file_import(self, chrome_dir: str) -> str | None:
        """Handle importing a single CSS file"""
        css_file = self.get_file_path()

        if not css_file:
            print("Operation cancelled: No file was selected")
            return None

        filename = os.path.basename(css_file)
        target_filename = filename

        # Handle special cases for userChrome.css and mod.css
        if filename in ['userChrome.css', 'mod.css']:
            target_filename = 'mod.css'

        destination = os.path.join(chrome_dir, target_filename)

        # Check for filename conflicts
        if os.path.exists(destination):
            if not self.confirm_replace(target_filename):
                # If user doesn't want to replace, create a new filename
                base, ext = os.path.splitext(target_filename)
                counter = 1
                while os.path.exists(destination):
                    target_filename = f"{base}_{counter}{ext}"
                    destination = os.path.join(chrome_dir, target_filename)
                    counter += 1

        try:
            shutil.copy2(css_file, destination)
            return f"@import url('{target_filename}');\n"
        except Exception as e:
            print(f"Error copying file: {e}")
            return None

    def get_subfolder_preference(self) -> str:
        while True:
            subfolder = input(
                """How should the files be imported?\n
                (1) Copy directly to chrome folder\n
                (2) Create subfolder\n
                (3) Keep folder structure\n
                Choose (1-3):"""
            ).strip()
            if subfolder in ["1", "2", "3"]:
                return subfolder

    def handle_folder_import(self, chrome_dir: str) -> str | None:
        """Handle importing a folder of CSS files"""
        folder = self.get_folder_path()

        if not folder:
            print("Operation cancelled: No folder was selected")
            return None

        organization = self.get_subfolder_preference()
        folder_name = os.path.basename(folder)

        # Set up destination based on organization choice
        if organization == "2":  # Create subfolder
            destination = os.path.join(chrome_dir, folder_name)
        else:  # Direct to chrome folder
            destination = chrome_dir

        # Check for userChrome.css in the source folder
        source_userchrome = os.path.join(folder, 'userChrome.css')
        if os.path.exists(source_userchrome):
            # Always rename userChrome.css to mod.css in folder imports
            target_mod_css = os.path.join(destination, 'mod.css')
            try:
                os.makedirs(destination, exist_ok=True)
                shutil.copy2(source_userchrome, target_mod_css)
                if organization == "2":
                    return f"@import url('{folder_name}/mod.css');\n"
                else:
                    return "@import url('mod.css');\n"
            except Exception as e:
                print(f"Error copying userChrome.css: {e}")
                return None

        # If no userChrome.css, look for mod.css
        source_mod = os.path.join(folder, 'mod.css')
        if os.path.exists(source_mod):
            target_mod_css = os.path.join(destination, 'mod.css')
            try:
                os.makedirs(destination, exist_ok=True)
                shutil.copy2(source_mod, target_mod_css)
                if organization == "2":
                    return f"@import url('{folder_name}/mod.css');\n"
                else:
                    return "@import url('mod.css');\n"
            except Exception as e:
                print(f"Error copying mod.css: {e}")
                return None

        print("No userChrome.css or mod.css found in selected folder")
        return None

    def process_files(self, source: str, dest: str, response: str) -> FileOperationResult:
        """Process CSS files during copy operation"""
        try:
            files_copied: list[str] = []
            for root, _, files in os.walk(source):
                for file in files:
                    if not file.endswith('.css'):
                        continue

                    src_file = os.path.join(root, file)
                    rel_path = os.path.relpath(src_file, source)
                    dest_file = os.path.join(dest, rel_path)

                    if self.process_css_file(src_file, dest_file, response):
                        files_copied.append(rel_path)

            if not files_copied:
                return FileOperationResult(success=False, message="No CSS files were copied")

            return FileOperationResult(
                success=True,
                message="Files copied successfully",
                data=files_copied[0]
            )

        except Exception as e:
            return FileOperationResult(success=False, message=f"Error processing files: {e}")

    def process_css_file(self, src_file: str, dest_file: str, response: str) -> bool:
        """Process a single CSS file during copy operation"""
        if os.path.getsize(src_file) > self.MAX_FILE_SIZE:
            print(f"Warning: Large file detected: {os.path.basename(src_file)}")
            return False

        if not self.check_path_length(dest_file):
            return False

        try:
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            if not os.path.exists(dest_file) or response == "1":
                shutil.copy2(src_file, dest_file)
                return True
        except Exception as exc:
            print(f"Error copying {src_file}: {exc}")
        return False

    def perform_copy(self, source_folder: str, destination: str,
                    response: str, organization: str, folder_name: str) -> str | None:
        """Copy files with improved organization and error handling"""
        if not self.validate_copy_prerequisites(destination):
            return None

        copied_files = self.copy_css_files(
            source_folder, destination, response
        )

        if not copied_files.success:
            return None

        return self.generate_import_path(
            copied_files.data, organization, folder_name
        )

    def validate_copy_prerequisites(self, destination: str) -> bool:
        """Validate prerequisites before copying files"""
        return (self.check_path_length(destination) and
                self.check_file_permissions(destination))

    def copy_css_files(self, source: str, dest: str, response: str) -> FileOperationResult:
        """Copy CSS files with proper organization"""
        css_files = [f for f in os.listdir(source) if f.endswith('.css')]
        if not css_files:
            return FileOperationResult(False, "No CSS files found")

        os.makedirs(dest, exist_ok=True)
        result = self.process_files(source, dest, response)
        return result

    def setup_chrome_dir(self, profile: ProfileDict) -> str | None:
        """Set up the chrome directory for the profile"""
        try:
            profile_path = str(profile['path'])  # Explicitly cast to str
            chrome_dir = os.path.join(profile_path, 'chrome')

            if not self.check_file_permissions(chrome_dir):
                return None

            os.makedirs(chrome_dir, exist_ok=True)
            return chrome_dir
        except Exception as e:
            print(f"Error setting up chrome directory: {e}")
            return None

    def write_userchrome_content(self, file_path: str, content: str, _mode: str = 'w') -> bool:
        """Write content to userChrome.css file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                _ = f.write(content)
            return True
        except UnicodeEncodeError:
            try:
                with open(file_path, 'w', encoding='latin-1') as f:
                    _ = f.write(content)
                return True
            except Exception as e:
                print(f"Error writing file: {e}")
                return False

    def create_backup(self, file_path: str) -> str | None:
        """Create a backup of the given file"""
        if not os.path.exists(file_path):
            return None
        backup_path = f"{file_path}.backup"
        try:
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            print(f"Error creating backup: {e}")
            return None

    def has_duplicate_import(self, content: str, import_line: str) -> bool:
        """Check if import already exists in content"""
        normalized_import = import_line.lower().replace(" ", "")
        normalized_content = content.lower().replace(" ", "")
        return normalized_import in normalized_content

    def prepare_content(self, existing_content: str, import_line: str, mode: str) -> str:
        """Prepare content for writing to file"""
        if mode == 'w':
            content = existing_content
            if content and not content.endswith('\n'):
                content += '\n'
            content += import_line
        else:
            content = import_line
        return content

    def restore_from_backup(self, original_path: str, backup_path: str | None) -> None:
        """Restore file from backup"""
        if backup_path and os.path.exists(backup_path):
            try:
                shutil.copy2(backup_path, original_path)
                print("Restored from backup after error")
            except Exception as e:
                print(f"Error restoring from backup: {e}")

    def cleanup_backup(self, backup_path: str | None) -> None:
        """Clean up backup file"""
        if backup_path and os.path.exists(backup_path):
            try:
                os.remove(backup_path)
            except Exception as e:
                print(f"Warning: Could not remove backup file: {e}")

    def has_import(self, content: str, import_line: str) -> bool:
        """Check if import already exists in content"""
        # Normalize both strings for comparison (remove comments, whitespace)
        def normalize_import(line: str) -> str:
            return line.replace('/*', '').replace('*/', '').strip()

        normalized_import = normalize_import(import_line)
        content_lines = content.splitlines()

        for line in content_lines:
            if line.strip().startswith('@import'):
                if normalize_import(line) == normalized_import:
                    return True
        return False

    def get_last_import_position(self, content: str) -> int:
        """Find position after the last import statement"""
        lines = content.splitlines()
        last_import_index = -1

        for i, line in enumerate(lines):
            if line.strip().startswith('@import'):
                last_import_index = i

        return last_import_index

    def update_userchrome(self, userchrome_path: str, import_line: str,
                         existing_content: str, _only_imports: bool) -> None:
        """Update the userChrome.css file with new import"""
        if not self.check_file_permissions(userchrome_path):
            return

        if self.has_import(existing_content, import_line):
            print("Notice: Import already exists in userChrome.css")
            return

        try:
            lines = existing_content.splitlines()
            last_import_pos = self.get_last_import_position(existing_content)

            if last_import_pos == -1:  # No existing imports
                lines.insert(0, import_line)
            else:
                lines.insert(last_import_pos + 1, import_line)

            if len(lines) > last_import_pos + 2:
                if lines[last_import_pos + 2].strip():
                    lines.insert(last_import_pos + 2, '')

            content = '\n'.join(lines)
            _ = self.write_userchrome_content(userchrome_path, content)

        except Exception as e:
            print(f"Error updating userChrome.css: {e}")

    def toggle_import(self, userchrome_path: str, index: int, enable: bool = True) -> None:
        """Enable or disable an import statement"""
        try:
            with open(userchrome_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.splitlines()
            import_lines = [i for i, line in enumerate(lines)
                           if line.strip().startswith('@import') or
                              (line.strip().startswith('/*') and '@import' in line)]

            if not 0 <= index < len(import_lines):
                print("Invalid import index")
                return

            line_num = import_lines[index]
            line = lines[line_num]

            if enable:
                # Remove comment markers if present
                if '/*' in line and '*/' in line:
                    line = line.replace('/*', '').replace('*/', '').strip()
            else:
                # Add comment markers if not present
                if not (line.strip().startswith('/*') and line.strip().endswith('*/')):
                    line = f"/* {line.strip()} */"

            lines[line_num] = line
            content = '\n'.join(lines)

            _ = self.write_userchrome_content(userchrome_path, content)
            print(f"Import {'enabled' if enable else 'disabled'} successfully")

        except Exception as e:
            print(f"Error toggling import: {e}")

    def handle_import(self, chrome_dir: str) -> None:
        """Handle the import process"""
        userchrome_path = os.path.join(chrome_dir, 'userChrome.css')
        existing_content, only_imports = self.handle_existing_userchrome(chrome_dir, userchrome_path)

        import_line = self.import_file_or_folder(chrome_dir)
        if not import_line:
            return

        self.update_userchrome(userchrome_path, import_line, existing_content, only_imports)

        print("\nCSS file successfully imported!")
        print("To apply the changes, please restart Zen Browser")

    def list_imports(self, userchrome_path: str) -> list[tuple[int, str, bool]]:
        """List all imports and their status"""
        imports: list[tuple[int, str, bool]] = []
        try:
            with open(userchrome_path, 'r', encoding='utf-8') as f:
                content = f.read()

            for i, line in enumerate(content.splitlines()):
                line = line.strip()
                if '@import' in line:
                    is_enabled = not (line.startswith('/*') and line.endswith('*/'))
                    imports.append((i, line, is_enabled))

        except Exception as e:
            print(f"Error listing imports: {e}")

        return imports

    def manage_imports(self, chrome_dir: str) -> None:
        """Manage import statements in userChrome.css"""
        userchrome_path = os.path.join(chrome_dir, 'userChrome.css')

        while True:
            imports = self.list_imports(userchrome_path)
            if not imports:
                print("No imports found in userChrome.css")
                return

            print("\nCurrent imports:")
            for i, (_, line, enabled) in enumerate(imports):
                status = "Enabled" if enabled else "Disabled"
                print(f"{i+1}. [{status}] {line}")

            choice = input("\nEnter number to toggle import (or 'q' to quit): ").lower()
            if choice == 'q':
                break

            try:
                index = int(choice) - 1
                if 0 <= index < len(imports):
                    self.toggle_import(userchrome_path, index, not imports[index][2])
                else:
                    print("Invalid selection")
            except ValueError:
                print("Please enter a number or 'q'")

    def confirm_replace(self, filename: str) -> bool:
        """Confirm if user wants to replace existing file"""
        while True:
            response = input(f"""\nWarning: '{filename}' already exists in chrome directory.\n
                Do you want to replace it? (y/n): """).lower()
            if response in ['y', 'n']:
                return response == 'y'
            print("Please enter 'y' for yes or 'n' for no")

    def handle_existing_files(self, existing_files: list[str]) -> str | None:
        """Handle existing files and get user response"""
        print("\nThe following files already exist:")
        for file in existing_files:
            print(f"- {file}")

        while True:
            response = input(
                """\nHow would you like to handle existing files?\n
                1. Replace all\n
                2. Skip existing (keep old files)\n
                3. Cancel operation\n
                Choose (1-3): """
            ).strip()

            if response in ["1", "2", "3"]:
                return response if response != "3" else None
            print("Please enter 1, 2, or 3")

    def copy_folder(self, source_folder: str, chrome_dir: str, organization: str) -> str | None:
        """Copy a folder of CSS files and return the folder name for import"""
        folder_name = os.path.basename(source_folder)

        # Set up destination
        destination = os.path.join(chrome_dir, folder_name) if organization == "2" else chrome_dir

        try:
            # Check existing files
            existing_files = self.get_existing_files(source_folder, destination)

            if existing_files:
                response = self.handle_existing_files(existing_files)
                if not response:
                    return None
            else:
                response = "2" # Default to skip mode

            return self.perform_copy(source_folder, destination, response, organization, folder_name)

        except Exception as e:
            print(f"Error copying folder: {e}")
            return None

    def handle_existing_userchrome(self, chrome_dir: str, userchrome_path: str) -> tuple[str, bool]:
        """Handle existing userChrome.css file"""
        existing_content = ""
        only_imports = True

        if os.path.exists(userchrome_path):
            existing_content, only_imports = self.read_userchrome(userchrome_path)
            if not only_imports and existing_content.strip():
                existing_content = self.handle_backup(chrome_dir, userchrome_path)

        return existing_content, only_imports

    def import_file_or_folder(self, chrome_dir: str) -> str | None:
        """Handle file/folder import selection and processing"""
        import_type = self.get_import_type()
        if import_type == "1":
            return self.handle_single_file_import(chrome_dir)
        else:
            return self.handle_folder_import(chrome_dir)

    def cleanup_temporary_files(self, chrome_dir: str) -> None:
        """Clean up any temporary files created during import process"""
        try:
            backup_files = [f for f in os.listdir(chrome_dir)
                           if f.endswith('.backup') or f.endswith('.tmp')]
            for file in backup_files:
                file_path = os.path.join(chrome_dir, file)
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Warning: Could not remove temporary file {file}: {e}")
        except Exception as e:
            print(f"Warning: Error during cleanup: {e}")

    def check_profile_lock(self, profile: ProfileDict) -> bool:
        """Check if profile is locked"""
        try:
            profile_path = str(profile['path'])  # Explicitly cast to str
            lock_file = os.path.join(profile_path, 'lock')
            return os.path.exists(lock_file)
        except (KeyError, TypeError) as e:
            print(f"Error checking profile lock: {e}")
            return False

    def chrome_loader(self) -> None:
        """Load UserChrome configurations for each profile"""
        chrome_dir = None
        try:
            self.setup_paths()
            profiles = self.get_profile_info()

            if not profiles:
                print("No Zen Browser profiles found")
                return

            selected_profile = self.select_profile(profiles)
            if not selected_profile:
                print("No profile selected")
                return

            if self.check_profile_lock(selected_profile):
                print("Warning: Profile appears to be in use. Please close Zen Browser first.")
                return

            chrome_dir = self.setup_chrome_dir(selected_profile)
            if not chrome_dir:
                return

            while True:
                print("\nUserChrome Loader Menu:")
                print("1. Import CSS")
                print("2. Manage Imports")

                choice = input("Choose an option (1-2): ").strip()

                if choice == "1":
                    self.handle_import(chrome_dir)
                elif choice == "2":
                    self.manage_imports(chrome_dir)
                else:
                    print("Invalid choice")

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            if chrome_dir:
                self.cleanup_temporary_files(chrome_dir)

def main() -> None:
    try:
        loader = Main()
        loader.chrome_loader()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
