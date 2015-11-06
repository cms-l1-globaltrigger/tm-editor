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

setup(
    name = 'tmEditor',
    version = '0.1.6',
    description = "Trigger Menu Editor for uGT upgrade",
    author = "Bernhard Arnold",
    author_email = "bernhard.arnold@cern.ch",
    url = "https://twiki.cern.ch/twiki/bin/viewauth/CMS/GlobalTriggerUpgradeL1T-uTme",
    packages = ['tmEditor', ],
    data_files = [],
    scripts = [
        'scripts/tm-editor',
    ],
    provides = ['tmEditor', ],
)
