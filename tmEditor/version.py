#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL: $
# Last committed    : $Revision: $
# Last changed by   : $Author: $
# Last changed date : $Date: $
#

"""Versions.

To change the release version of the editor, just edit the version constants in
 this module.

To extract the version from outside the application (eg. Makefile) just execute
the module with optional flags:

 $ python tmEditor/version.py [-v|-r|--major|--minor|--patch]

"""

__all__ = ["VERSION", "VERSION_MAJOR", "VERSION_MINOR", "VERSION_PATCH", "PKG_RELEASE"]

VERSION_MAJOR = 0
VERSION_MINOR = 3
VERSION_PATCH = 2
PKG_RELEASE = 1

VERSION = ".".join([str(item) for item in VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH])

if __name__ == "__main__":
    import sys, argparse
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--version", action="store_true", help="show version (default)")
    group.add_argument("--major", action="store_true", help="major version")
    group.add_argument("--minor", action="store_true", help="minor version")
    group.add_argument("--patch", action="store_true", help="patch version")
    group.add_argument("-r", "--release", action="store_true", help="show package release version")
    args = parser.parse_args()
    if args.major:
        print VERSION_MAJOR
    elif args.minor:
        print VERSION_MINOR
    elif args.patch:
        print VERSION_PATCH
    elif args.release:
        print PKG_RELEASE
    else:
        print VERSION
    sys.exit(0)
