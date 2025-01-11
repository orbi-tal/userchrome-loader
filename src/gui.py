import os
import configparser
import sys
import shutil
import re
from typing import cast
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QPushButton, QLabel, QComboBox,
                            QFileDialog, QMessageBox, QStackedWidget, QDialog,
                            QRadioButton, QCheckBox, QListWidget)
from PyQt6.QtCore import Qt
from main import Main as ChromeLoader

class WelcomeDialog(QMainWindow):  # Changed from QDialog to QMainWindow
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to UserChrome Loader")
        self.setup_ui()

    def setup_ui(self):
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Welcome header
        welcome_label = QLabel("Welcome to UserChrome Loader!")
        welcome_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(welcome_label)

        # Description
        description = QLabel(
            "UserChrome Loader helps you customize Zen Browser's appearance "
            "by managing CSS modifications.\n\n"
            "With this tool, you can:"
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        # Features list
        features = [
            "• Import single CSS files or mod folders",
            "• Manage multiple CSS customizations",
            "• Enable/disable modifications without removing them",
            "• Easily remove unwanted customizations"
        ]
        features_label = QLabel("\n".join(features))
        layout.addWidget(features_label)

        # Usage Instructions
        usage_label = QLabel("\nHow to Use:")
        usage_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(usage_label)

        instructions = [
            "1. Close Zen Browser before making any changes",
            "2. Select your browser profile",
            "3. Import CSS:",
            "   • For single files: Choose 'Import CSS' → 'Single CSS File'",
            "   • For mod folders: Choose 'Import CSS' → 'Mod Folder'",
            "4. Manage your imports:",
            "   • Enable/disable specific modifications",
            "   • Remove unwanted customizations",
            "5. Restart Zen Browser to see your changes"
        ]
        instructions_label = QLabel("\n".join(instructions))
        instructions_label.setWordWrap(True)
        layout.addWidget(instructions_label)

        # Tips Section
        tips_label = QLabel("\nTips:")
        tips_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(tips_label)

        tips = [
            "• Keep backups of your original CSS files",
            "• Test one modification at a time",
            "• Use the 'Manage Imports' feature to troubleshoot issues",
            "• Remember to restart the browser after each change"
        ]
        tips_label = QLabel("\n".join(tips))
        tips_label.setWordWrap(True)
        layout.addWidget(tips_label)

        # Important note
        note_label = QLabel(
            "\nImportant Note: Please close Zen Browser before making any changes. "
            "Restart Zen Browser after making modifications to see the effects."
        )
        note_label.setStyleSheet("color: #d9534f;")
        note_label.setWordWrap(True)
        layout.addWidget(note_label)

        # Don't show again checkbox
        self.dont_show_checkbox = QCheckBox("Don't show this message again")
        layout.addWidget(self.dont_show_checkbox)

        # Continue button
        button_box = QHBoxLayout()
        continue_button = QPushButton("Close")  # Changed from "Get Started" to "Close"
        continue_button.setStyleSheet("padding: 6px 12px;")
        continue_button.clicked.connect(self.handle_close)
        button_box.addStretch()
        button_box.addWidget(continue_button)
        layout.addLayout(button_box)

        # Set window size and position
        self.setMinimumWidth(500)
        self.adjustSize()

    def handle_close(self):
        """Handle window close and save preferences"""
        self.save_preference()
        self.close()

    def save_preference(self):
        """Save the user's preference about showing the welcome dialog"""
        if self.dont_show_checkbox.isChecked():
            config_dir = os.path.expanduser('~/.config/userchrome-loader')
            os.makedirs(config_dir, exist_ok=True)

            config_path = os.path.join(config_dir, 'preferences.ini')
            config = configparser.ConfigParser()

            if os.path.exists(config_path):
                config.read(config_path)

            if not config.has_section('Preferences'):
                config.add_section('Preferences')

            config['Preferences']['show_welcome'] = 'false'

            with open(config_path, 'w', encoding='utf-8') as f:
                config.write(f)

    @staticmethod
    def should_show() -> bool:
        """Check if the welcome dialog should be shown"""
        config_path = os.path.expanduser('~/.config/userchrome-loader/preferences.ini')
        if os.path.exists(config_path):
            config = configparser.ConfigParser()
            config.read(config_path)
            return config.get('Preferences', 'show_welcome', fallback='true').lower() == 'true'
        return True

class SubfolderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Preference")
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Add description
        layout.addWidget(QLabel("How should the files be imported?"))

        # Add radio buttons
        self.direct_radio = QRadioButton("Copy directly to chrome folder")
        self.subfolder_radio = QRadioButton("Create subfolder")
        self.direct_radio.setChecked(True)

        layout.addWidget(self.direct_radio)
        layout.addWidget(self.subfolder_radio)

        # Add buttons
        button_box = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_box.addWidget(ok_button)
        button_box.addWidget(cancel_button)
        layout.addLayout(button_box)

    def get_selection(self):
        if self.direct_radio.isChecked():
            return "1"
        elif self.subfolder_radio.isChecked():
            return "2"
        else:
            return "3"

class ReplaceFileDialog(QDialog):
    def __init__(self, filename: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("File Already Exists")
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Add warning message
        message = QLabel(f"Warning: '{filename}' already exists in chrome directory.\nDo you want to replace it?")
        layout.addWidget(message)

        # Add buttons
        button_box = QHBoxLayout()
        yes_button = QPushButton("Yes")
        yes_button.clicked.connect(self.accept)
        no_button = QPushButton("No")
        no_button.clicked.connect(self.reject)

        button_box.addWidget(yes_button)
        button_box.addWidget(no_button)
        layout.addLayout(button_box)

class RemoveAllImportsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Remove All")
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Warning icon and message
        warning_label = QLabel("⚠️ Warning")
        warning_label.setStyleSheet("font-size: 18px; color: #f0ad4e;")
        layout.addWidget(warning_label)

        message = QLabel(
            "This will remove all CSS imports from userChrome.css.\n"
            "This action cannot be undone.\n\n"
            "Are you sure you want to continue?"
        )
        message.setWordWrap(True)
        layout.addWidget(message)

        # Buttons
        button_box = QHBoxLayout()
        remove_button = QPushButton("Remove All")
        remove_button.setStyleSheet("background-color: #d9534f; color: white;")
        remove_button.clicked.connect(self.accept)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_box.addWidget(cancel_button)
        button_box.addWidget(remove_button)
        layout.addLayout(button_box)

class GenericConfirmDialog(QDialog):
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(message))

        button_box = QHBoxLayout()
        yes_button = QPushButton("Yes")
        yes_button.clicked.connect(self.accept)
        no_button = QPushButton("No")
        no_button.clicked.connect(self.reject)

        button_box.addWidget(yes_button)
        button_box.addWidget(no_button)
        layout.addLayout(button_box)

class ExistingFilesDialog(QDialog):
    def __init__(self, existing_files: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Files Already Exist")
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Add message and list of files
        layout.addWidget(QLabel("The following files already exist:"))
        files_list = QLabel("\n".join(f"- {f}" for f in existing_files))
        layout.addWidget(files_list)

        layout.addWidget(QLabel("\nHow would you like to handle existing files?"))

        # Add radio buttons
        self.replace_radio = QRadioButton("Replace all")
        self.skip_radio = QRadioButton("Skip existing (keep old files)")
        self.replace_radio.setChecked(True)

        layout.addWidget(self.replace_radio)
        layout.addWidget(self.skip_radio)

        # Add buttons
        button_box = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_box.addWidget(ok_button)
        button_box.addWidget(cancel_button)
        layout.addLayout(button_box)

    def get_selection(self) -> str:
        return "1" if self.replace_radio.isChecked() else "2"

class MainWindow(QMainWindow):
    INSTALLATION_PAGE = 0
    PROFILE_PAGE = 1
    MAIN_MENU_PAGE = 2
    IMPORT_PAGE = 3
    MANAGE_PAGE = 4

    def __init__(self):
        super().__init__()
        self.chrome_loader = ChromeLoader()

        # Show welcome dialog if needed
        if WelcomeDialog.should_show():
            self.welcome_dialog = WelcomeDialog(self)
            self.welcome_dialog.show()  # Show as a window instead of modal dialog

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('UserChrome Loader')
        self.setMinimumSize(600, 400)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create stacked widget for different pages
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Create pages
        self.setup_installation_page()
        self.setup_profile_page()
        self.setup_main_menu_page()
        self.setup_import_page()
        self.setup_manage_imports_page()

        # Start with installation selection
        self.load_installations()
        self.stacked_widget.setCurrentIndex(0)

    def setup_installation_page(self):
        # First check if we should skip this page
        if not sys.platform.startswith('linux'):
            # For non-Linux systems, automatically proceed with standard installation
            self.chrome_loader.installation_type = 'standard'
            self.chrome_loader.setup_paths()
            self.load_profiles()
            self.stacked_widget.setCurrentIndex(self.PROFILE_PAGE)
            return

        # Check available installations on Linux
        flatpak_path = os.path.join(
            self.chrome_loader.home_dir,
            '.var',
            'app',
            'io.github.zen_browser.zen',
            '.zen',
            'profiles.ini'
        )

        standard_path = os.path.join(
            self.chrome_loader.home_dir,
            '.zen',
            'profiles.ini'
        )

        installations = []
        if os.path.exists(flatpak_path):
            installations.append(('Flatpak Installation', 'flatpak', flatpak_path))
        if os.path.exists(standard_path):
            installations.append(('Standard Installation', 'standard', standard_path))

        if not installations:
            # No installations found, proceed with standard
            QMessageBox.warning(
                self,
                "No Installation Found",
                "No Zen Browser installation found.\nProceeding with standard installation."
            )
            self.chrome_loader.installation_type = 'standard'
            self.chrome_loader.setup_paths()
            self.load_profiles()
            self.stacked_widget.setCurrentIndex(self.PROFILE_PAGE)
            return

        if len(installations) == 1:
            # Single installation found, automatically select it
            install_type = installations[0][1]
            self.chrome_loader.installation_type = install_type
            self.chrome_loader.setup_paths()
            self.load_profiles()
            self.stacked_widget.setCurrentIndex(self.PROFILE_PAGE)
            return

        # Only create the installation page if multiple installations are found
        page = QWidget()
        layout = QVBoxLayout(page)

        # Title and description
        layout.addWidget(QLabel("Select Zen Browser Installation:"))

        # Installation type selection
        self.installation_combo = QComboBox()
        for display_name, install_type, path in installations:
            self.installation_combo.addItem(f"{display_name} ({path})", install_type)

        # Buttons
        button_layout = QHBoxLayout()
        select_button = QPushButton("Select Installation")
        select_button.clicked.connect(self.handle_installation_selection)
        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.close)

        button_layout.addWidget(select_button)
        button_layout.addWidget(exit_button)

        layout.addWidget(self.installation_combo)
        layout.addLayout(button_layout)
        layout.addStretch()

        self.stacked_widget.addWidget(page)

    def load_installations(self):
        """Load available Zen Browser installations"""
        # The logic is now handled in setup_installation_page
        self.stacked_widget.setCurrentIndex(0)

    def handle_installation_selection(self):
        """Handle installation selection"""
        if self.installation_combo.count() == 0:
            return

        installation_type = self.installation_combo.currentData()
        self.chrome_loader.installation_type = installation_type
        self.chrome_loader.setup_paths()
        self.load_profiles()
        self.stacked_widget.setCurrentIndex(1)

    def setup_profile_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        # Profile selection
        profile_label = QLabel("Select Profile:")
        self.profile_combo = QComboBox()

        # Buttons
        button_layout = QHBoxLayout()
        select_button = QPushButton("Select Profile")
        select_button.clicked.connect(self.handle_profile_selection)
        back_button = QPushButton("Back")
        back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(self.INSTALLATION_PAGE))
        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.close)

        button_layout.addWidget(select_button)
        button_layout.addWidget(back_button)
        button_layout.addWidget(exit_button)

        layout.addWidget(profile_label)
        layout.addWidget(self.profile_combo)
        layout.addLayout(button_layout)
        layout.addStretch()

        self.stacked_widget.addWidget(page)

    def setup_main_menu_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        import_button = QPushButton("Import CSS")
        import_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(self.IMPORT_PAGE))

        manage_button = QPushButton("Manage Imports")
        manage_button.clicked.connect(self.load_manage_imports)

        back_button = QPushButton("Back to Profile Selection")
        back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(self.PROFILE_PAGE))

        layout.addWidget(import_button)
        layout.addWidget(manage_button)
        layout.addWidget(back_button)
        layout.addStretch()

        self.stacked_widget.addWidget(page)


    def setup_import_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        # Import type selection
        import_label = QLabel("Select Import Type:")
        self.import_combo = QComboBox()
        self.import_combo.addItems(["Single CSS File", "Mod Folder"])

        # Import button
        import_button = QPushButton("Choose File/Folder")
        import_button.clicked.connect(self.handle_import)

        # Back button
        back_button = QPushButton("Back to Main Menu")
        back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(self.MAIN_MENU_PAGE))

        layout.addWidget(import_label)
        layout.addWidget(self.import_combo)
        layout.addWidget(import_button)
        layout.addWidget(back_button)
        layout.addStretch()

        self.stacked_widget.addWidget(page)
        back_button = QPushButton("Back to Main Menu")
        back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(self.MAIN_MENU_PAGE))

    def setup_manage_imports_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        # Import list - replace QComboBox with QListWidget
        layout.addWidget(QLabel("Current Imports:"))
        self.import_list = QListWidget()  # Changed from QComboBox to QListWidget
        self.import_list.setMinimumHeight(200)  # Set minimum height for better visibility
        layout.addWidget(self.import_list)

        # Buttons
        toggle_button = QPushButton("Toggle Selected Import")
        toggle_button.clicked.connect(self.toggle_selected_import)

        remove_button = QPushButton("Remove Selected Import")
        remove_button.clicked.connect(self.remove_selected_import)

        remove_all_button = QPushButton("Remove All Imports")
        remove_all_button.clicked.connect(self.remove_all_imports)

        back_button = QPushButton("Back to Main Menu")
        back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(self.MAIN_MENU_PAGE))

        layout.addWidget(toggle_button)
        layout.addWidget(remove_button)
        layout.addWidget(remove_all_button)
        layout.addWidget(back_button)
        layout.addStretch()

        self.stacked_widget.addWidget(page)

    def load_profiles(self):
        """Load available profiles"""
        self.profile_combo.clear()
        profiles = self.chrome_loader.get_profile_info()
        print(f"\nLoading {len(profiles)} profiles into combo box")

        for profile in profiles:
            display_name = str(profile['display_name'])
            is_default = profile['is_default']
            print(f"\nProcessing profile:")
            print(f"  Display name: {display_name}")
            print(f"  Is default: {is_default}")

            if is_default:
                display_name += " (Default)"
                print(f"  Modified display name: {display_name}")

            self.profile_combo.addItem(display_name, profile)

    def handle_profile_selection(self):
        print("Profile selection handler called")

        if self.profile_combo.count() == 0:
            QMessageBox.warning(self, "Error", "No profiles available")
            return

        selected_profile = self.profile_combo.currentData()
        print(f"Selected profile: {selected_profile}")

        if self.chrome_loader.check_profile_lock(selected_profile):
            QMessageBox.warning(self, "Warning",
                              "Profile appears to be in use. Please close Zen Browser first.")
            return

        chrome_dir = self.chrome_loader.setup_chrome_dir(selected_profile)
        print(f"Chrome dir: {chrome_dir}")

        if not chrome_dir:
            QMessageBox.warning(self, "Error", "Could not set up chrome directory")
            return

        self.chrome_dir = chrome_dir
        self.stacked_widget.setCurrentIndex(self.MAIN_MENU_PAGE)

    def handle_import(self):
        import_type = self.import_combo.currentIndex()

        if import_type == 0:  # Single CSS File
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select CSS File", "", "CSS Files (*.css)")
            if file_path:
                self.handle_single_file_import(file_path)
        else:  # Mod Folder
            folder_path = QFileDialog.getExistingDirectory(
                self, "Select Mod Folder")
            if folder_path:
                self.handle_folder_import(folder_path)

    def handle_existing_files(self, existing_files: list[str]) -> str | None:
        """Show dialog for handling existing files"""
        dialog = ExistingFilesDialog(existing_files, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_selection()
        return None

    def confirm_replace(self, filename: str) -> bool:
        """Show dialog to confirm file replacement"""
        dialog = ReplaceFileDialog(filename, self)
        return dialog.exec() == QDialog.DialogCode.Accepted

    def get_file_path(self) -> str | None:
        """Get file path using Qt file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSS File",
            "",
            "CSS Files (*.css)"
        )
        return file_path if file_path else None

    def get_folder_path(self) -> str | None:
        """Get folder path using Qt folder dialog"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Mod Folder"
        )
        return folder_path if folder_path else None

    def handle_single_file_import(self, file_path):
        """Handle importing a single CSS file"""
        if not file_path:
            return

        filename = os.path.basename(file_path)
        target_filename = filename

        # Handle special cases for userChrome.css and mod.css
        if filename.lower() in ['userchrome.css', 'mod.css']:
            target_filename = 'mod.css'

        destination = os.path.join(self.chrome_dir, target_filename)

        # Check for filename conflicts
        if os.path.exists(destination):
            if not self.confirm_replace(target_filename):
                # If user doesn't want to replace, create a new filename
                base, ext = os.path.splitext(target_filename)
                counter = 1
                while os.path.exists(destination):
                    target_filename = f"{base}_{counter}{ext}"
                    destination = os.path.join(self.chrome_dir, target_filename)
                    counter += 1

        try:
            # Create chrome directory if it doesn't exist
            os.makedirs(self.chrome_dir, exist_ok=True)

            # Copy the file
            shutil.copy2(file_path, destination)

            # Handle userChrome.css
            userchrome_path = os.path.join(self.chrome_dir, 'userChrome.css')
            import_line = f"@import url('{target_filename}');\n"

            # Read existing content or create new
            existing_content = ""
            if os.path.exists(userchrome_path):
                with open(userchrome_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()

            # Update userChrome.css
            if not any(import_line.strip() in line for line in existing_content.splitlines()):
                if existing_content and not existing_content.endswith('\n'):
                    existing_content += '\n'
                existing_content += import_line

                with open(userchrome_path, 'w', encoding='utf-8') as f:
                    f.write(existing_content)

            # Refresh the imports list
            self.refresh_imports_list()

            QMessageBox.information(
                self,
                "Success",
                "CSS file imported successfully!\nPlease restart Zen Browser to apply changes."
            )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to import CSS file: {str(e)}")

    def handle_folder_import(self, folder_path):
        """Handle importing a mod folder"""
        if not folder_path:
            return

        # Supported file extensions
        SUPPORTED_EXTENSIONS = {
            # CSS files
            '.css',
            # Images
            '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico',
            # Fonts
            '.ttf', '.otf', '.woff', '.woff2', '.eot'
        }

        # Show subfolder preference dialog
        dialog = SubfolderDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        organization = dialog.get_selection()
        folder_name = os.path.basename(folder_path)

        # Set up destination
        destination = os.path.join(self.chrome_dir, folder_name) if organization == "2" else self.chrome_dir

        try:
            # Create destination directory if it doesn't exist
            os.makedirs(destination, exist_ok=True)

            # Track if we found and handled userChrome.css or mod.css
            main_css_handled = False
            import_line = None
            files_copied = []

            # First pass: Copy all supported files except userChrome.css and mod.css
            for root, _, files in os.walk(folder_path):
                for file in files:
                    # Check if file extension is supported
                    if not any(file.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                        continue

                    if file.lower() not in ['userchrome.css', 'mod.css']:
                        # Get the relative path from the source folder
                        rel_path = os.path.relpath(root, folder_path)
                        source_file = os.path.join(root, file)

                        if rel_path == '.':
                            # File is in the root of the source folder
                            target_file = os.path.join(destination, file)
                        else:
                            # File is in a subfolder
                            target_dir = os.path.join(destination, rel_path)
                            os.makedirs(target_dir, exist_ok=True)
                            target_file = os.path.join(target_dir, file)

                        shutil.copy2(source_file, target_file)
                        files_copied.append(os.path.relpath(target_file, self.chrome_dir))

            # Second pass: Handle userChrome.css or mod.css
            source_userchrome = os.path.join(folder_path, 'userChrome.css')
            source_mod = os.path.join(folder_path, 'mod.css')

            if os.path.exists(source_userchrome) or os.path.exists(source_mod):
                source_file = source_userchrome if os.path.exists(source_userchrome) else source_mod
                target_mod = os.path.join(destination, 'mod.css')
                shutil.copy2(source_file, target_mod)
                main_css_handled = True
                files_copied.append(os.path.relpath(target_mod, self.chrome_dir))

                # Create import line
                if organization == "2":
                    import_line = f"@import url('{folder_name}/mod.css');\n"
                else:
                    import_line = "@import url('mod.css');\n"

            # Update userChrome.css if we have an import line
            if import_line:
                userchrome_path = os.path.join(self.chrome_dir, 'userChrome.css')
                existing_content = ""
                if os.path.exists(userchrome_path):
                    with open(userchrome_path, 'r', encoding='utf-8') as f:
                        existing_content = f.read()

                if not any(import_line.strip() in line for line in existing_content.splitlines()):
                    if existing_content and not existing_content.endswith('\n'):
                        existing_content += '\n'
                    existing_content += import_line

                    with open(userchrome_path, 'w', encoding='utf-8') as f:
                        f.write(existing_content)

            # Refresh the imports list
            self.refresh_imports_list()

            # Show summary message
            if files_copied:
                message = "Files copied:\n" + "\n".join(f"- {f}" for f in files_copied)
                if main_css_handled:
                    message += "\n\nMod folder imported successfully!"
                else:
                    message += "\n\nWarning: No userChrome.css or mod.css found."
                message += "\n\nPlease restart Zen Browser to apply changes."

                QMessageBox.information(
                    self,
                    "Import Complete",
                    message
                )
            else:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "No supported files found in the selected folder."
                )

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to import mod folder: {str(e)}")

    def refresh_imports_list(self):
        """Refresh the imports list in the manage imports page"""
        if not hasattr(self, 'import_list'):
            return

        self.import_list.clear()  # Changed from import_list_combo to import_list
        userchrome_path = os.path.join(self.chrome_dir, 'userChrome.css')

        if not os.path.exists(userchrome_path):
            return

        try:
            with open(userchrome_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                if '@import' in line:
                    # Check if the line is commented out
                    is_enabled = not (line.strip().startswith('/*') and line.strip().endswith('*/'))
                    # Remove comment markers for display
                    display_line = line.replace('/* ', '').replace(' */', '') if not is_enabled else line
                    status = "Enabled" if is_enabled else "Disabled"
                    self.import_list.addItem(f"[{status}] {display_line}")

        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to refresh imports list: {str(e)}"
            )

    def load_manage_imports(self):
        self.import_list.clear()
        imports = self.chrome_loader.list_imports(
            f"{self.chrome_dir}/userChrome.css")

        for _, line, enabled in imports:
            status = "Enabled" if enabled else "Disabled"
            self.import_list.addItem(f"[{status}] {line}")

        self.stacked_widget.setCurrentIndex(self.MANAGE_PAGE)

    def toggle_selected_import(self):
        """Toggle selected import between enabled and disabled state"""
        if self.import_list.count() == 0:
            return

        current_item = self.import_list.currentItem()
        if not current_item:
            return

        current_text = current_item.text()
        import_line = current_text[current_text.find(']') + 2:]
        is_enabled = current_text.startswith('[Enabled]')

        try:
            userchrome_path = os.path.join(self.chrome_dir, 'userChrome.css')
            with open(userchrome_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Find and update the matching line
            for i, line in enumerate(lines):
                if import_line.strip() in line.strip():
                    if is_enabled:
                        # Disable: Add comment markers
                        lines[i] = f"/* {line.strip()} */\n"
                    else:
                        # Enable: Remove comment markers
                        lines[i] = line.strip().replace('/* ', '').replace(' */', '') + '\n'
                    break

            # Write the updated content
            with open(userchrome_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            # Refresh the display
            self.refresh_imports_list()

            # Show success message
            status = "disabled" if is_enabled else "enabled"
            QMessageBox.information(
                self,
                "Success",
                f"Import {status}!\nPlease restart Zen Browser to apply changes."
            )

        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to toggle import: {str(e)}"
            )

    def remove_selected_import(self):
        """Remove selected import and its corresponding files"""
        if self.import_list.count() == 0:
            return

        current_item = self.import_list.currentItem()
        if not current_item:
            return

        current_text = current_item.text()
        import_line = current_text[current_text.find(']') + 2:]

        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Confirm Remove",
            "This will remove both the import line and its corresponding CSS files/folders.\n"
            "This action cannot be undone.\n\n"
            "Do you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        try:
            userchrome_path = os.path.join(self.chrome_dir, 'userChrome.css')

            # Extract the file/folder path from the import line
            import_match = re.search(r"@import\s+url\(['\"](.+?)['\"]", import_line)
            if not import_match:
                QMessageBox.warning(self, "Error", "Could not parse import line")
                return

            imported_path = import_match.group(1)
            full_path = os.path.join(self.chrome_dir, imported_path)

            # Remove the import line from userChrome.css
            with open(userchrome_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            new_lines = [line for line in lines
                        if import_line.strip() not in line.strip()]

            with open(userchrome_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

            # Remove the corresponding files/folders
            if '/' in imported_path or '\\' in imported_path:
                # If the import references a file in a subfolder
                folder_path = os.path.dirname(full_path)
                if os.path.exists(folder_path) and folder_path != self.chrome_dir:
                    shutil.rmtree(folder_path)
                    print(f"Removed folder: {folder_path}")
            else:
                # If it's a single file in the chrome directory
                if os.path.exists(full_path):
                    os.remove(full_path)
                    print(f"Removed file: {full_path}")

            # Refresh the display
            self.refresh_imports_list()

            QMessageBox.information(
                self,
                "Success",
                "Import and associated files removed successfully."
            )

        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to remove import and files: {str(e)}"
            )

    def remove_all_imports(self):
        """Remove all imports and their corresponding files"""
        dialog = RemoveAllImportsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            userchrome_path = os.path.join(self.chrome_dir, 'userChrome.css')
            if self.chrome_loader.remove_all_imports(userchrome_path):
                QMessageBox.information(
                    self,
                    "Success",
                    "All imports have been removed successfully."
                )
                self.refresh_imports_list()
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Failed to remove imports. Please check the console for details."
                )

    def cleanup_empty_folders(self, directory):
        """Recursively remove empty folders"""
        for root, dirs, files in os.walk(directory, topdown=False):
            for dirname in dirs:
                dir_path = os.path.join(root, dirname)
                try:
                    if not os.listdir(dir_path):  # Check if directory is empty
                        if dir_path != self.chrome_dir:  # Don't remove chrome dir itself
                            os.rmdir(dir_path)
                            print(f"Removed empty directory: {dir_path}")
                except OSError:
                    pass  # Handle case where directory might be locked or already removed
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
