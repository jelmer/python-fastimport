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

"""Test how Commands are displayed"""

from unittest import TestCase


from fastimport import (
    commands,
)


class TestBlobDisplay(TestCase):
    def test_blob(self) -> None:
        c = commands.BlobCommand(b"1", b"hello world")
        self.assertEqual(b"blob\nmark :1\ndata 11\nhello world", bytes(c))

    def test_blob_no_mark(self) -> None:
        c = commands.BlobCommand(None, b"hello world")
        self.assertEqual(b"blob\ndata 11\nhello world", bytes(c))

    def test_blob_with_original_oid(self) -> None:
        c = commands.BlobCommand(
            b"1",
            b"hello world",
            original_oid=b"95d09f2b10159347eece71399a7e2e907ea3df4f",
        )
        self.assertEqual(
            b"blob\n"
            b"mark :1\n"
            b"original-oid 95d09f2b10159347eece71399a7e2e907ea3df4f\n"
            b"data 11\n"
            b"hello world",
            bytes(c),
        )


class TestCheckpointDisplay(TestCase):
    def test_checkpoint(self) -> None:
        c = commands.CheckpointCommand()
        self.assertEqual(b"checkpoint", bytes(c))


class TestCommitDisplay(TestCase):
    def test_commit(self) -> None:
        # user tuple is (name, email, secs-since-epoch, secs-offset-from-utc)
        committer = (b"Joe Wong", b"joe@example.com", 1234567890, -6 * 3600)
        c = commands.CommitCommand(
            b"refs/heads/master",
            b"bbb",
            None,
            committer,
            b"release v1.0",
            b":aaa",
            None,
            None,
        )
        self.assertEqual(
            b"commit refs/heads/master\n"
            b"mark :bbb\n"
            b"committer Joe Wong <joe@example.com> 1234567890 -0600\n"
            b"data 12\n"
            b"release v1.0\n"
            b"from :aaa",
            bytes(c),
        )

    def test_commit_no_mark(self) -> None:
        # user tuple is (name, email, secs-since-epoch, secs-offset-from-utc)
        committer = (b"Joe Wong", b"joe@example.com", 1234567890, -6 * 3600)
        c = commands.CommitCommand(
            b"refs/heads/master",
            None,
            None,
            committer,
            b"release v1.0",
            b":aaa",
            None,
            None,
        )
        self.assertEqual(
            b"commit refs/heads/master\n"
            b"committer Joe Wong <joe@example.com> 1234567890 -0600\n"
            b"data 12\n"
            b"release v1.0\n"
            b"from :aaa",
            bytes(c),
        )

    def test_commit_no_from(self) -> None:
        # user tuple is (name, email, secs-since-epoch, secs-offset-from-utc)
        committer = (b"Joe Wong", b"joe@example.com", 1234567890, -6 * 3600)
        c = commands.CommitCommand(
            b"refs/heads/master",
            b"bbb",
            None,
            committer,
            b"release v1.0",
            None,
            None,
            None,
        )
        self.assertEqual(
            b"commit refs/heads/master\n"
            b"mark :bbb\n"
            b"committer Joe Wong <joe@example.com> 1234567890 -0600\n"
            b"data 12\n"
            b"release v1.0",
            bytes(c),
        )

    def test_commit_with_original_oid(self) -> None:
        # user tuple is (name, email, secs-since-epoch, secs-offset-from-utc)
        committer = (b"Joe Wong", b"joe@example.com", 1234567890, -6 * 3600)
        c = commands.CommitCommand(
            b"refs/heads/master",
            b"bbb",
            None,
            committer,
            b"release v1.0",
            b":aaa",
            None,
            None,
            original_oid="6193131b432739c1c6c9ac85614f7ce1e2a59854",
        )
        self.assertEqual(
            b"commit refs/heads/master\n"
            b"mark :bbb\n"
            b"original-oid 6193131b432739c1c6c9ac85614f7ce1e2a59854\n"
            b"committer Joe Wong <joe@example.com> 1234567890 -0600\n"
            b"data 12\n"
            b"release v1.0\n"
            b"from :aaa",
            bytes(c),
        )

    def test_commit_with_author(self) -> None:
        # user tuple is (name, email, secs-since-epoch, secs-offset-from-utc)
        author = (b"Sue Wong", b"sue@example.com", 1234565432, -6 * 3600)
        committer = (b"Joe Wong", b"joe@example.com", 1234567890, -6 * 3600)
        c = commands.CommitCommand(
            b"refs/heads/master",
            b"bbb",
            author,
            committer,
            b"release v1.0",
            b":aaa",
            None,
            None,
        )
        self.assertEqual(
            b"commit refs/heads/master\n"
            b"mark :bbb\n"
            b"author Sue Wong <sue@example.com> 1234565432 -0600\n"
            b"committer Joe Wong <joe@example.com> 1234567890 -0600\n"
            b"data 12\n"
            b"release v1.0\n"
            b"from :aaa",
            bytes(c),
        )

    def test_commit_with_merges(self) -> None:
        # user tuple is (name, email, secs-since-epoch, secs-offset-from-utc)
        committer = (b"Joe Wong", b"joe@example.com", 1234567890, -6 * 3600)
        c = commands.CommitCommand(
            b"refs/heads/master",
            b"ddd",
            None,
            committer,
            b"release v1.0",
            b":aaa",
            [b":bbb", b":ccc"],
            None,
        )
        self.assertEqual(
            b"commit refs/heads/master\n"
            b"mark :ddd\n"
            b"committer Joe Wong <joe@example.com> 1234567890 -0600\n"
            b"data 12\n"
            b"release v1.0\n"
            b"from :aaa\n"
            b"merge :bbb\n"
            b"merge :ccc",
            bytes(c),
        )

    def test_commit_with_filecommands(self) -> None:
        file_cmds = iter(
            [
                commands.FileDeleteCommand(b"readme.txt"),
                commands.FileModifyCommand(b"NEWS", 0o100644, None, b"blah blah blah"),
            ]
        )
        # user tuple is (name, email, secs-since-epoch, secs-offset-from-utc)
        committer = (b"Joe Wong", b"joe@example.com", 1234567890, -6 * 3600)
        c = commands.CommitCommand(
            b"refs/heads/master",
            b"bbb",
            None,
            committer,
            b"release v1.0",
            b":aaa",
            None,
            file_cmds,
        )
        self.assertEqual(
            b"commit refs/heads/master\n"
            b"mark :bbb\n"
            b"committer Joe Wong <joe@example.com> 1234567890 -0600\n"
            b"data 12\n"
            b"release v1.0\n"
            b"from :aaa\n"
            b"D readme.txt\n"
            b"M 644 inline NEWS\n"
            b"data 14\n"
            b"blah blah blah",
            bytes(c),
        )

    def test_commit_with_more_authors(self) -> None:
        # user tuple is (name, email, secs-since-epoch, secs-offset-from-utc)
        author = (b"Sue Wong", b"sue@example.com", 1234565432, -6 * 3600)
        committer = (b"Joe Wong", b"joe@example.com", 1234567890, -6 * 3600)
        more_authors = [
            (b"Al Smith", b"al@example.com", 1234565432.0, -6 * 3600),
            (b"Bill Jones", b"bill@example.com", 1234565432.0, -6 * 3600),
        ]
        c = commands.CommitCommand(
            b"refs/heads/master",
            b"bbb",
            author,
            committer,
            b"release v1.0",
            b":aaa",
            None,
            None,
            more_authors=more_authors,
        )
        self.assertEqual(
            b"commit refs/heads/master\n"
            b"mark :bbb\n"
            b"author Sue Wong <sue@example.com> 1234565432 -0600\n"
            b"author Al Smith <al@example.com> 1234565432 -0600\n"
            b"author Bill Jones <bill@example.com> 1234565432 -0600\n"
            b"committer Joe Wong <joe@example.com> 1234567890 -0600\n"
            b"data 12\n"
            b"release v1.0\n"
            b"from :aaa",
            bytes(c),
        )

    def test_commit_with_properties(self) -> None:
        # user tuple is (name, email, secs-since-epoch, secs-offset-from-utc)
        committer = (b"Joe Wong", b"joe@example.com", 1234567890, -6 * 3600)
        properties = {
            "greeting": "hello",
            "planet": "world",
        }
        c = commands.CommitCommand(
            b"refs/heads/master",
            b"bbb",
            None,
            committer,
            b"release v1.0",
            b":aaa",
            None,
            None,
            properties=properties,
        )
        self.assertEqual(
            b"commit refs/heads/master\n"
            b"mark :bbb\n"
            b"committer Joe Wong <joe@example.com> 1234567890 -0600\n"
            b"data 12\n"
            b"release v1.0\n"
            b"from :aaa\n"
            b"property greeting 5 hello\n"
            b"property planet 5 world",
            bytes(c),
        )

    def test_commit_with_int_mark(self) -> None:
        # user tuple is (name, email, secs-since-epoch, secs-offset-from-utc)
        committer = (b"Joe Wong", b"joe@example.com", 1234567890, -6 * 3600)
        properties = {
            "greeting": "hello",
            "planet": "world",
        }
        c = commands.CommitCommand(
            b"refs/heads/master",
            123,
            None,
            committer,
            b"release v1.0",
            b":aaa",
            None,
            None,
            properties=properties,
        )
        self.assertEqual(
            b"commit refs/heads/master\n"
            b"mark :123\n"
            b"committer Joe Wong <joe@example.com> 1234567890 -0600\n"
            b"data 12\n"
            b"release v1.0\n"
            b"from :aaa\n"
            b"property greeting 5 hello\n"
            b"property planet 5 world",
            bytes(c),
        )


class TestCommitCopy(TestCase):
    def setUp(self) -> None:
        super(TestCommitCopy, self).setUp()
        file_cmds = iter(
            [
                commands.FileDeleteCommand(b"readme.txt"),
                commands.FileModifyCommand(b"NEWS", 0o100644, None, b"blah blah blah"),
            ]
        )

        committer = (b"Joe Wong", b"joe@example.com", 1234567890, -6 * 3600)
        self.c = commands.CommitCommand(
            b"refs/heads/master",
            b"bbb",
            None,
            committer,
            b"release v1.0",
            b":aaa",
            None,
            file_cmds,
        )

    def test_simple_copy(self) -> None:
        c2 = self.c.copy()

        self.assertFalse(self.c is c2)
        self.assertEqual(bytes(self.c), bytes(c2))

    def test_replace_attr(self) -> None:
        c2 = self.c.copy(mark=b"ccc")
        self.assertEqual(bytes(self.c).replace(b"mark :bbb", b"mark :ccc"), bytes(c2))


class TestFeatureDisplay(TestCase):
    def test_feature(self) -> None:
        c = commands.FeatureCommand(b"dwim")
        self.assertEqual(b"feature dwim", bytes(c))

    def test_feature_with_value(self) -> None:
        c = commands.FeatureCommand(b"dwim", b"please")
        self.assertEqual(b"feature dwim=please", bytes(c))


class TestProgressDisplay(TestCase):
    def test_progress(self) -> None:
        c = commands.ProgressCommand(b"doing foo")
        self.assertEqual(b"progress doing foo", bytes(c))


class TestResetDisplay(TestCase):
    def test_reset(self) -> None:
        c = commands.ResetCommand(b"refs/tags/v1.0", b":xxx")
        self.assertEqual(b"reset refs/tags/v1.0\nfrom :xxx\n", bytes(c))

    def test_reset_no_from(self) -> None:
        c = commands.ResetCommand(b"refs/remotes/origin/master", None)
        self.assertEqual(b"reset refs/remotes/origin/master", bytes(c))


class TestTagDisplay(TestCase):
    def test_tag(self) -> None:
        # tagger tuple is (name, email, secs-since-epoch, secs-offset-from-utc)
        tagger = (b"Joe Wong", b"joe@example.com", 1234567890, -6 * 3600)
        c = commands.TagCommand(b"refs/tags/v1.0", b":xxx", tagger, b"create v1.0")
        self.assertEqual(
            b"tag refs/tags/v1.0\n"
            b"from :xxx\n"
            b"tagger Joe Wong <joe@example.com> 1234567890 -0600\n"
            b"data 11\n"
            b"create v1.0",
            bytes(c),
        )

    def test_tag_with_original_oid(self) -> None:
        # tagger tuple is (name, email, secs-since-epoch, secs-offset-from-utc)
        tagger = (b"Joe Wong", b"joe@example.com", 1234567890, -6 * 3600)
        c = commands.TagCommand(
            b"refs/tags/v1.0",
            b":xxx",
            tagger,
            b"create v1.0",
            original_oid="498a0acad8ad7e20e58933f954a3f1369d29b517",
        )
        self.assertEqual(
            b"tag refs/tags/v1.0\n"
            b"from :xxx\n"
            b"original-oid 498a0acad8ad7e20e58933f954a3f1369d29b517\n"
            b"tagger Joe Wong <joe@example.com> 1234567890 -0600\n"
            b"data 11\n"
            b"create v1.0",
            bytes(c),
        )

    def test_tag_no_from(self) -> None:
        tagger = (b"Joe Wong", b"joe@example.com", 1234567890, -6 * 3600)
        c = commands.TagCommand(b"refs/tags/v1.0", None, tagger, b"create v1.0")
        self.assertEqual(
            b"tag refs/tags/v1.0\n"
            b"tagger Joe Wong <joe@example.com> 1234567890 -0600\n"
            b"data 11\n"
            b"create v1.0",
            bytes(c),
        )


class TestFileModifyDisplay(TestCase):
    def test_filemodify_file(self) -> None:
        c = commands.FileModifyCommand(b"foo/bar", 0o100644, b":23", None)
        self.assertEqual(b"M 644 :23 foo/bar", bytes(c))

    def test_filemodify_file_executable(self) -> None:
        c = commands.FileModifyCommand(b"foo/bar", 0o100755, b":23", None)
        self.assertEqual(b"M 755 :23 foo/bar", bytes(c))

    def test_filemodify_file_internal(self) -> None:
        c = commands.FileModifyCommand(b"foo/bar", 0o100644, None, b"hello world")
        self.assertEqual(b"M 644 inline foo/bar\ndata 11\nhello world", bytes(c))

    def test_filemodify_symlink(self) -> None:
        c = commands.FileModifyCommand(b"foo/bar", 0o120000, None, b"baz")
        self.assertEqual(b"M 120000 inline foo/bar\ndata 3\nbaz", bytes(c))

    def test_filemodify_treeref(self) -> None:
        c = commands.FileModifyCommand(
            b"tree-info", 0o160000, b"revision-id-info", None
        )
        self.assertEqual(b"M 160000 revision-id-info tree-info", bytes(c))


class TestFileDeleteDisplay(TestCase):
    def test_filedelete(self) -> None:
        c = commands.FileDeleteCommand(b"foo/bar")
        self.assertEqual(b"D foo/bar", bytes(c))


class TestFileCopyDisplay(TestCase):
    def test_filecopy(self) -> None:
        c = commands.FileCopyCommand(b"foo/bar", b"foo/baz")
        self.assertEqual(b"C foo/bar foo/baz", bytes(c))

    def test_filecopy_quoted(self) -> None:
        # Check the first path is quoted if it contains spaces
        c = commands.FileCopyCommand(b"foo/b a r", b"foo/b a z")
        self.assertEqual(b'C "foo/b a r" foo/b a z', bytes(c))


class TestFileRenameDisplay(TestCase):
    def test_filerename(self) -> None:
        c = commands.FileRenameCommand(b"foo/bar", b"foo/baz")
        self.assertEqual(b"R foo/bar foo/baz", bytes(c))

    def test_filerename_quoted(self) -> None:
        # Check the first path is quoted if it contains spaces
        c = commands.FileRenameCommand(b"foo/b a r", b"foo/b a z")
        self.assertEqual(b'R "foo/b a r" foo/b a z', bytes(c))


class TestFileDeleteAllDisplay(TestCase):
    def test_filedeleteall(self) -> None:
        c = commands.FileDeleteAllCommand()
        self.assertEqual(b"deleteall", bytes(c))


class TestNotesDisplay(TestCase):
    def test_noteonly(self) -> None:
        c = commands.NoteModifyCommand(b"foo", b"A basic note")
        self.assertEqual(b"N inline :foo\ndata 12\nA basic note", bytes(c))

    def test_notecommit(self) -> None:
        committer = (b"Ed Mund", b"ed@example.org", 1234565432, 0)

        commits = [
            commands.CommitCommand(
                ref=b"refs/heads/master",
                mark=b"1",
                author=committer,
                committer=committer,
                message=b"test\n",
                from_=None,
                merges=[],
                file_iter=[commands.FileModifyCommand(b"bar", 0o100644, None, b"")],
            ),
            commands.CommitCommand(
                ref=b"refs/notes/commits",
                mark=None,
                author=None,
                committer=committer,
                message=b"Notes added by 'git notes add'\n",
                from_=None,
                merges=[],
                file_iter=[commands.NoteModifyCommand(b"1", b"Test note\n")],
                original_oid="c0a594761e2226be654ccd0e0ff0b6af95aa1040",
            ),
            commands.CommitCommand(
                ref=b"refs/notes/test",
                mark=None,
                author=None,
                committer=committer,
                message=b"Notes added by 'git notes add'\n",
                from_=None,
                merges=[],
                file_iter=[commands.NoteModifyCommand(b"1", b"Test test\n")],
            ),
        ]

        self.assertEqual(
            b"""commit refs/heads/master
mark :1
author Ed Mund <ed@example.org> 1234565432 +0000
committer Ed Mund <ed@example.org> 1234565432 +0000
data 5
test

M 644 inline bar
data 0
commit refs/notes/commits
original-oid c0a594761e2226be654ccd0e0ff0b6af95aa1040
committer Ed Mund <ed@example.org> 1234565432 +0000
data 31
Notes added by 'git notes add'

N inline :1
data 10
Test note
commit refs/notes/test
committer Ed Mund <ed@example.org> 1234565432 +0000
data 31
Notes added by 'git notes add'

N inline :1
data 10
Test test
""",
            b"".join([bytes(s) for s in commits]),
        )


class TestPathChecking(TestCase):
    def test_filemodify_path_checking(self) -> None:
        self.assertRaises(
            ValueError, commands.FileModifyCommand, b"", 0o100644, None, b"text"
        )
        self.assertRaises(
            ValueError, commands.FileModifyCommand, None, 0o100644, None, b"text"
        )

    def test_filedelete_path_checking(self) -> None:
        self.assertRaises(ValueError, commands.FileDeleteCommand, b"")
        self.assertRaises(ValueError, commands.FileDeleteCommand, None)

    def test_filerename_path_checking(self) -> None:
        self.assertRaises(ValueError, commands.FileRenameCommand, b"", b"foo")
        self.assertRaises(ValueError, commands.FileRenameCommand, None, b"foo")
        self.assertRaises(ValueError, commands.FileRenameCommand, b"foo", b"")
        self.assertRaises(ValueError, commands.FileRenameCommand, b"foo", None)

    def test_filecopy_path_checking(self) -> None:
        self.assertRaises(ValueError, commands.FileCopyCommand, b"", b"foo")
        self.assertRaises(ValueError, commands.FileCopyCommand, None, b"foo")
        self.assertRaises(ValueError, commands.FileCopyCommand, b"foo", b"")
        self.assertRaises(ValueError, commands.FileCopyCommand, b"foo", None)
