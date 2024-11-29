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

    print("\nVersion bump complete!")
    print("Don't forget to:")
    print("1. Review the changes")
    print("2. Update the changelog in metainfo.xml if needed")
    print("3. Commit the changes")

if __name__ == "__main__":
    main()