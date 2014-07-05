#!/usr/bin/env python
from distutils.core import setup

version = "0.9.4"

setup(name="fastimport",
      description="VCS fastimport/fastexport parser",
      version=version,
      author="Canonical Ltd",
      author_email="bazaar@lists.canonical.com",
      license="GNU GPL v2 or later",
      url="https://launchpad.net/python-fastimport",
      packages=['fastimport', 'fastimport.tests', 'fastimport.processors'])
