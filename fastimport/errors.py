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

"""Exception classes for fastimport"""

# Prefix to messages to show location information
_LOCATION_FMT = "line %(lineno)d: "


class ImportError(Exception):
    """The base exception class for all import processing exceptions."""

    def __init__(self):
        super(ImportError, self).__init__(self._fmt % self.__dict__)


class ParsingError(ImportError):
    """The base exception class for all import processing exceptions."""

    _fmt = _LOCATION_FMT + "Unknown Import Parsing Error"

    def __init__(self, lineno):
        self.lineno = lineno
        ImportError.__init__(self)


class MissingBytes(ParsingError):
    """Raised when EOF encountered while expecting to find more bytes."""

    _fmt = (_LOCATION_FMT + "Unexpected EOF - expected %(expected)d bytes,"
            " found %(found)d")

    def __init__(self, lineno, expected, found):
        self.expected = expected
        self.found = found
        ParsingError.__init__(self, lineno)


class MissingTerminator(ParsingError):
    """Raised when EOF encountered while expecting to find a terminator."""

    _fmt = (_LOCATION_FMT +
            "Unexpected EOF - expected '%(terminator)s' terminator")

    def __init__(self, lineno, terminator):
        self.terminator = terminator
        ParsingError.__init__(self, lineno)


class InvalidCommand(ParsingError):
    """Raised when an unknown command found."""

    _fmt = (_LOCATION_FMT + "Invalid command '%(cmd)s'")

    def __init__(self, lineno, cmd):
        self.cmd = cmd
        ParsingError.__init__(self, lineno)


class MissingSection(ParsingError):
    """Raised when a section is required in a command but not present."""

    _fmt = (_LOCATION_FMT + "Command %(cmd)s is missing section %(section)s")

    def __init__(self, lineno, cmd, section):
        self.cmd = cmd
        self.section = section
        ParsingError.__init__(self, lineno)


class BadFormat(ParsingError):
    """Raised when a section is formatted incorrectly."""

    _fmt = (_LOCATION_FMT + "Bad format for section %(section)s in "
            "command %(cmd)s: found '%(text)s'")

    def __init__(self, lineno, cmd, section, text):
        self.cmd = cmd
        self.section = section
        self.text = text
        ParsingError.__init__(self, lineno)


class InvalidTimezone(ParsingError):
    """Raised when converting a string timezone to a seconds offset."""

    _fmt = (_LOCATION_FMT +
            "Timezone %(timezone)r could not be converted.%(reason)s")

    def __init__(self, lineno, timezone, reason=None):
        self.timezone = timezone
        if reason:
            self.reason = ' ' + reason
        else:
            self.reason = ''
        ParsingError.__init__(self, lineno)


class PrematureEndOfStream(ParsingError):
    """Raised when the 'done' feature was specified but missing."""

    _fmt = (_LOCATION_FMT + "Stream end before 'done' command")

    def __init__(self, lineno):
        ParsingError.__init__(self, lineno)


class UnknownDateFormat(ImportError):
    """Raised when an unknown date format is given."""

    _fmt = ("Unknown date format '%(format)s'")

    def __init__(self, format):
        self.format = format
        ImportError.__init__(self)


class MissingHandler(ImportError):
    """Raised when a processor can't handle a command."""

    _fmt = ("Missing handler for command %(cmd)s")

    def __init__(self, cmd):
        self.cmd = cmd
        ImportError.__init__(self)


class UnknownParameter(ImportError):
    """Raised when an unknown parameter is passed to a processor."""

    _fmt = ("Unknown parameter - '%(param)s' not in %(knowns)s")

    def __init__(self, param, knowns):
        self.param = param
        self.knowns = knowns
        ImportError.__init__(self)


class BadRepositorySize(ImportError):
    """Raised when the repository has an incorrect number of revisions."""

    _fmt = ("Bad repository size - %(found)d revisions found, "
            "%(expected)d expected")

    def __init__(self, expected, found):
        self.expected = expected
        self.found = found
        ImportError.__init__(self)


class BadRestart(ImportError):
    """Raised when the import stream and id-map do not match up."""

    _fmt = ("Bad restart - attempted to skip commit %(commit_id)s "
            "but matching revision-id is unknown")

    def __init__(self, commit_id):
        self.commit_id = commit_id
        ImportError.__init__(self)


class UnknownFeature(ImportError):
    """Raised when an unknown feature is given in the input stream."""

    _fmt = ("Unknown feature '%(feature)s' - try a later importer or "
            "an earlier data format")

    def __init__(self, feature):
        self.feature = feature
        ImportError.__init__(self)
