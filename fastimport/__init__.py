# Copyright (C) 2008-2011 Canonical Ltd
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Fastimport file format parser and generator

This is a Python parser for git's fast-import format.  It was
originally developed for bzr-fastimport but has been extracted so
it can be used by other projects.  Use it like so:

   import fastimport.processor
   import fastimport.parser

   class ImportProcessor(fastimport.processor.ImportProcessor):
       ...

   parser = fastimport.parser.ImportParser(sys.stdin)
   processor = ImportProcessor(...)
   processor.process(parser.parse())
"""

__version__ = (0, 9, 14)
