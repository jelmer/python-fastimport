# Copyright (C) 2008 Canonical Ltd
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

"""Date parsing routines.

Each routine represents a date format that can be specified in a
stream using the date-format feature.  The return value is
timestamp,timezone where

* timestamp is seconds since epoch
* timezone is the offset from UTC in seconds.
"""
import time

from . import errors


def parse_raw(s, lineno=0):
    """Parse a date from a raw string.

    The format must be exactly "seconds-since-epoch offset-utc".
    See the spec for details.
    """
    timestamp_str, timezone_str = s.split(b' ', 1)
    timestamp = float(timestamp_str)
    try:
        timezone = parse_tz(timezone_str)
    except ValueError:
        raise errors.InvalidTimezone(lineno, timezone_str)
    return timestamp, timezone


def parse_tz(tz):
    """Parse a timezone specification in the [+|-]HHMM format.

    :return: the timezone offset in seconds.
    """
    # from git_repository.py in bzr-git
    sign_byte = tz[0:1]
    # in python 3 b'+006'[0] would return an integer,
    # but b'+006'[0:1] return a new bytes string.
    if sign_byte not in (b'+', b'-'):
        raise ValueError(tz)

    sign = {b'+': +1, b'-': -1}[sign_byte]
    hours = int(tz[1:-2])
    minutes = int(tz[-2:])

    return sign * 60 * (60 * hours + minutes)


def parse_rfc2822(s, lineno=0):
    """Parse a date from a rfc2822 string.

    See the spec for details.
    """
    raise NotImplementedError(parse_rfc2822)


def parse_now(s, lineno=0):
    """Parse a date from a string.

    The format must be exactly "now".
    See the spec for details.
    """
    return time.time(), 0


# Lookup tabel of date parsing routines
DATE_PARSERS_BY_NAME = {
    u'raw':      parse_raw,
    u'rfc2822':  parse_rfc2822,
    u'now':      parse_now,
    }
