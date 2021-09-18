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

"""fast-import command classes.

These objects are used by the parser to represent the content of
a fast-import stream.
"""
from __future__ import division

import re
import stat

from .helpers import (
    newobject as object,
    utf8_bytes_string,
    )


# There is a bug in git 1.5.4.3 and older by which unquoting a string consumes
# one extra character. Set this variable to True to work-around it. It only
# happens when renaming a file whose name contains spaces and/or quotes, and
# the symptom is:
#   % git-fast-import
#   fatal: Missing space after source: R "file 1.txt" file 2.txt
# http://git.kernel.org/?p=git/git.git;a=commit;h=c8744d6a8b27115503565041566d97c21e722584
GIT_FAST_IMPORT_NEEDS_EXTRA_SPACE_AFTER_QUOTE = False


# Lists of command names
COMMAND_NAMES = [b'blob', b'checkpoint', b'commit', b'feature', b'progress',
                 b'reset', b'tag']
FILE_COMMAND_NAMES = [b'filemodify', b'filedelete', b'filecopy', b'filerename',
                      b'filedeleteall']

# Feature names
MULTIPLE_AUTHORS_FEATURE = b'multiple-authors'
COMMIT_PROPERTIES_FEATURE = b'commit-properties'
EMPTY_DIRS_FEATURE = b'empty-directories'
FEATURE_NAMES = [
    MULTIPLE_AUTHORS_FEATURE,
    COMMIT_PROPERTIES_FEATURE,
    EMPTY_DIRS_FEATURE,
    ]


class ImportCommand(object):
    """Base class for import commands."""

    def __init__(self, name):
        self.name = name
        # List of field names not to display
        self._binary = []

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return bytes(self).decode('utf8')

    def __bytes__(self):
        raise NotImplementedError(
            'An implementation of __bytes__ is required'
        )

    def dump_str(self, names=None, child_lists=None, verbose=False):
        """Dump fields as a string.

        For debugging.

        :param names: the list of fields to include or
            None for all public fields
        :param child_lists: dictionary of child command names to
            fields for that child command to include
        :param verbose: if True, prefix each line with the command class and
            display fields as a dictionary; if False, dump just the field
            values with tabs between them
        """
        interesting = {}
        if names is None:
            fields = [
                k for k in list(self.__dict__.keys())
                if not k.startswith(b'_')
            ]
        else:
            fields = names
        for field in fields:
            value = self.__dict__.get(field)
            if field in self._binary and value is not None:
                value = b'(...)'
            interesting[field] = value
        if verbose:
            return "%s: %s" % (self.__class__.__name__, interesting)
        else:
            return "\t".join([repr(interesting[k]) for k in fields])


class BlobCommand(ImportCommand):

    def __init__(self, mark, data, lineno=0):
        ImportCommand.__init__(self, b'blob')
        self.mark = mark
        self.data = data
        self.lineno = lineno
        # Provide a unique id in case the mark is missing
        if mark is None:
            self.id = b'@' + ("%d" % lineno).encode('utf-8')
        else:
            self.id = b':' + mark
        self._binary = [b'data']

    def __bytes__(self):
        if self.mark is None:
            mark_line = b''
        else:
            mark_line = b"\nmark :" + self.mark
        return (b'blob' + mark_line + b'\n' +
                ('data %d\n' % len(self.data)).encode('utf-8') + self.data)


class CheckpointCommand(ImportCommand):

    def __init__(self):
        ImportCommand.__init__(self, b'checkpoint')

    def __bytes__(self):
        return b'checkpoint'


class CommitCommand(ImportCommand):

    def __init__(self, ref, mark, author, committer, message, from_,
                 merges, file_iter, lineno=0, more_authors=None,
                 properties=None):
        ImportCommand.__init__(self, b'commit')
        self.ref = ref
        self.mark = mark
        self.author = author
        self.committer = committer
        self.message = message
        self.from_ = from_
        self.merges = merges
        self.file_iter = file_iter
        self.more_authors = more_authors
        self.properties = properties
        self.lineno = lineno
        self._binary = [b'file_iter']
        # Provide a unique id in case the mark is missing
        if self.mark is None:
            self.id = b'@' + ('%d' % lineno).encode('utf-8')
        else:
            if isinstance(self.mark, (int)):
                self.id = b':' + str(self.mark).encode('utf-8')
            else:
                self.id = b':' + self.mark

    def copy(self, **kwargs):
        if not isinstance(self.file_iter, list):
            self.file_iter = list(self.file_iter)

        fields = dict(
            (key, value)
            for key, value in self.__dict__.items()
            if key not in ('id', 'name')
            if not key.startswith('_')
        )

        fields.update(kwargs)

        return CommitCommand(**fields)

    def __bytes__(self):
        return self.to_string(include_file_contents=True)

    def to_string(self, use_features=True, include_file_contents=False):
        """
            @todo the name to_string is ambiguous since the method actually
                returns bytes.
        """
        if self.mark is None:
            mark_line = b''
        else:
            if isinstance(self.mark, (int)):
                mark_line = b'\nmark :' + str(self.mark).encode('utf-8')
            else:
                mark_line = b'\nmark :' + self.mark

        if self.author is None:
            author_section = b''
        else:
            author_section = b'\nauthor ' + format_who_when(self.author)
            if use_features and self.more_authors:
                for author in self.more_authors:
                    author_section += b'\nauthor ' + format_who_when(author)

        committer = b'committer ' + format_who_when(self.committer)

        if self.message is None:
            msg_section = b''
        else:
            msg = self.message
            msg_section = ('\ndata %d\n' % len(msg)).encode('ascii') + msg
        if self.from_ is None:
            from_line = b''
        else:
            from_line = b'\nfrom ' + self.from_
        if self.merges is None:
            merge_lines = b''
        else:
            merge_lines = b''.join(
                [b'\nmerge ' + m for m in self.merges])
        if use_features and self.properties:
            property_lines = []
            for name in sorted(self.properties):
                value = self.properties[name]
                property_lines.append(b'\n' + format_property(name, value))
            properties_section = b''.join(property_lines)
        else:
            properties_section = b''
        if self.file_iter is None:
            filecommands = b''
        else:
            if include_file_contents:
                filecommands = b''.join(
                    [b'\n' + bytes(c) for c in self.iter_files()])
            else:
                filecommands = b''.join(
                    [b'\n' + str(c) for c in self.iter_files()])
        return b''.join([
            b'commit ',
            self.ref,
            mark_line,
            author_section + b'\n',
            committer,
            msg_section,
            from_line,
            merge_lines,
            properties_section,
            filecommands])

    def dump_str(self, names=None, child_lists=None, verbose=False):
        result = [ImportCommand.dump_str(self, names, verbose=verbose)]
        for f in self.iter_files():
            if child_lists is None:
                continue
            try:
                child_names = child_lists[f.name]
            except KeyError:
                continue
            result.append('\t%s' % f.dump_str(child_names, verbose=verbose))
        return '\n'.join(result)

    def iter_files(self):
        """Iterate over files."""
        # file_iter may be a callable or an iterator
        if callable(self.file_iter):
            return self.file_iter()
        return iter(self.file_iter)


class FeatureCommand(ImportCommand):

    def __init__(self, feature_name, value=None, lineno=0):
        ImportCommand.__init__(self, b'feature')
        self.feature_name = feature_name
        self.value = value
        self.lineno = lineno

    def __bytes__(self):
        if self.value is None:
            value_text = b''
        else:
            value_text = b'=' + self.value
        return b'feature ' + self.feature_name + value_text


class ProgressCommand(ImportCommand):

    def __init__(self, message):
        ImportCommand.__init__(self, b'progress')
        self.message = message

    def __bytes__(self):
        return b'progress ' + self.message


class ResetCommand(ImportCommand):

    def __init__(self, ref, from_):
        ImportCommand.__init__(self, b'reset')
        self.ref = ref
        self.from_ = from_

    def __bytes__(self):
        if self.from_ is None:
            from_line = b''
        else:
            # According to git-fast-import(1), the extra LF is optional here;
            # however, versions of git up to 1.5.4.3 had a bug by which the LF
            # was needed. Always emit it, since it doesn't hurt and maintains
            # compatibility with older versions.
            # http://git.kernel.org/?p=git/git.git;a=commit;h=655e8515f279c01f525745d443f509f97cd805ab
            from_line = b'\nfrom ' + self.from_ + b'\n'
        return b'reset ' + self.ref + from_line


class TagCommand(ImportCommand):

    def __init__(self, id, from_, tagger, message):
        ImportCommand.__init__(self, b'tag')
        self.id = id
        self.from_ = from_
        self.tagger = tagger
        self.message = message

    def __bytes__(self):
        if self.from_ is None:
            from_line = b''
        else:
            from_line = b'\nfrom ' + self.from_
        if self.tagger is None:
            tagger_line = b''
        else:
            tagger_line = b'\ntagger ' + format_who_when(self.tagger)
        if self.message is None:
            msg_section = b''
        else:
            msg = self.message
            msg_section = ('\ndata %d\n' % len(msg)).encode('ascii') + msg
        return b'tag ' + self.id + from_line + tagger_line + msg_section


class FileCommand(ImportCommand):
    """Base class for file commands."""
    pass


class FileModifyCommand(FileCommand):

    def __init__(self, path, mode, dataref, data):
        # Either dataref or data should be null
        FileCommand.__init__(self, b'filemodify')
        self.path = check_path(path)
        self.mode = mode
        self.dataref = dataref
        self.data = data
        self._binary = [b'data']

    def __bytes__(self):
        return self.to_string(include_file_contents=True)

    def __str__(self):
        return self.to_string(include_file_contents=False)

    def _format_mode(self, mode):
        if mode in (0o755, 0o100755):
            return b'755'
        elif mode in (0o644, 0o100644):
            return b'644'
        elif mode == 0o40000:
            return b'040000'
        elif mode == 0o120000:
            return b'120000'
        elif mode == 0o160000:
            return b'160000'
        else:
            raise AssertionError('Unknown mode %o' % mode)

    def to_string(self, include_file_contents=False):
        datastr = b''
        if stat.S_ISDIR(self.mode):
            dataref = b'-'
        elif self.dataref is None:
            dataref = b'inline'
            if include_file_contents:
                datastr = (
                    ('\ndata %d\n' % len(self.data)).encode('ascii') +
                    self.data)
        else:
            dataref = self.dataref
        path = format_path(self.path)

        return b' '.join(
            [b'M', self._format_mode(self.mode), dataref, path + datastr])


class FileDeleteCommand(FileCommand):

    def __init__(self, path):
        FileCommand.__init__(self, b'filedelete')
        self.path = check_path(path)

    def __bytes__(self):
        return b' '.join([b'D', format_path(self.path)])


class FileCopyCommand(FileCommand):

    def __init__(self, src_path, dest_path):
        FileCommand.__init__(self, b'filecopy')
        self.src_path = check_path(src_path)
        self.dest_path = check_path(dest_path)

    def __bytes__(self):
        return b' '.join(
            [b'C', format_path(self.src_path, quote_spaces=True),
             format_path(self.dest_path)])


class FileRenameCommand(FileCommand):

    def __init__(self, old_path, new_path):
        FileCommand.__init__(self, b'filerename')
        self.old_path = check_path(old_path)
        self.new_path = check_path(new_path)

    def __bytes__(self):
        return b' '.join([
            b'R',
            format_path(self.old_path, quote_spaces=True),
            format_path(self.new_path)]
        )


class FileDeleteAllCommand(FileCommand):

    def __init__(self):
        FileCommand.__init__(self, b'filedeleteall')

    def __bytes__(self):
        return b'deleteall'


class NoteModifyCommand(FileCommand):

    def __init__(self, from_, data):
        super(NoteModifyCommand, self).__init__(b'notemodify')
        self.from_ = from_
        self.data = data
        self._binary = ['data']

    def __bytes__(self):
        return (b'N inline :' + self.from_ +
                ('\ndata %d\n' % len(self.data)).encode('ascii') + self.data)


def check_path(path):
    """Check that a path is legal.

    :return: the path if all is OK
    :raise ValueError: if the path is illegal
    """
    if path is None or path == b'' or path.startswith(b'/'):
        raise ValueError("illegal path '%s'" % path)

    if not isinstance(path, bytes):
        raise TypeError("illegal type for path '%r'" % path)

    return path


def format_path(p, quote_spaces=False):
    """Format a path in utf8, quoting it if necessary."""
    if b'\n' in p:
        p = re.sub(b'\n', b'\\n', p)
        quote = True
    else:
        quote = p[0] == b'"' or (quote_spaces and b' ' in p)
    if quote:
        extra = GIT_FAST_IMPORT_NEEDS_EXTRA_SPACE_AFTER_QUOTE and b' ' or b''
        p = b'"' + p + b'"' + extra
    return p


def format_who_when(fields):
    """Format tuple of name,email,secs-since-epoch,utc-offset-secs as bytes."""
    offset = fields[3]
    if offset < 0:
        offset_sign = b'-'
        offset = abs(offset)
    else:
        offset_sign = b'+'
    offset_hours = offset // 3600
    offset_minutes = offset // 60 - offset_hours * 60
    offset_str = (
        offset_sign +
        ('%02d%02d' % (offset_hours, offset_minutes)).encode('ascii'))
    name = fields[0]

    if name == b'':
        sep = b''
    else:
        sep = b' '

    name = utf8_bytes_string(name)

    email = fields[1]

    email = utf8_bytes_string(email)

    return b''.join(
        (name, sep, b'<', email, b'> ',
         ("%d" % fields[2]).encode('ascii'), b' ', offset_str))


def format_property(name, value):
    """Format the name and value (both unicode) of a property as a string."""
    result = b''
    utf8_name = utf8_bytes_string(name)

    result = b'property ' + utf8_name
    if value is not None:
        utf8_value = utf8_bytes_string(value)
        result += (b' ' + ('%d' % len(utf8_value)).encode('ascii') +
                   b' ' + utf8_value)

    return result
