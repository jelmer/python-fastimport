# Copyright (C) 2009 Canonical Ltd
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

"""Test the helper functions."""

import unittest

from fastimport import (
    helpers,
    )


class TestCommonDirectory(unittest.TestCase):

    def test_no_paths(self):
        c = helpers.common_directory(None)
        self.assertEqual(c, None)
        c = helpers.common_directory([])
        self.assertEqual(c, None)

    def test_one_path(self):
        c = helpers.common_directory([b'foo'])
        self.assertEqual(c, b'')
        c = helpers.common_directory([b'foo/'])
        self.assertEqual(c, b'foo/')
        c = helpers.common_directory([b'foo/bar'])
        self.assertEqual(c, b'foo/')

    def test_two_paths(self):
        c = helpers.common_directory([b'foo', b'bar'])
        self.assertEqual(c, b'')
        c = helpers.common_directory([b'foo/', b'bar'])
        self.assertEqual(c, b'')
        c = helpers.common_directory([b'foo/', b'foo/bar'])
        self.assertEqual(c, b'foo/')
        c = helpers.common_directory([b'foo/bar/x', b'foo/bar/y'])
        self.assertEqual(c, b'foo/bar/')
        c = helpers.common_directory([b'foo/bar/aa_x', b'foo/bar/aa_y'])
        self.assertEqual(c, b'foo/bar/')

    def test_lots_of_paths(self):
        c = helpers.common_directory(
            [b'foo/bar/x', b'foo/bar/y', b'foo/bar/z'])
        self.assertEqual(c, b'foo/bar/')
