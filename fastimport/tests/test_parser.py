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

"""Test the Import parsing"""
import io
import time
import unittest

from fastimport import (
    commands,
    errors,
    parser,
    )


class TestLineBasedParser(unittest.TestCase):

    def test_push_line(self):
        s = io.BytesIO(b"foo\nbar\nbaz\n")
        p = parser.LineBasedParser(s)
        self.assertEqual(b'foo', p.next_line())
        self.assertEqual(b'bar', p.next_line())
        p.push_line(b'bar')
        self.assertEqual(b'bar', p.next_line())
        self.assertEqual(b'baz', p.next_line())
        self.assertEqual(None, p.next_line())

    def test_read_bytes(self):
        s = io.BytesIO(b"foo\nbar\nbaz\n")
        p = parser.LineBasedParser(s)
        self.assertEqual(b'fo', p.read_bytes(2))
        self.assertEqual(b'o\nb', p.read_bytes(3))
        self.assertEqual(b'ar', p.next_line())
        # Test that the line buffer is ignored
        p.push_line(b'bar')
        self.assertEqual(b'baz', p.read_bytes(3))
        # Test missing bytes
        self.assertRaises(errors.MissingBytes, p.read_bytes, 10)

    def test_read_until(self):
        # TODO
        return
        s = io.BytesIO(b"foo\nbar\nbaz\nabc\ndef\nghi\n")
        p = parser.LineBasedParser(s)
        self.assertEqual(b'foo\nbar', p.read_until(b'baz'))
        self.assertEqual(b'abc', p.next_line())
        # Test that the line buffer is ignored
        p.push_line(b'abc')
        self.assertEqual(b'def', p.read_until(b'ghi'))
        # Test missing terminator
        self.assertRaises(errors.MissingTerminator, p.read_until(b'>>>'))


# Sample text
_sample_import_text = b"""
progress completed
# Test blob formats
blob
mark :1
data 4
aaaablob
data 5
bbbbb
# Commit formats
commit refs/heads/master
mark :2
committer bugs bunny <bugs@bunny.org> now
data 14
initial import
M 644 inline README
data 18
Welcome from bugs
commit refs/heads/master
committer <bugs@bunny.org> now
data 13
second commit
from :2
M 644 inline README
data 23
Welcome from bugs, etc.
# Miscellaneous
checkpoint
progress completed
# Test a commit without sub-commands (bug #351717)
commit refs/heads/master
mark :3
author <bugs@bunny.org> now
committer <bugs@bunny.org> now
data 20
first commit, empty
# Test a commit with a heredoc-style (delimited_data) messsage (bug #400960)
commit refs/heads/master
mark :4
author <bugs@bunny.org> now
committer <bugs@bunny.org> now
data <<EOF
Commit with heredoc-style message
EOF
# Test a "submodule"/tree-reference
commit refs/heads/master
mark :5
author <bugs@bunny.org> now
committer <bugs@bunny.org> now
data 15
submodule test
M 160000 rev-id tree-id
# Test features
feature whatever
feature foo=bar
# Test commit with properties
commit refs/heads/master
mark :6
committer <bugs@bunny.org> now
data 18
test of properties
property p1
property p2 5 hohum
property p3 16 alpha
beta
gamma
property p4 8 whatever
# Test a commit with multiple authors
commit refs/heads/master
mark :7
author Fluffy <fluffy@bunny.org> now
author Daffy <daffy@duck.org> now
author Donald <donald@duck.org> now
committer <bugs@bunny.org> now
data 17
multi-author test
"""

_timefunc = time.time


class TestImportParser(unittest.TestCase):

    def setUp(self):
        self.fake_time = 42.0123
        time.time = lambda: self.fake_time

    def tearDown(self):
        time.time = _timefunc
        del self.fake_time

    def test_iter_commands(self):
        s = io.BytesIO(_sample_import_text)
        p = parser.ImportParser(s)
        result = []
        for cmd in p.iter_commands():
            result.append(cmd)
            if cmd.name == b'commit':
                for fc in cmd.iter_files():
                    result.append(fc)

        self.assertEqual(len(result), 17)
        cmd1 = result.pop(0)
        self.assertEqual(b'progress', cmd1.name)
        self.assertEqual(b'completed', cmd1.message)
        cmd2 = result.pop(0)
        self.assertEqual(b'blob', cmd2.name)
        self.assertEqual(b'1', cmd2.mark)
        self.assertEqual(b':1', cmd2.id)
        self.assertEqual(b'aaaa', cmd2.data)
        self.assertEqual(4, cmd2.lineno)
        cmd3 = result.pop(0)
        self.assertEqual(b'blob', cmd3.name)
        self.assertEqual(b'@7', cmd3.id)
        self.assertEqual(None, cmd3.mark)
        self.assertEqual(b'bbbbb', cmd3.data)
        self.assertEqual(7, cmd3.lineno)
        cmd4 = result.pop(0)
        self.assertEqual(b'commit', cmd4.name)
        self.assertEqual(b'2', cmd4.mark)
        self.assertEqual(b':2', cmd4.id)
        self.assertEqual(
            b'initial import', cmd4.message)

        self.assertEqual(
            (b'bugs bunny', b'bugs@bunny.org', self.fake_time, 0),
            cmd4.committer)
        # namedtuple attributes
        self.assertEqual(b'bugs bunny', cmd4.committer.name)
        self.assertEqual(b'bugs@bunny.org', cmd4.committer.email)
        self.assertEqual(self.fake_time, cmd4.committer.timestamp)
        self.assertEqual(0, cmd4.committer.timezone)

        self.assertEqual(None, cmd4.author)
        self.assertEqual(11, cmd4.lineno)
        self.assertEqual(b'refs/heads/master', cmd4.ref)
        self.assertEqual(None, cmd4.from_)
        self.assertEqual([], cmd4.merges)
        file_cmd1 = result.pop(0)
        self.assertEqual(b'filemodify', file_cmd1.name)
        self.assertEqual(b'README', file_cmd1.path)
        self.assertEqual(0o100644, file_cmd1.mode)
        self.assertEqual(b'Welcome from bugs\n', file_cmd1.data)
        cmd5 = result.pop(0)
        self.assertEqual(b'commit', cmd5.name)
        self.assertEqual(None, cmd5.mark)
        self.assertEqual(b'@19', cmd5.id)
        self.assertEqual(b'second commit', cmd5.message)
        self.assertEqual(
            (b'', b'bugs@bunny.org', self.fake_time, 0), cmd5.committer)
        self.assertEqual(None, cmd5.author)
        self.assertEqual(19, cmd5.lineno)
        self.assertEqual(b'refs/heads/master', cmd5.ref)
        self.assertEqual(b':2', cmd5.from_)
        self.assertEqual([], cmd5.merges)
        file_cmd2 = result.pop(0)
        self.assertEqual(b'filemodify', file_cmd2.name)
        self.assertEqual(b'README', file_cmd2.path)
        self.assertEqual(0o100644, file_cmd2.mode)
        self.assertEqual(b'Welcome from bugs, etc.', file_cmd2.data)
        cmd6 = result.pop(0)
        self.assertEqual(cmd6.name, b'checkpoint')
        cmd7 = result.pop(0)
        self.assertEqual(b'progress', cmd7.name)
        self.assertEqual(b'completed', cmd7.message)
        cmd = result.pop(0)
        self.assertEqual(b'commit', cmd.name)
        self.assertEqual(b'3', cmd.mark)
        self.assertEqual(None, cmd.from_)
        cmd = result.pop(0)
        self.assertEqual(b'commit', cmd.name)
        self.assertEqual(b'4', cmd.mark)
        self.assertEqual(b'Commit with heredoc-style message\n', cmd.message)
        cmd = result.pop(0)
        self.assertEqual(b'commit', cmd.name)
        self.assertEqual(b'5', cmd.mark)
        self.assertEqual(b'submodule test\n', cmd.message)
        file_cmd1 = result.pop(0)
        self.assertEqual(b'filemodify', file_cmd1.name)
        self.assertEqual(b'tree-id', file_cmd1.path)
        self.assertEqual(0o160000, file_cmd1.mode)
        self.assertEqual(b"rev-id", file_cmd1.dataref)
        cmd = result.pop(0)
        self.assertEqual(b'feature', cmd.name)
        self.assertEqual(b'whatever', cmd.feature_name)
        self.assertEqual(None, cmd.value)
        cmd = result.pop(0)
        self.assertEqual(b'feature', cmd.name)
        self.assertEqual(b'foo', cmd.feature_name)
        self.assertEqual(b'bar', cmd.value)
        cmd = result.pop(0)
        self.assertEqual(b'commit', cmd.name)
        self.assertEqual(b'6', cmd.mark)
        self.assertEqual(b'test of properties', cmd.message)
        self.assertEqual({
            b'p1': None,
            b'p2': b'hohum',
            b'p3': b'alpha\nbeta\ngamma',
            b'p4': b'whatever',
        }, cmd.properties)
        cmd = result.pop(0)
        self.assertEqual(b'commit', cmd.name)
        self.assertEqual(b'7', cmd.mark)
        self.assertEqual(b'multi-author test', cmd.message)
        self.assertEqual(b'', cmd.committer[0])
        self.assertEqual(b'bugs@bunny.org', cmd.committer[1])
        self.assertEqual(b'Fluffy', cmd.author[0])
        self.assertEqual(b'fluffy@bunny.org', cmd.author[1])
        self.assertEqual(b'Daffy', cmd.more_authors[0][0])
        self.assertEqual(b'daffy@duck.org', cmd.more_authors[0][1])
        self.assertEqual(b'Donald', cmd.more_authors[1][0])
        self.assertEqual(b'donald@duck.org', cmd.more_authors[1][1])

    def test_done_feature_missing_done(self):
        s = io.BytesIO(b"""feature done
""")
        p = parser.ImportParser(s)
        cmds = p.iter_commands()
        self.assertEqual(b"feature", next(cmds).name)
        self.assertRaises(errors.PrematureEndOfStream, lambda: next(cmds))

    def test_done_with_feature(self):
        s = io.BytesIO(b"""feature done
done
more data
""")
        p = parser.ImportParser(s)
        cmds = p.iter_commands()
        self.assertEqual(b"feature", next(cmds).name)
        self.assertRaises(StopIteration, lambda: next(cmds))

    def test_done_without_feature(self):
        s = io.BytesIO(b"""done
more data
""")
        p = parser.ImportParser(s)
        cmds = p.iter_commands()
        self.assertEqual([], list(cmds))


class TestStringParsing(unittest.TestCase):

    def test_unquote(self):
        s = br'hello \"sweet\" wo\\r\tld'
        self.assertEqual(
            br'hello "sweet" wo\r' + b'\tld',
            parser._unquote_c_string(s))


class TestPathPairParsing(unittest.TestCase):

    def test_path_pair_simple(self):
        p = parser.ImportParser(b'')
        self.assertEqual([b'foo', b'bar'], p._path_pair(b'foo bar'))

    def test_path_pair_spaces_in_first(self):
        p = parser.ImportParser("")
        self.assertEqual(
            [b'foo bar', b'baz'],
            p._path_pair(b'"foo bar" baz'))


class TestTagParsing(unittest.TestCase):

    def test_tagger_with_email(self):
        p = parser.ImportParser(io.BytesIO(
            b"tag refs/tags/v1.0\n"
            b"from :xxx\n"
            b"tagger Joe Wong <joe@example.com> 1234567890 -0600\n"
            b"data 11\n"
            b"create v1.0"))
        cmds = list(p.iter_commands())
        self.assertEqual(1, len(cmds))
        self.assertTrue(isinstance(cmds[0], commands.TagCommand))
        self.assertEqual(
            cmds[0].tagger,
            (b'Joe Wong', b'joe@example.com', 1234567890.0, -21600))

    def test_tagger_no_email_strict(self):
        p = parser.ImportParser(io.BytesIO(
            b"tag refs/tags/v1.0\n"
            b"from :xxx\n"
            b"tagger Joe Wong\n"
            b"data 11\n"
            b"create v1.0"))
        self.assertRaises(errors.BadFormat, list, p.iter_commands())

    def test_tagger_no_email_not_strict(self):
        p = parser.ImportParser(io.BytesIO(
            b"tag refs/tags/v1.0\n"
            b"from :xxx\n"
            b"tagger Joe Wong\n"
            b"data 11\n"
            b"create v1.0"), strict=False)
        cmds = list(p.iter_commands())
        self.assertEqual(1, len(cmds))
        self.assertTrue(isinstance(cmds[0], commands.TagCommand))
        self.assertEqual(cmds[0].tagger[:2], (b'Joe Wong', None))
