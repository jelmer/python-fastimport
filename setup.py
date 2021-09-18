#!/usr/bin/env python
from setuptools import setup

version = "0.9.14"

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
      test_suite="fastimport.tests.test_suite",
      python_requires=">=3.5",
      scripts=[
          'bin/fast-import-query',
          'bin/fast-import-filter',
          'bin/fast-import-info',
      ],
      classifiers=[
          'Development Status :: 4 - Beta',
          'License :: OSI Approved :: GNU General Public License v2 '
          'or later (GPLv2+)',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: Implementation :: CPython',
          'Programming Language :: Python :: Implementation :: PyPy',
          'Operating System :: POSIX',
          'Topic :: Software Development :: Version Control',
      ],
      )
