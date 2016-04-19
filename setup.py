#!/usr/bin/env python
from distutils.core import setup

version = "0.9.7dev"

setup(name="fastimport",
      description="VCS fastimport/fastexport parser",
      version=version,
      author="Canonical Ltd",
      author_email="bazaar@lists.canonical.com",
      maintainer="Jelmer Vernooij",
      maintainer_email="jelmer@jelmer.uk",
      license="GNU GPL v2 or later",
      url="htps://github.com/jelmer/python-fastimport",
      packages=['fastimport', 'fastimport.tests', 'fastimport.processors'])
