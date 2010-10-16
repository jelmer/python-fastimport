#!/usr/bin/env python
from distutils.core import setup

setup(name="fastimport",
      version="0.9.0dev0",
      description="VCS fastimport/fsatexport parser",
      author="Canonical Ltd",
      author_email="bazaar@lists.canonical.com",
      license = "GNU GPL v2",
      url="https://launchpad.net/python-fastimport",
      packages=['fastimport', 'fastimport.tests', 'fastimport.processors'])
