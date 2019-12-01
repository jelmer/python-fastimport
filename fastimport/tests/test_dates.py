# Copyright (C) 2012 Canonical Ltd
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

"""Test parsing of dates."""

from unittest import TestCase

from fastimport import (
    dates,
    )


class ParseTzTests(TestCase):

    def test_parse_tz_utc(self):
        self.assertEqual(0, dates.parse_tz(b'+0000'))
        self.assertEqual(0, dates.parse_tz(b'-0000'))

    def test_parse_tz_cet(self):
        self.assertEqual(3600, dates.parse_tz(b'+0100'))

    def test_parse_tz_odd(self):
        self.assertEqual(1864800, dates.parse_tz(b'+51800'))
