#!/usr/bin/env python
from distutils.core import setup

version = "0.9.8"

setup(version=version,
      packages=['fastimport', 'fastimport.tests', 'fastimport.processors'],
      scripts=[
          'bin/fast-import-query',
          'bin/fast-import-filter',
          'bin/fast-import-info',
      ],
      )
