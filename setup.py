#!/usr/bin/env python
from distutils.core import setup

version = "0.9.7"

setup(name="fastimport",
      description="VCS fastimport/fastexport parser",
      version=version,
      author="Canonical Ltd",
      author_email="bazaar@lists.canonical.com",
      maintainer="Jelmer Vernooij",
      maintainer_email="jelmer@jelmer.uk",
      license="GNU GPL v2 or later",
      url="https://github.com/jelmer/python-fastimport",
      packages=['fastimport', 'fastimport.tests', 'fastimport.processors'],
      scripts=[
          'bin/fast-import-query',
          'bin/fast-import-filter',
          'bin/fast-import-info',
      ],
      classifiers=[
          'Development Status :: 4 - Beta',
          'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: Implementation :: CPython',
          'Programming Language :: Python :: Implementation :: PyPy',
          'Operating System :: POSIX',
          'Topic :: Software Development :: Version Control',
      ],
      )
