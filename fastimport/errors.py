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

# ImportError is heavily based on BzrError

class ImportError(StandardError):
    """The base exception class for all import processing exceptions."""

    _fmt = "Unknown Import Error"

    def __init__(self, msg=None, **kwds):
        StandardError.__init__(self)
        if msg is not None:
            self._preformatted_string = msg
        else:
            self._preformatted_string = None
            for key, value in kwds.items():
                setattr(self, key, value)

    def _format(self):
        s = getattr(self, '_preformatted_string', None)
        if s is not None:
            # contains a preformatted message
            return s
        try:
            fmt = self._fmt
            if fmt:
                d = dict(self.__dict__)
                s = fmt % d
                # __str__() should always return a 'str' object
                # never a 'unicode' object.
                return s
        except (AttributeError, TypeError, NameError, ValueError, KeyError), e:
            return 'Unprintable exception %s: dict=%r, fmt=%r, error=%r' \
                % (self.__class__.__name__,
                   self.__dict__,
                   getattr(self, '_fmt', None),
                   e)

    def __unicode__(self):
        u = self._format()
        if isinstance(u, str):
            # Try decoding the str using the default encoding.
            u = unicode(u)
        elif not isinstance(u, unicode):
            # Try to make a unicode object from it, because __unicode__ must
            # return a unicode object.
            u = unicode(u)
        return u

    def __str__(self):
        s = self._format()
        if isinstance(s, unicode):
            s = s.encode('utf8')
        else:
            # __str__ must return a str.
            s = str(s)
        return s

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, str(self))

    def __eq__(self, other):
        if self.__class__ is not other.__class__:
            return NotImplemented
        return self.__dict__ == other.__dict__


class ParsingError(ImportError):
    """The base exception class for all import processing exceptions."""

    _fmt = _LOCATION_FMT + "Unknown Import Parsing Error"

    def __init__(self, lineno):
        ImportError.__init__(self)
        self.lineno = lineno


class MissingBytes(ParsingError):
    """Raised when EOF encountered while expecting to find more bytes."""

    _fmt = (_LOCATION_FMT + "Unexpected EOF - expected %(expected)d bytes,"
        " found %(found)d")

    def __init__(self, lineno, expected, found):
        ParsingError.__init__(self, lineno)
        self.expected = expected
        self.found = found


class MissingTerminator(ParsingError):
    """Raised when EOF encountered while expecting to find a terminator."""

    _fmt = (_LOCATION_FMT +
        "Unexpected EOF - expected '%(terminator)s' terminator")

    def __init__(self, lineno, terminator):
        ParsingError.__init__(self, lineno)
        self.terminator = terminator


class InvalidCommand(ParsingError):
    """Raised when an unknown command found."""

    _fmt = (_LOCATION_FMT + "Invalid command '%(cmd)s'")

    def __init__(self, lineno, cmd):
        ParsingError.__init__(self, lineno)
        self.cmd = cmd


class MissingSection(ParsingError):
    """Raised when a section is required in a command but not present."""

    _fmt = (_LOCATION_FMT + "Command %(cmd)s is missing section %(section)s")

    def __init__(self, lineno, cmd, section):
        ParsingError.__init__(self, lineno)
        self.cmd = cmd
        self.section = section


class BadFormat(ParsingError):
    """Raised when a section is formatted incorrectly."""

    _fmt = (_LOCATION_FMT + "Bad format for section %(section)s in "
        "command %(cmd)s: found '%(text)s'")

    def __init__(self, lineno, cmd, section, text):
        ParsingError.__init__(self, lineno)
        self.cmd = cmd
        self.section = section
        self.text = text


class InvalidTimezone(ParsingError):
    """Raised when converting a string timezone to a seconds offset."""

    _fmt = (_LOCATION_FMT +
        "Timezone %(timezone)r could not be converted.%(reason)s")

    def __init__(self, lineno, timezone, reason=None):
        ParsingError.__init__(self, lineno)
        self.timezone = timezone
        if reason:
            self.reason = ' ' + reason
        else:
            self.reason = ''


class PrematureEndOfStream(ParsingError):
    """Raised when the 'done' feature was specified but missing."""

    _fmt = (_LOCATION_FMT + "Stream end before 'done' command")

    def __init__(self, lineno):
        ParsingError.__init__(self, lineno)


class UnknownDateFormat(ImportError):
    """Raised when an unknown date format is given."""

    _fmt = ("Unknown date format '%(format)s'")

    def __init__(self, format):
        ImportError.__init__(self)
        self.format = format


class MissingHandler(ImportError):
    """Raised when a processor can't handle a command."""

    _fmt = ("Missing handler for command %(cmd)s")

    def __init__(self, cmd):
        ImportError.__init__(self)
        self.cmd = cmd


class UnknownParameter(ImportError):
    """Raised when an unknown parameter is passed to a processor."""

    _fmt = ("Unknown parameter - '%(param)s' not in %(knowns)s")

    def __init__(self, param, knowns):
        ImportError.__init__(self)
        self.param = param
        self.knowns = knowns


class BadRepositorySize(ImportError):
    """Raised when the repository has an incorrect number of revisions."""

    _fmt = ("Bad repository size - %(found)d revisions found, "
        "%(expected)d expected")

    def __init__(self, expected, found):
        ImportError.__init__(self)
        self.expected = expected
        self.found = found


class BadRestart(ImportError):
    """Raised when the import stream and id-map do not match up."""

    _fmt = ("Bad restart - attempted to skip commit %(commit_id)s "
        "but matching revision-id is unknown")

    def __init__(self, commit_id):
        ImportError.__init__(self)
        self.commit_id = commit_id


class UnknownFeature(ImportError):
    """Raised when an unknown feature is given in the input stream."""

    _fmt = ("Unknown feature '%(feature)s' - try a later importer or "
        "an earlier data format")

    def __init__(self, feature):
        ImportError.__init__(self)
        self.feature = feature
