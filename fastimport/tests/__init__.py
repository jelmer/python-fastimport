# __init__.py -- The tests for python-fastimport
# Copyright (C) 2010 Canonical, Ltd.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License or (at your option) any later version of
# the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Tests for fastimport."""

import unittest


def test_suite():
    names = [
        'test_commands',
        'test_dates',
        'test_errors',
        'test_filter_processor',
        'test_info_processor',
        'test_helpers',
        'test_parser',
        ]
    module_names = ['fastimport.tests.' + name for name in names]
    result = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(module_names)
    result.addTests(suite)

    return result
