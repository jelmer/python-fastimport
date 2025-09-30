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
from typing import cast

from fastimport import (
    commands,
    errors,
    parser,
)


class TestLineBasedParser(unittest.TestCase):
    def test_push_line(self) -> None:
        s = io.BytesIO(b"foo\nbar\nbaz\n")
        p = parser.LineBasedParser(s)
        self.assertEqual(b"foo", p.next_line())
        self.assertEqual(b"bar", p.next_line())
        p.push_line(b"bar")
        self.assertEqual(b"bar", p.next_line())
        self.assertEqual(b"baz", p.next_line())
        self.assertEqual(None, p.next_line())

    def test_read_bytes(self) -> None:
        s = io.BytesIO(b"foo\nbar\nbaz\n")
        p = parser.LineBasedParser(s)
        self.assertEqual(b"fo", p.read_bytes(2))
        self.assertEqual(b"o\nb", p.read_bytes(3))
        self.assertEqual(b"ar", p.next_line())
        # Test that the line buffer is ignored
        p.push_line(b"bar")
        self.assertEqual(b"baz", p.read_bytes(3))
        # Test missing bytes
        self.assertRaises(errors.MissingBytes, p.read_bytes, 10)

    def test_read_until(self) -> None:
        # TODO
        return
        s = io.BytesIO(b"foo\nbar\nbaz\nabc\ndef\nghi\n")
        p = parser.LineBasedParser(s)
        self.assertEqual(b"foo\nbar", p.read_until(b"baz"))
        self.assertEqual(b"abc", p.next_line())
        # Test that the line buffer is ignored
        p.push_line(b"abc")
        self.assertEqual(b"def", p.read_until(b"ghi"))
        # Test missing terminator
        self.assertRaises(errors.MissingTerminator, p.read_until(b">>>"))


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
# Test a commit with a heredoc-style (delimited_data) message (bug #400960)
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
    def setUp(self) -> None:
        self.fake_time = 42.0123
        time.time = lambda: self.fake_time

    def tearDown(self) -> None:
        time.time = _timefunc
        del self.fake_time

    def test_iter_commands(self) -> None:
        s = io.BytesIO(_sample_import_text)
        p = parser.ImportParser(s)
        result = []
        for cmd in p.iter_commands():
            result.append(cmd)
            if cmd.name == b"commit":
                commit_cmd = cast(commands.CommitCommand, cmd)
                for fc in commit_cmd.iter_files():
                    result.append(fc)

        self.assertEqual(len(result), 17)
        cmd1 = result.pop(0)
        self.assertEqual(b"progress", cmd1.name)
        progress_cmd1 = cast(commands.ProgressCommand, cmd1)
        self.assertEqual(b"completed", progress_cmd1.message)
        cmd2 = result.pop(0)
        self.assertEqual(b"blob", cmd2.name)
        blob_cmd2 = cast(commands.BlobCommand, cmd2)
        self.assertEqual(b"1", blob_cmd2.mark)
        self.assertEqual(b":1", blob_cmd2.id)
        self.assertEqual(b"aaaa", blob_cmd2.data)
        self.assertEqual(4, blob_cmd2.lineno)
        cmd3 = result.pop(0)
        self.assertEqual(b"blob", cmd3.name)
        blob_cmd3 = cast(commands.BlobCommand, cmd3)
        self.assertEqual(b"@7", blob_cmd3.id)
        self.assertEqual(None, blob_cmd3.mark)
        self.assertEqual(b"bbbbb", blob_cmd3.data)
        self.assertEqual(7, blob_cmd3.lineno)
        cmd4 = result.pop(0)
        self.assertEqual(b"commit", cmd4.name)
        commit_cmd4 = cast(commands.CommitCommand, cmd4)
        self.assertEqual(b"2", commit_cmd4.mark)
        self.assertEqual(b":2", commit_cmd4.id)
        self.assertEqual(b"initial import", commit_cmd4.message)

        self.assertEqual(
            (b"bugs bunny", b"bugs@bunny.org", self.fake_time, 0), commit_cmd4.committer
        )
        # namedtuple attributes
        self.assertEqual(b"bugs bunny", commit_cmd4.committer.name)  # type: ignore[union-attr]
        self.assertEqual(b"bugs@bunny.org", commit_cmd4.committer.email)  # type: ignore[union-attr]
        self.assertEqual(self.fake_time, commit_cmd4.committer.timestamp)  # type: ignore[union-attr]
        self.assertEqual(0, commit_cmd4.committer.timezone)  # type: ignore[union-attr]

        self.assertEqual(None, commit_cmd4.author)
        self.assertEqual(11, commit_cmd4.lineno)
        self.assertEqual(b"refs/heads/master", commit_cmd4.ref)
        self.assertEqual(None, commit_cmd4.from_)
        self.assertEqual([], commit_cmd4.merges)
        file_cmd1 = result.pop(0)
        self.assertEqual(b"filemodify", file_cmd1.name)
        file_modify_cmd1 = cast(commands.FileModifyCommand, file_cmd1)
        self.assertEqual(b"README", file_modify_cmd1.path)
        self.assertEqual(0o100644, file_modify_cmd1.mode)
        self.assertEqual(b"Welcome from bugs\n", file_modify_cmd1.data)
        cmd5 = result.pop(0)
        self.assertEqual(b"commit", cmd5.name)
        commit_cmd5 = cast(commands.CommitCommand, cmd5)
        self.assertEqual(None, commit_cmd5.mark)
        self.assertEqual(b"@19", commit_cmd5.id)
        self.assertEqual(b"second commit", commit_cmd5.message)
        self.assertEqual(
            (b"", b"bugs@bunny.org", self.fake_time, 0), commit_cmd5.committer
        )
        self.assertEqual(None, commit_cmd5.author)
        self.assertEqual(19, commit_cmd5.lineno)
        self.assertEqual(b"refs/heads/master", commit_cmd5.ref)
        self.assertEqual(b":2", commit_cmd5.from_)
        self.assertEqual([], commit_cmd5.merges)
        file_cmd2 = result.pop(0)
        self.assertEqual(b"filemodify", file_cmd2.name)
        file_modify_cmd2 = cast(commands.FileModifyCommand, file_cmd2)
        self.assertEqual(b"README", file_modify_cmd2.path)
        self.assertEqual(0o100644, file_modify_cmd2.mode)
        self.assertEqual(b"Welcome from bugs, etc.", file_modify_cmd2.data)
        cmd6 = result.pop(0)
        self.assertEqual(cmd6.name, b"checkpoint")
        cmd7 = result.pop(0)
        self.assertEqual(b"progress", cmd7.name)
        progress_cmd7 = cast(commands.ProgressCommand, cmd7)
        self.assertEqual(b"completed", progress_cmd7.message)
        cmd = result.pop(0)
        self.assertEqual(b"commit", cmd.name)
        commit_cmd = cast(commands.CommitCommand, cmd)
        self.assertEqual(b"3", commit_cmd.mark)
        self.assertEqual(None, commit_cmd.from_)
        cmd = result.pop(0)
        self.assertEqual(b"commit", cmd.name)
        commit_cmd = cast(commands.CommitCommand, cmd)
        self.assertEqual(b"4", commit_cmd.mark)
        self.assertEqual(b"Commit with heredoc-style message\n", commit_cmd.message)
        cmd = result.pop(0)
        self.assertEqual(b"commit", cmd.name)
        commit_cmd = cast(commands.CommitCommand, cmd)
        self.assertEqual(b"5", commit_cmd.mark)
        self.assertEqual(b"submodule test\n", commit_cmd.message)
        file_cmd1 = result.pop(0)
        self.assertEqual(b"filemodify", file_cmd1.name)
        file_modify_cmd = cast(commands.FileModifyCommand, file_cmd1)
        self.assertEqual(b"tree-id", file_modify_cmd.path)
        self.assertEqual(0o160000, file_modify_cmd.mode)
        self.assertEqual(b"rev-id", file_modify_cmd.dataref)
        cmd = result.pop(0)
        self.assertEqual(b"feature", cmd.name)
        feature_cmd = cast(commands.FeatureCommand, cmd)
        self.assertEqual(b"whatever", feature_cmd.feature_name)
        self.assertEqual(None, feature_cmd.value)
        cmd = result.pop(0)
        self.assertEqual(b"feature", cmd.name)
        feature_cmd = cast(commands.FeatureCommand, cmd)
        self.assertEqual(b"foo", feature_cmd.feature_name)
        self.assertEqual(b"bar", feature_cmd.value)
        cmd = result.pop(0)
        self.assertEqual(b"commit", cmd.name)
        commit_cmd = cast(commands.CommitCommand, cmd)
        self.assertEqual(b"6", commit_cmd.mark)
        self.assertEqual(b"test of properties", commit_cmd.message)
        self.assertEqual(
            {
                b"p1": None,
                b"p2": b"hohum",
                b"p3": b"alpha\nbeta\ngamma",
                b"p4": b"whatever",
            },
            commit_cmd.properties,
        )
        cmd = result.pop(0)
        self.assertEqual(b"commit", cmd.name)
        commit_cmd = cast(commands.CommitCommand, cmd)
        self.assertEqual(b"7", commit_cmd.mark)
        self.assertEqual(b"multi-author test", commit_cmd.message)
        self.assertEqual(b"", commit_cmd.committer[0])
        self.assertEqual(b"bugs@bunny.org", commit_cmd.committer[1])
        self.assertEqual(b"Fluffy", commit_cmd.author[0])  # type: ignore[index]
        self.assertEqual(b"fluffy@bunny.org", commit_cmd.author[1])  # type: ignore[index]
        self.assertEqual(b"Daffy", commit_cmd.more_authors[0][0])  # type: ignore[index]
        self.assertEqual(b"daffy@duck.org", commit_cmd.more_authors[0][1])  # type: ignore[index]
        self.assertEqual(b"Donald", commit_cmd.more_authors[1][0])  # type: ignore[index]
        self.assertEqual(b"donald@duck.org", commit_cmd.more_authors[1][1])  # type: ignore[index]

    def test_done_feature_missing_done(self) -> None:
        s = io.BytesIO(b"""feature done
""")
        p = parser.ImportParser(s)
        cmds = p.iter_commands()
        self.assertEqual(b"feature", next(cmds).name)
        self.assertRaises(errors.PrematureEndOfStream, lambda: next(cmds))

    def test_done_with_feature(self) -> None:
        s = io.BytesIO(b"""feature done
done
more data
""")
        p = parser.ImportParser(s)
        cmds = p.iter_commands()
        self.assertEqual(b"feature", next(cmds).name)
        self.assertRaises(StopIteration, lambda: next(cmds))

    def test_done_without_feature(self) -> None:
        s = io.BytesIO(b"""done
more data
""")
        p = parser.ImportParser(s)
        cmds = p.iter_commands()
        self.assertEqual([], list(cmds))

    def test_blob_with_original_oid(self) -> None:
        s = io.BytesIO(
            b"""blob
mark :1
original-oid abc123def456
data 11
hello world
"""
        )
        p = parser.ImportParser(s)
        cmd = next(p.iter_commands())
        self.assertEqual(b"blob", cmd.name)
        blob_cmd = cast(commands.BlobCommand, cmd)
        self.assertEqual(b"1", blob_cmd.mark)
        self.assertEqual(b"abc123def456", blob_cmd.original_oid)
        self.assertEqual(b"hello world", blob_cmd.data)

    def test_commit_with_original_oid(self) -> None:
        s = io.BytesIO(
            b"""commit refs/heads/master
mark :2
original-oid 6193131b432739c1c6c9ac85614f7ce1e2a59854
committer Joe Doe <joe@example.com> 1234567890 +0000
data 7
Testing
"""
        )
        p = parser.ImportParser(s)
        cmd = next(p.iter_commands())
        self.assertEqual(b"commit", cmd.name)
        commit_cmd = cast(commands.CommitCommand, cmd)
        self.assertEqual(b"2", commit_cmd.mark)
        self.assertEqual(
            b"6193131b432739c1c6c9ac85614f7ce1e2a59854", commit_cmd.original_oid
        )
        self.assertEqual(b"refs/heads/master", commit_cmd.ref)
        self.assertEqual(b"Testing", commit_cmd.message)

    def test_tag_with_original_oid(self) -> None:
        s = io.BytesIO(
            b"""tag refs/tags/v1.0
from :2
original-oid 498a0acad8ad7e20e58933f954a3f1369d29b517
tagger Jane Doe <jane@example.com> 1234567890 +0000
data 11
Version 1.0
"""
        )
        p = parser.ImportParser(s)
        cmd = next(p.iter_commands())
        self.assertEqual(b"tag", cmd.name)
        tag_cmd = cast(commands.TagCommand, cmd)
        self.assertEqual(b":2", tag_cmd.from_)
        self.assertEqual(
            b"498a0acad8ad7e20e58933f954a3f1369d29b517", tag_cmd.original_oid
        )
        self.assertEqual(b"refs/tags/v1.0", tag_cmd.id)
        self.assertEqual(b"Version 1.0", tag_cmd.message)

    def test_mixed_with_and_without_original_oid(self) -> None:
        """Test that original-oid is optional and parsing works with mixed commands"""
        s = io.BytesIO(
            b"""blob
mark :1
data 4
test
blob
mark :2
original-oid xyz789
data 5
test2
commit refs/heads/master
mark :3
committer A <a@b.com> 1234567890 +0000
data 1
A
commit refs/heads/master
mark :4
original-oid def456
committer B <b@c.com> 1234567890 +0000
data 1
B
"""
        )
        p = parser.ImportParser(s)
        cmds = list(p.iter_commands())
        self.assertEqual(4, len(cmds))

        # First blob without original-oid
        self.assertEqual(b"blob", cmds[0].name)
        blob1 = cast(commands.BlobCommand, cmds[0])
        self.assertIsNone(blob1.original_oid)

        # Second blob with original-oid
        self.assertEqual(b"blob", cmds[1].name)
        blob2 = cast(commands.BlobCommand, cmds[1])
        self.assertEqual(b"xyz789", blob2.original_oid)

        # First commit without original-oid
        self.assertEqual(b"commit", cmds[2].name)
        commit1 = cast(commands.CommitCommand, cmds[2])
        self.assertIsNone(commit1.original_oid)

        # Second commit with original-oid
        self.assertEqual(b"commit", cmds[3].name)
        commit2 = cast(commands.CommitCommand, cmds[3])
        self.assertEqual(b"def456", commit2.original_oid)

    def test_original_oid_roundtrip(self) -> None:
        """Test that commands with original-oid can be serialized and parsed back correctly"""
        # Test blob roundtrip
        blob = commands.BlobCommand(b"1", b"test data", original_oid=b"abc123")
        blob_bytes = bytes(blob)
        p = parser.ImportParser(io.BytesIO(blob_bytes))
        parsed_blob = cast(commands.BlobCommand, next(p.iter_commands()))
        self.assertEqual(b"abc123", parsed_blob.original_oid)
        self.assertEqual(b"test data", parsed_blob.data)

        # Test commit roundtrip
        commit = commands.CommitCommand(
            b"refs/heads/master",
            b"2",
            None,
            (b"Joe", b"joe@example.com", 1234567890, 0),
            b"test",
            None,
            None,
            None,
            original_oid=b"def456",
        )
        commit_bytes = bytes(commit)
        p = parser.ImportParser(io.BytesIO(commit_bytes))
        parsed_commit = cast(commands.CommitCommand, next(p.iter_commands()))
        self.assertEqual(b"def456", parsed_commit.original_oid)
        self.assertEqual(b"test", parsed_commit.message)

        # Test tag roundtrip
        tag = commands.TagCommand(
            b"refs/tags/v1.0",
            b":2",
            (b"Jane", b"jane@example.com", 1234567890, 0),
            b"Version 1.0",
            original_oid=b"789xyz",
        )
        tag_bytes = bytes(tag)
        p = parser.ImportParser(io.BytesIO(tag_bytes))
        parsed_tag = cast(commands.TagCommand, next(p.iter_commands()))
        self.assertEqual(b"789xyz", parsed_tag.original_oid)
        self.assertEqual(b"Version 1.0", parsed_tag.message)


class TestStringParsing(unittest.TestCase):
    def test_unquote(self) -> None:
        s = rb"hello \"sweet\" wo\\r\tld"
        self.assertEqual(rb'hello "sweet" wo\r' + b"\tld", parser._unquote_c_string(s))


class TestPathPairParsing(unittest.TestCase):
    def test_path_pair_simple(self) -> None:
        p = parser.ImportParser(io.BytesIO(b""))
        self.assertEqual([b"foo", b"bar"], p._path_pair(b"foo bar"))

    def test_path_pair_spaces_in_first(self) -> None:
        p = parser.ImportParser(io.BytesIO(b""))
        self.assertEqual([b"foo bar", b"baz"], p._path_pair(b'"foo bar" baz'))


class TestTagParsing(unittest.TestCase):
    def test_tagger_with_email(self) -> None:
        p = parser.ImportParser(
            io.BytesIO(
                b"tag refs/tags/v1.0\n"
                b"from :xxx\n"
                b"tagger Joe Wong <joe@example.com> 1234567890 -0600\n"
                b"data 11\n"
                b"create v1.0"
            )
        )
        cmds = list(p.iter_commands())
        self.assertEqual(1, len(cmds))
        self.assertIsInstance(cmds[0], commands.TagCommand)
        tag_cmd = cast(commands.TagCommand, cmds[0])
        self.assertEqual(
            tag_cmd.tagger, (b"Joe Wong", b"joe@example.com", 1234567890.0, -21600)
        )

    def test_tagger_no_email_strict(self) -> None:
        p = parser.ImportParser(
            io.BytesIO(
                b"tag refs/tags/v1.0\nfrom :xxx\ntagger Joe Wong\ndata 11\ncreate v1.0"
            )
        )
        self.assertRaises(errors.BadFormat, list, p.iter_commands())

    def test_tagger_no_email_not_strict(self) -> None:
        p = parser.ImportParser(
            io.BytesIO(
                b"tag refs/tags/v1.0\nfrom :xxx\ntagger Joe Wong\ndata 11\ncreate v1.0"
            ),
            strict=False,
        )
        cmds = list(p.iter_commands())
        self.assertEqual(1, len(cmds))
        self.assertIsInstance(cmds[0], commands.TagCommand)
        tag_cmd = cast(commands.TagCommand, cmds[0])
        self.assertEqual(tag_cmd.tagger[:2], (b"Joe Wong", None))  # type: ignore[index]
