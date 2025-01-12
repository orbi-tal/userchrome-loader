""" UserChrome Loader
Provides a User-Friendly way to load Userchrome Scripts for Zen Browser
"""

import os
import sys
import configparser
import re
import platform
import shutil
import pycurl
import tempfile
import json
import libarchive.public as la
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from dataclasses import dataclass
from typing import TypeAlias, Final, Any
from typing_extensions import TypeGuard
from collections.abc import Mapping
from io import BytesIO
from PyQt6.QtCore import QSettings

ProfileDict: TypeAlias = dict[str, str | bool]
StrDict: TypeAlias = dict[str, str]
StrList: TypeAlias = list[str]
StrSet: TypeAlias = set[str]
Installation = tuple[str, str]

@dataclass
class ModInfo:
    url: str
    last_updated: float
    version: str | None
    import_path: str
    type: str
    metadata: dict[str, Any]
    etag: str | None

class DownloadManager:
    """Handles file downloads and validation"""
    ALLOWED_EXTENSIONS = {
            '.css', '.png', '.jpg', '.jpeg', '.gif',
            '.svg', '.webp', '.ttf', '.otf', '.woff',
            '.woff2', '.eot', '.ico'
        }

    def __init__(self) -> None:
        self.temp_dir: str = tempfile.mkdtemp(prefix='ucloader_')
        self.curl = pycurl.Curl()
        self.setup_curl()

    def setup_curl(self):
        """Initialize or reinitialize curl object"""
        if self.curl is None:
            self.curl = pycurl.Curl()

        self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
        self.curl.setopt(pycurl.MAXREDIRS, 5)
        self.curl.setopt(pycurl.TIMEOUT, 300)
        self.curl.setopt(pycurl.HTTPHEADER, [
            'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language: en-US,en;q=0.5',
            'Accept-Encoding: gzip, deflate, br',
            'Connection: keep-alive',
        ])

    def cleanup(self):
        if self.curl:
            self.curl.close()
        if self.temp_dir:
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"Warning: Failed to clean up temporary directory: {e}")

    def validate_url(self, url: str) -> bool:
        try:
            # Add https:// if no protocol is specified
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                return False

            # Add supported domains here
            supported_domains = {
                'raw.githubusercontent.com',
                'gitlab.com',
                'bitbucket.org',
                # Add more supported domains as needed
            }

            domain = parsed.netloc.lower()
            if not any(domain.endswith(d) for d in supported_domains):
                # Check file extension for direct downloads
                valid_extensions = {'.zip', '.rar', '.7z', '.tar', '.gz', '.tgz', '.bz2', '.xz'}
                return any(parsed.path.lower().endswith(ext) for ext in valid_extensions)

            return True
        except Exception:
            return False

    def download_and_validate(self, url: str) -> tuple[bool, str, str]:
        """
        Download and validate content from URL
        Returns: (success, message, extracted_path)
        """
        try:
            # Create temporary directory
            self.temp_dir = tempfile.mkdtemp(prefix='ucloader_')

            # Check if it's a GitHub URL
            if 'github.com' in url:
                return self.handle_github_url(url)

            # Validate other URLs
            if not self.validate_url(url):
                return False, "Invalid or unsupported URL", ""

            # Handle direct download for archives
            archive_path = os.path.join(self.temp_dir, 'archive')
            success, message = self.download_file(url, archive_path)
            if not success:
                return False, message, ""

            # Extract and validate archive
            extract_path = os.path.join(self.temp_dir, 'extracted')
            success, message, final_path = self.process_archive(archive_path, extract_path)
            if not success:
                return False, message, ""

            # Validate content
            css_files = self.find_css_files(final_path)
            if not css_files:
                return False, "No CSS files found in downloaded content", ""

            return True, "Download and validation successful", final_path

        except Exception as e:
            return False, f"Download failed: {str(e)}", ""

    def download_file(self, url: str, path: str) -> tuple[bool, str]:
        """Download file"""
        buffer = BytesIO()
        try:
            self.curl.setopt(pycurl.URL, url)
            self.curl.setopt(pycurl.WRITEDATA, buffer)
            self.curl.perform()

            with open(path, 'wb') as f:
                f.write(buffer.getvalue())
            return True, "Success"
        except Exception as e:
            return False, str(e)
        finally:
            buffer.close()

    def handle_github_url(self, url: str) -> tuple[bool, str, str]:
        """Handle GitHub repository or file downloads"""
        if self.temp_dir is None:
                self.temp_dir = tempfile.mkdtemp(prefix='ucloader_')

        try:
            # Parse GitHub URL
            parts = url.split('github.com/')
            if len(parts) != 2:
                return False, "Invalid GitHub URL", ""

            path_parts = parts[1].split('/')
            if len(path_parts) < 2:
                return False, "Invalid GitHub repository path", ""

            owner = path_parts[0]
            repo = path_parts[1]

            # Create temporary directory if not exists
            if not self.temp_dir:
                self.temp_dir = tempfile.mkdtemp(prefix='ucloader_')

            # Determine if it's a file or repository
            if len(path_parts) > 4 and path_parts[2] in ('blob', 'tree'):
                # It's a file or directory within the repository
                branch = path_parts[3]
                file_path = '/'.join(path_parts[4:])

                # Convert blob URL to raw URL for single files
                if path_parts[2] == 'blob':
                    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
                    download_path = os.path.join(self.temp_dir, os.path.basename(file_path))
                    success, message = self.download_file(raw_url, download_path)
                    if not success:
                        return False, message, ""
                    return True, "File downloaded successfully", self.temp_dir

            # Default to downloading the repository
            download_url = f"https://api.github.com/repos/{owner}/{repo}/zipball"
            archive_path = os.path.join(self.temp_dir, 'repo.zip')

            # Download repository
            success, message = self.download_file(download_url, archive_path)
            if not success:
                return False, message, ""

            # Extract the archive
            extract_path = os.path.join(self.temp_dir, 'extracted')
            success, message, final_path = self.process_archive(archive_path, extract_path)
            if not success:
                return False, message, ""

            return True, "Repository downloaded successfully", final_path

        except Exception as e:
            return False, f"Failed to process GitHub URL: {str(e)}", ""

    def process_archive(self, archive_path: str, extract_path: str) -> tuple[bool, str, str]:
        """Extract and validate archive"""
        try:
            os.makedirs(extract_path, exist_ok=True)

            # Extract archive
            self.extract_archive(archive_path, extract_path)

            # Validate extracted content
            if not self.validate_extracted_content(extract_path):
                return False, "Content validation failed", ""

            # Find main directory
            items = os.listdir(extract_path)
            if len(items) == 1 and os.path.isdir(os.path.join(extract_path, items[0])):
                final_path = os.path.join(extract_path, items[0])
            else:
                final_path = extract_path

            return True, "Archive processed successfully", final_path

        except Exception as e:
            return False, f"Archive processing failed: {str(e)}", ""

    def extract_archive(self, archive_path: str, extract_path: str):
        """Extract archive using libarchive"""

        ALLOWED_EXTENSIONS = {
            '.css', '.png', '.jpg', '.jpeg', '.gif',
            '.svg', '.webp', '.ttf', '.otf', '.woff',
            '.woff2', '.eot', '.ico'
        }
        try:
            with la.file_reader(archive_path) as archive:
                for entry in archive:
                    # Security checks
                    path = entry.pathname
                    if path.startswith(('/', '\\')) or '..' in path:
                        continue

                    # Check file extension
                    ext = os.path.splitext(path)[1].lower()
                    if ext not in ALLOWED_EXTENSIONS:
                        continue

                    target_path = os.path.join(extract_path, path)
                    target_dir = os.path.dirname(target_path)

                    try:
                        os.makedirs(target_dir, exist_ok=True)
                        with open(target_path, 'wb') as f:
                            for block in entry.get_blocks():
                                f.write(block)
                    except (OSError, IOError) as e:
                        print(f"Warning: Failed to extract {path}: {e}")
                        continue

        except ImportError:
            # Fallback to zipfile for basic ZIP support
            import zipfile
            if zipfile.is_zipfile(archive_path):
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    for member in zip_ref.namelist():
                        # Security checks
                        if member.startswith(('/', '\\')) or '..' in member:
                            continue

                        # Check file extension
                        ext = os.path.splitext(member)[1].lower()
                        if ext not in ALLOWED_EXTENSIONS:
                            continue

                        try:
                            zip_ref.extract(member, extract_path)
                        except Exception as e:
                            print(f"Warning: Failed to extract {member}: {e}")
                            continue
            else:
                raise Exception("Archive format not supported. Please use ZIP format or install libarchive-c")

        except Exception as e:
            raise Exception(f"Failed to extract archive: {str(e)}")

    def validate_extracted_content(self, path: str) -> bool:
        """Validate extracted content"""
        MAX_TOTAL_SIZE = 100 * 1024 * 1024  # 100MB
        MAX_FILES = 1000

        total_size = 0
        file_count = 0

        for root, _, files in os.walk(path):
            file_count += len(files)
            if file_count > MAX_FILES:
                return False

            for file in files:
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path)
                    total_size += size
                    if total_size > MAX_TOTAL_SIZE:
                        return False
                except OSError:
                    continue

        return file_count > 0

    def find_css_files(self, path: str) -> list[dict[str, Any]]:
        """Find and validate CSS files"""
        css_files: list[dict[str, Any]] = []
        MAX_CSS_SIZE = 1 * 1024 * 1024  # 1MB

        for root, _, files in os.walk(path):
            for file in files:
                if not file.lower().endswith('.css'):
                    continue

                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path)
                    if size > MAX_CSS_SIZE:
                        continue

                    css_files.append({
                        'path': file_path,
                        'relative_path': os.path.relpath(file_path, path),
                        'name': file,
                        'is_main': file.lower() in ['userchrome.css', 'mod.css'],
                        'size': size
                    })
                except OSError:
                    continue

        return css_files

    def check_for_updates(self, mod_info: ModInfo) -> tuple[bool, str, dict[str, Any]]:
        """Check if updates are available for a mod
        Returns: (has_update, message, update_info)
        """
        if mod_info.type == 'github':
            return self._check_github_updates(mod_info)
        elif mod_info.type == 'gitlab':
            return self._check_gitlab_updates(mod_info)
        else:
            return self._check_direct_updates(mod_info)

    def _check_github_updates(self, mod_info: ModInfo) -> tuple[bool, str, dict[str, Any]]:
        """Check for updates on GitHub repository"""
        try:
            # Extract owner and repo from URL
            parts = mod_info.url.split('github.com/')
            if len(parts) != 2:
                return False, "Invalid GitHub URL", {}

            owner, repo = parts[1].split('/')[:2]
            api_url = f"https://api.github.com/repos/{owner}/{repo}"

            # Set up curl request
            buffer = BytesIO()
            self.curl.setopt(pycurl.URL, api_url)
            self.curl.setopt(pycurl.WRITEDATA, buffer)

            # Add headers for GitHub API
            self.curl.setopt(pycurl.HTTPHEADER, [
                'Accept: application/vnd.github.v3+json',
                'User-Agent: UserChromeLoader'
            ])

            self.curl.perform()

            # Parse response
            response = json.loads(buffer.getvalue().decode('utf-8'))

            latest_update = response.get('pushed_at')
            if not latest_update:
                return False, "Could not determine latest update", {}

            # Convert to timestamp for comparison
            latest_timestamp = datetime.strptime(
                latest_update, '%Y-%m-%dT%H:%M:%SZ'
            ).timestamp()

            has_update = latest_timestamp > mod_info.last_updated

            return has_update, (
                "Update available" if has_update else "Up to date"
            ), {
                'version': response.get('default_branch'),
                'last_updated': latest_timestamp,
                'description': response.get('description', '')
            }

        except Exception as e:
            return False, f"Failed to check for updates: {str(e)}", {}

    def _check_gitlab_updates(self, mod_info: ModInfo) -> tuple[bool, str, dict[str, Any]]:
        """Check for updates on GitLab repository"""
        try:
            # Extract project info from URL
            parts = mod_info.url.split('gitlab.com/')
            if len(parts) != 2:
                return False, "Invalid GitLab URL", {}

            project_path = parts[1].split('/')
            if len(project_path) < 2:
                return False, "Invalid GitLab project path", {}

            # Construct API URL
            project_id = '/'.join(project_path[:2])
            api_url = f"https://gitlab.com/api/v4/projects/{project_id.replace('/', '%2F')}"

            # Set up curl request
            buffer = BytesIO()
            self.curl.setopt(pycurl.URL, api_url)
            self.curl.setopt(pycurl.WRITEDATA, buffer)

            # Add headers for GitLab API
            self.curl.setopt(pycurl.HTTPHEADER, [
                'Accept: application/json',
                'User-Agent: UserChromeLoader'
            ])

            self.curl.perform()

            # Parse response
            response = json.loads(buffer.getvalue().decode('utf-8'))

            last_activity = response.get('last_activity_at')
            if not last_activity:
                return False, "Could not determine latest update", {}

            # Convert to timestamp for comparison
            latest_timestamp = datetime.strptime(
                last_activity, '%Y-%m-%dT%H:%M:%S.%fZ'
            ).timestamp()

            has_update = latest_timestamp > mod_info.last_updated

            return has_update, (
                "Update available" if has_update else "Up to date"
            ), {
                'version': response.get('default_branch'),
                'last_updated': latest_timestamp,
                'description': response.get('description', '')
            }

        except Exception as e:
            return False, f"Failed to check for updates: {str(e)}", {}

    def _check_direct_updates(self, mod_info: ModInfo) -> tuple[bool, str, dict[str, Any]]:
        """Check for updates on direct file URLs"""
        try:
            buffer = BytesIO()
            self.curl.setopt(pycurl.URL, mod_info.url)
            self.curl.setopt(pycurl.NOBODY, 1)
            self.curl.setopt(pycurl.WRITEDATA, buffer)
            self.curl.perform()

            # Get last modified time
            last_modified = self.curl.getinfo(pycurl.INFO_FILETIME)

            # Reset curl options
            self.curl.setopt(pycurl.NOBODY, 0)

            if last_modified == -1:  # No last-modified header
                return False, "Could not determine file age", {}

            has_update = last_modified > mod_info.last_updated

            return has_update, (
                "Update available" if has_update else "Up to date"
            ), {
                'last_updated': last_modified
            }

        except Exception as e:
            return False, f"Failed to check for updates: {str(e)}", {}

class ModManager:
    def __init__(self):
        self.settings = QSettings('UserChromeLoader', 'UserChromeLoader')

    def save_mod_info(self, url: str, mod_info: ModInfo) -> None:
        """Save information about an imported mod"""
        mods = self.settings.value('imported_mods', {}, dict)
        mods[url] = {
            'last_updated': mod_info.last_updated,
            'version': mod_info.version,
            'import_path': mod_info.import_path,
            'type': mod_info.type,
            'metadata': mod_info.metadata,
            'etag': mod_info.etag
        }
        self.settings.setValue('imported_mods', mods)

    def get_mod_info(self, url: str) -> ModInfo | None:
        """Get information about an imported mod"""
        mods = self.settings.value('imported_mods', {}, dict)
        if url in mods:
            info = mods[url]
            return ModInfo(
                url=url,
                last_updated=info['last_updated'],
                etag=info.get('etag'),
                import_path=info['import_path'],
                version=info.get('version'),
                type=info.get('type', 'direct'),  # Default to 'direct' if not specified
                metadata=info.get('metadata', {})  # Default to empty dict if not specified
            )
        return None

    def get_all_mods(self) -> list[ModInfo]:
        """Get information about all imported mods"""
        mods = self.settings.value('imported_mods', {}, dict)
        return [
            ModInfo(
                url=url,
                last_updated=info['last_updated'],
                etag=info.get('etag'),
                import_path=info['import_path'],
                version=info.get('version'),
                type=info.get('type', 'direct'),  # Default to 'direct' if not specified
                metadata=info.get('metadata', {})  # Default to empty dict if not specified
            )
            for url, info in mods.items()
        ]

    def remove_mod(self, url: str):
        """Remove a mod from the tracked mods"""
        mods = self.settings.value('imported_mods', {}, dict)
        if url in mods:
            del mods[url]
            self.settings.setValue('imported_mods', mods)

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
        self.curl: pycurl.Curl | None = None
        self.setup_curl()
        self.home_dir: str = str(Path.home())
        self.zen_dir: str = ""
        self.profiles_ini_path: str = ""
        self.imported_files: set[str] = set()
        self.installation_type: str | None = installation_type
        self.download_manager: DownloadManager | None = None
        self.temp_dir: str | None = None

    def is_valid_profile(self, profile: Mapping[str, str]) -> TypeGuard[ProfileDict]:
        """Type guard to validate profile structure"""
        required_keys = {'name', 'path', 'display_name', 'is_default'}
        return all(key in profile for key in required_keys)

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to remove problematic characters"""
        return "".join(c for c in filename if c.isalnum() or c in ".-_ ")

    def check_path_length(self, path: str) -> bool:
        """Check if path length is valid for the current platform"""
        if platform.system().lower() == 'windows' and len(path) > 260:
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

    def setup_curl(self):
        """Initialize curl object"""
        if not hasattr(self, 'curl') or self.curl is None:
            self.curl = pycurl.Curl()
        self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
        self.curl.setopt(pycurl.MAXREDIRS, 5)
        self.curl.setopt(pycurl.TIMEOUT, 300)
        self.curl.setopt(pycurl.HTTPHEADER, [
            'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language: en-US,en;q=0.5',
            'Accept-Encoding: gzip, deflate, br',
            'Connection: keep-alive',
        ])

    def setup_paths(self):
        system = platform.system().lower()

        if system == 'darwin':  # macOS
            self.zen_dir = os.path.join(
                self.home_dir,
                'Library',
                'Application Support',
                'zen',
                'Profiles'
            )
            self.profiles_ini_path = os.path.join(
                self.zen_dir,
                'profiles.ini'
            )

        elif system == 'windows':  # Windows
            appdata = os.getenv('APPDATA')
            if not appdata:
                raise EnvironmentError("APPDATA environment variable not found")

            self.zen_dir = os.path.join(appdata, 'zen')
            self.profiles_ini_path = os.path.join(self.zen_dir, 'profiles.ini')

            print(f"Windows profile directory: {self.zen_dir}")
            print(f"Profiles.ini path: {self.profiles_ini_path}")

        elif system == 'linux':  # Linux
            installation = self.select_installation()
            if installation == 'flatpak':
                self.zen_dir = os.path.join(
                    self.home_dir,
                    '.var',
                    'app',
                    'io.github.zen_browser.zen',
                    '.zen'
                )
            else:  # standard
                self.zen_dir = os.path.join(self.home_dir, '.zen')
            self.profiles_ini_path = os.path.join(self.zen_dir, 'profiles.ini')

        # Print debug information
        print(f"System: {system}")
        print(f"Home directory: {self.home_dir}")
        print(f"Zen directory: {self.zen_dir}")
        print(f"Profiles.ini path: {self.profiles_ini_path}")

        # Create directories if they don't exist
        os.makedirs(os.path.dirname(self.profiles_ini_path), exist_ok=True)

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

    def get_profile_info(self) -> list[dict[str, str | bool]]:
        """Get Zen Browser profile information from profiles.ini"""
        if not os.path.exists(self.profiles_ini_path):
            print("Profiles.ini not found")
            return []

        config = configparser.ConfigParser()
        try:
            # Read the profiles.ini file
            _ = config.read(self.profiles_ini_path)
            profiles = []

            # Print debug info
            print("\nAvailable sections in profiles.ini:")
            print(config.sections())

            for section in config.sections():
                if section.startswith('Profile'):
                    try:
                        # Get profile details
                        path = config.get(section, 'Path')
                        is_relative = config.getboolean(section, 'IsRelative', fallback=True)
                        name = config.get(section, 'Name', fallback=os.path.basename(path))
                        is_default = config.getboolean(section, 'Default', fallback=False)

                        # Construct full path
                        full_path = os.path.join(self.zen_dir, path) if is_relative else path

                        profile = {
                            'name': os.path.basename(path),
                            'path': full_path,
                            'display_name': name,
                            'is_default': is_default
                        }

                        # Print debug info
                        print(f"\nFound profile:")
                        print(f"  Section: {section}")
                        print(f"  Path: {full_path}")
                        print(f"  Name: {name}")
                        print(f"  Is Default: {is_default}")

                        profiles.append(profile)

                    except Exception as e:
                        print(f"Error processing profile section {section}: {e}")
                        continue

            return profiles

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

        # Strip comments and empty lines for checking imports
        cleaned_lines = []
        in_comment_block = False

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue

            # Handle multi-line comments
            if '/*' in line:
                in_comment_block = True
                line = line[:line.index('/*')].strip()
            if '*/' in line:
                in_comment_block = False
                line = line[line.index('*/') + 2:].strip()

            if not in_comment_block and line:
                # Remove single-line comments
                if '//' in line:
                    line = line[:line.index('//')].strip()
                if line:
                    cleaned_lines.append(line)

        # Check if all non-empty lines are imports
        only_imports = all(
            line.startswith('@import')
            for line in cleaned_lines
        )

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
                "2. Mod Folder\n"
                "Choose (1-2): "
            )
        while True:
                import_type = input(prompt).strip()
                return import_type

    def get_file_path_fallback(self) -> str | None:
        """Simple fallback for file selection using command line"""
        while True:
            file_path = input("Enter path to CSS file (or press Enter to cancel): ").strip()
            if not file_path:
                return None

            # Expand user path (~/something) if present
            file_path = os.path.expanduser(file_path)

            # Check if file exists and is a CSS file
            if os.path.isfile(file_path):
                if file_path.lower().endswith('.css'):
                    return file_path
                else:
                    print("File must have .css extension")
            else:
                print("File not found")

    def get_file_path(self) -> str | None:
        """This will be handled by the GUI file dialog"""
        return None  # Actual file selection is handled in GUI

    def get_folder_path(self) -> str | None:
        """This will be handled by the GUI folder dialog"""
        return None  # Actual folder selection is handled in GUI

    def setup_url_handler(self, url: str, buffer: BytesIO):
        if not self.curl:
            self.curl = pycurl.Curl()
        self.curl.setopt(pycurl.URL, url)
        self.curl.setopt(pycurl.WRITEDATA, buffer)
        self.curl.setopt(pycurl.USERAGENT, 'UserChromeLoader/1.0')

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
        """This will be handled by the GUI dialog"""
        return "1"  # Default value, actual selection is handled in GUI

    def handle_folder_import(self, chrome_dir: str) -> str | None:
        """Handle importing a mod folder"""
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

    def handle_github_url(self, url: str) -> tuple[bool, str, str]:
        if not self.temp_dir:
            self.temp_dir = tempfile.mkdtemp(prefix='ucloader_')

        try:
            parts = url.split('github.com/')
            if len(parts) != 2:
                return False, "Invalid GitHub URL", ""

            path_parts = parts[1].split('/')
            if len(path_parts) < 2:
                return False, "Invalid GitHub repository path", ""

            owner = path_parts[0]
            repo = path_parts[1]

            if len(path_parts) > 4 and path_parts[2] in ('blob', 'tree'):
                branch = path_parts[3]
                file_path = '/'.join(path_parts[4:])

                if path_parts[2] == 'blob':
                    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
                    download_path = str(Path(self.temp_dir) / os.path.basename(file_path))
                    success, message = self.download_file(raw_url, download_path)
                    if not success:
                        return False, message, ""
                    return True, "File downloaded successfully", str(self.temp_dir)

            # Download repository
            download_url = f"https://api.github.com/repos/{owner}/{repo}/zipball"
            archive_path = str(Path(self.temp_dir) / 'repo.zip')
            extract_path = str(Path(self.temp_dir) / 'extracted')

            success, message = self.download_file(download_url, archive_path)
            if not success:
                return False, message, ""

            success, message, final_path = self.process_archive(archive_path, extract_path)
            return success, message, final_path

        except Exception as e:
            return False, f"Failed to process GitHub URL: {str(e)}", ""

    def download_github_contents(self, url: str) -> str | None:
        """Download and process GitHub repository contents"""
        try:
            success, message, path = self.handle_github_url(url)
            if success:
                return path
            return None
        except Exception as e:
            raise RuntimeError(f"Failed to download repository: {e}")

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

    def download_file(self, url: str, save_path: str) -> tuple[bool, str]:
        if not self.curl:
            self.setup_curl()

        buffer = BytesIO()
        try:
            self.curl.setopt(pycurl.URL, url)
            self.curl.setopt(pycurl.WRITEDATA, buffer)
            self.curl.perform()

            response_code = self.curl.getinfo(pycurl.RESPONSE_CODE)
            if response_code != 200:
                return False, f"Download failed with HTTP {response_code}"

            with open(save_path, 'wb') as f:
                f.write(buffer.getvalue())

            return True, "Download successful"

        except pycurl.error as e:
            return False, f"Download error: {str(e)}"
        finally:
            buffer.close()

    def process_archive(self, archive_path: str, extract_path: str) -> tuple[bool, str, str]:
        """Process downloaded archive"""
        try:
            os.makedirs(extract_path, exist_ok=True)
            # Extract archive using libarchive
            with la.file_reader(archive_path) as archive:
                for entry in archive:
                    la.extract.extract_entries([entry], extract_path)
            return True, "Success", extract_path
        except Exception as e:
            return False, str(e), ""

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

    def write_userchrome_content(self, file_path: str, content: str) -> bool:
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
            print("To apply the changes, please restart Zen Browser")

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

            print("\nImport Management Menu:")
            print("1. Toggle imports")
            print("2. Remove specific import")
            print("3. Remove all imports")
            print("4. Return to main menu")

            choice = input("Choose an option (1-4): ").strip()

            if choice == "1":
                self.toggle_imports_menu(imports, userchrome_path)
            elif choice == "2":
                self.remove_specific_import(imports, userchrome_path)
            elif choice == "3":
                if self.remove_all_imports(userchrome_path):
                    print("All imports have been removed")
                    return
            elif choice == "4":
                return
            else:
                print("Invalid choice")

    def toggle_imports_menu(self, imports: list[tuple[int, str, bool]], userchrome_path: str) -> None:
        """Menu for toggling individual imports"""
        if not imports:
            print("No imports found in userChrome.css")
            return

        print("\nCurrent imports:")
        for i, (_, line, enabled) in enumerate(imports):
            status = "Enabled" if enabled else "Disabled"
            print(f"{i+1}. [{status}] {line}")

        choice = input("\nEnter number to toggle import (or 'b' to go back): ").lower()
        if choice == 'b':
            return

        try:
            index = int(choice) - 1
            if 0 <= index < len(imports):
                self.toggle_import(userchrome_path, index, not imports[index][2])
            else:
                print("Invalid selection")
        except ValueError:
            print("Please enter a number or 'b'")

    def remove_specific_import(self, imports: list[tuple[int, str, bool]], userchrome_path: str) -> None:
        """Remove a specific import from userChrome.css"""
        if not imports:
            print("No imports found in userChrome.css")
            return

        print("\nCurrent imports:")
        for i, (_, line, _) in enumerate(imports):
            print(f"{i+1}. {line}")

        choice = input("\nEnter number to remove import (or 'b' to go back): ").lower()
        if choice == 'b':
            return

        try:
            index = int(choice) - 1
            if 0 <= index < len(imports):
                self.remove_import(userchrome_path, imports[index][0])
                print("Import removed successfully")
            else:
                print("Invalid selection")
        except ValueError:
            print("Please enter a number or 'b'")

    def remove_import(self, userchrome_path: str, line_number: int) -> None:
        """Remove a specific import line from the file"""
        try:
            with open(userchrome_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if 0 <= line_number < len(lines):
                del lines[line_number]

                # Remove any empty lines at the end of the file
                while lines and not lines[-1].strip():
                    lines.pop()

                with open(userchrome_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
        except Exception as e:
            print(f"Error removing import: {e}")

    def remove_all_imports(self, userchrome_path: str) -> bool:
        """Remove all imports and their corresponding files/folders"""
        if not os.path.exists(userchrome_path):
            print(f"File not found: {userchrome_path}")
            return False

        chrome_dir = os.path.dirname(userchrome_path)
        files_to_remove = set()
        folders_to_remove = set()

        try:
            # Read the file content
            content = ""
            try:
                with open(userchrome_path, 'r', encoding='utf-8') as file:
                    content = file.read()
            except UnicodeDecodeError:
                with open(userchrome_path, 'r', encoding='latin-1') as file:
                    content = file.read()

            # Find all import statements and collect files/folders to remove
            import_matches = re.finditer(r"@import\s+url\(['\"](.+?)['\"]", content)
            for match in import_matches:
                imported_path = match.group(1)
                full_path = os.path.join(chrome_dir, imported_path)

                # Handle both files and folders
                if '/' in imported_path or '\\' in imported_path:
                    # If the import references a file in a subfolder
                    folder_path = os.path.dirname(full_path)
                    if folder_path != chrome_dir:
                        folders_to_remove.add(folder_path)
                else:
                    # If it's a single file in the chrome directory
                    files_to_remove.add(full_path)

            # Process lines to remove imports
            lines = content.splitlines(True)
            new_lines = []
            skip_next_empty = False

            for line in lines:
                current_line = line.strip()

                if not current_line and skip_next_empty:
                    skip_next_empty = False
                    continue

                is_import = (current_line.startswith('@import') or
                            (current_line.startswith('/*') and '@import' in current_line))

                if is_import:
                    skip_next_empty = True
                    if new_lines and not new_lines[-1].strip():
                        new_lines.pop()
                    continue

                new_lines.append(line)

            # Clean up trailing empty lines
            while new_lines and not new_lines[-1].strip():
                new_lines.pop()

            # Ensure file has at least one newline
            if not new_lines:
                new_lines = ['\n']
            elif not new_lines[-1].endswith('\n'):
                new_lines[-1] += '\n'

            # Write the processed content back to file
            try:
                with open(userchrome_path, 'w', encoding='utf-8') as file:
                    file.writelines(new_lines)
            except UnicodeEncodeError:
                with open(userchrome_path, 'w', encoding='latin-1') as file:
                    file.writelines(new_lines)

            # Remove files and folders
            for file_path in files_to_remove:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        print(f"Removed file: {file_path}")
                    except Exception as e:
                        print(f"Error removing file {file_path}: {e}")

            for folder_path in folders_to_remove:
                if os.path.exists(folder_path):
                    try:
                        shutil.rmtree(folder_path)
                        print(f"Removed folder: {folder_path}")
                    except Exception as e:
                        print(f"Error removing folder {folder_path}: {e}")

            return True

        except Exception as e:
            print(f"Error removing imports: {e}")
            return False

    def confirm_replace(self, filename: str) -> bool:
        """This will be handled by the GUI dialog"""
        return True

    def handle_existing_files(self, existing_files: list[str]) -> str | None:
        """This will be handled by the GUI dialog"""
        return "2"  # Default to skip, actual handling is done in GUI

    def copy_folder(self, source_folder: str, chrome_dir: str, organization: str) -> str | None:
        """Copy a mod folder and return the folder name for import"""
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
            # Only create backup if the file contains non-import content
            if not only_imports and existing_content.strip():
                backup_content = self.handle_backup(chrome_dir, userchrome_path)
                # Only update existing_content if backup was created and user wants to import it
                if backup_content:
                    existing_content = backup_content
            else:
                print("No backup needed - file contains only imports")

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
                print("3. Exit")

                choice = input("Choose an option (1-3): ").strip()

                if choice == "1":
                    self.handle_import(chrome_dir)
                elif choice == "2":
                    self.manage_imports(chrome_dir)
                elif choice == "3":
                    print("Exiting UserChrome Loader...")
                    break
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
