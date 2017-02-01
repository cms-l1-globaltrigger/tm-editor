#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL: $
# Last committed    : $Revision: $
# Last changed by   : $Author: $
# Last changed date : $Date: $
#

from distutils.core import setup
from glob import glob
import subprocess

# Read version from module
version = subprocess.check_output("python tmEditor/version.py --version".split()).strip()

setup(
    name = "tmEditor",
    version = version,
    description = "Trigger Menu Editor for uGT upgrade",
    author = "Bernhard Arnold",
    author_email = "bernhard.arnold@cern.ch",
    url = "http://globaltrigger.hephy.at/upgrade/tme",
    packages = ["tmEditor", "tmEditor.core", "tmEditor.gui"],
    data_files = [],
    scripts = [
        "scripts/tm-editor",
    ],
    provides = ["tmEditor", ],
)
