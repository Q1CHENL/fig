#!/usr/bin/env python3

import re
import sys
import datetime
from pathlib import Path

def get_current_version():
    """Get current version from setup.py"""
    setup_py = Path('setup.py').read_text()
    version_match = re.search(r'version="(\d+\.\d+\.\d+)"', setup_py)
    if version_match:
        return version_match.group(1)
    return "0.0.0"

def bump_version(version, bump_type):
    """Bump version based on type (major, minor, patch)"""
    major, minor, patch = map(int, version.split('.'))
    if bump_type == 'major':
        return f"{major + 1}.0.0"
    elif bump_type == 'minor':
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"

def update_setup_py(new_version):
    """Update version in setup.py"""
    path = Path('setup.py')
    content = path.read_text()
    updated = re.sub(
        r'version="[\d.]+"',
        f'version="{new_version}"',
        content
    )
    path.write_text(updated)
    print(f"Updated setup.py to version {new_version}")

def update_meson_build(new_version):
    """Update version in meson.build"""
    path = Path('meson.build')
    content = path.read_text()
    updated = re.sub(
        r"version: '[\d.]+'",
        f"version: '{new_version}'",
        content
    )
    path.write_text(updated)
    print(f"Updated meson.build to version {new_version}")

def update_metainfo(new_version):
    """Update version in metainfo.xml"""
    path = Path('io.github.Q1CHENL.fig.metainfo.xml')
    content = path.read_text()
    
    # Get current date
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    # Find the releases section
    releases_match = re.search(r'(<releases>.*?</releases>)', content, re.DOTALL)
    if releases_match:
        old_releases = releases_match.group(1)
        new_release = f'<releases>\n    <release version="{new_version}" date="{today}"/>\n    {old_releases[10:]}'
        updated = content.replace(old_releases, new_release)
        path.write_text(updated)
        print(f"Updated metainfo.xml to version {new_version}")
    else:
        print("Could not find releases section in metainfo.xml")

def update_home_py(new_version):
    """Update version in home.py"""
    path = Path('fig/home.py')
    content = path.read_text()
    
    # Update version in about dialog
    updated = re.sub(
        r'about\.set_version\("[\d.]+"\)',
        f'about.set_version("{new_version}")',
        content
    )
    
    # Update version in debug info
    updated = re.sub(
        r'about\.set_debug_info\("Version: [\d.]+\\n',
        f'about.set_debug_info("Version: {new_version}\\n',
        updated
    )
    
    path.write_text(updated)
    print(f"Updated home.py to version {new_version}")

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ['major', 'minor', 'patch']:
        print("Usage: python vbump.py [major|minor|patch]")
        sys.exit(1)
    
    bump_type = sys.argv[1]
    current_version = get_current_version()
    new_version = bump_version(current_version, bump_type)
    
    print(f"Bumping version from {current_version} to {new_version}")
    
    update_setup_py(new_version)
    update_meson_build(new_version)
    update_metainfo(new_version)
    update_home_py(new_version)
    
    print("\nVersion bump complete!")
    print("Don't forget to:")
    print("1. Review the changes")
    print("2. Update the changelog in metainfo.xml if needed")
    print("3. Commit the changes")

if __name__ == "__main__":
    main()