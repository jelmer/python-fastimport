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

"""Test FilterProcessor"""
from io import BytesIO

from unittest import TestCase

from fastimport import (
    parser,
    )

from fastimport.processors import (
    filter_processor,
    )


# A sample input stream containing all (top level) import commands
_SAMPLE_ALL = b"""\
blob
mark :1
data 4
foo
commit refs/heads/master
mark :2
committer Joe <joe@example.com> 1234567890 +1000
data 14
Initial import
M 644 :1 COPYING
checkpoint
progress first import done
reset refs/remote/origin/master
from :2
tag v0.1
from :2
tagger Joe <joe@example.com> 1234567890 +1000
data 12
release v0.1
"""


# A sample input stream creating the following tree:
#
#  NEWS
#  doc/README.txt
#  doc/index.txt
_SAMPLE_WITH_DIR = b"""\
blob
mark :1
data 9
Welcome!
commit refs/heads/master
mark :100
committer a <b@c> 1234798653 +0000
data 4
test
M 644 :1 doc/README.txt
blob
mark :2
data 17
Life
is
good ...
commit refs/heads/master
mark :101
committer a <b@c> 1234798653 +0000
data 8
test
ing
from :100
M 644 :2 NEWS
blob
mark :3
data 19
Welcome!
my friend
blob
mark :4
data 11
== Docs ==
commit refs/heads/master
mark :102
committer d <b@c> 1234798653 +0000
data 8
test
ing
from :101
M 644 :3 doc/README.txt
M 644 :4 doc/index.txt
"""


class TestCaseWithFiltering(TestCase):

    def assertFiltering(self, input_stream, params, expected):
        outf = BytesIO()
        proc = filter_processor.FilterProcessor(
            params=params)
        proc.outf = outf
        s = BytesIO(input_stream)
        p = parser.ImportParser(s)
        proc.process(p.iter_commands)
        out = outf.getvalue()
        self.assertEqual(expected, out)


class TestNoFiltering(TestCaseWithFiltering):

    def test_params_not_given(self):
        self.assertFiltering(_SAMPLE_ALL, None, _SAMPLE_ALL)

    def test_params_are_none(self):
        params = {b'include_paths': None, b'exclude_paths': None}
        self.assertFiltering(_SAMPLE_ALL, params, _SAMPLE_ALL)


class TestIncludePaths(TestCaseWithFiltering):

    def test_file_in_root(self):
        # Things to note:
        # * only referenced blobs are retained
        # * from clause is dropped from the first command
        params = {b'include_paths': [b'NEWS']}
        self.assertFiltering(_SAMPLE_WITH_DIR, params, b"""\
blob
mark :2
data 17
Life
is
good ...
commit refs/heads/master
mark :101
committer a <b@c> 1234798653 +0000
data 8
test
ing
M 644 :2 NEWS
""")

    def test_file_in_subdir(self):
        #  Additional things to note:
        # * new root: path is now index.txt, not doc/index.txt
        # * other files changed in matching commits are excluded
        params = {b'include_paths': [b'doc/index.txt']}
        self.assertFiltering(_SAMPLE_WITH_DIR, params, b"""\
blob
mark :4
data 11
== Docs ==
commit refs/heads/master
mark :102
committer d <b@c> 1234798653 +0000
data 8
test
ing
M 644 :4 index.txt
""")

    def test_file_with_changes(self):
        #  Additional things to note:
        # * from updated to reference parents in the output
        params = {b'include_paths': [b'doc/README.txt']}
        self.assertFiltering(_SAMPLE_WITH_DIR, params, b"""\
blob
mark :1
data 9
Welcome!
commit refs/heads/master
mark :100
committer a <b@c> 1234798653 +0000
data 4
test
M 644 :1 README.txt
blob
mark :3
data 19
Welcome!
my friend
commit refs/heads/master
mark :102
committer d <b@c> 1234798653 +0000
data 8
test
ing
from :100
M 644 :3 README.txt
""")

    def test_subdir(self):
        params = {b'include_paths': [b'doc/']}
        self.assertFiltering(_SAMPLE_WITH_DIR, params, b"""\
blob
mark :1
data 9
Welcome!
commit refs/heads/master
mark :100
committer a <b@c> 1234798653 +0000
data 4
test
M 644 :1 README.txt
blob
mark :3
data 19
Welcome!
my friend
blob
mark :4
data 11
== Docs ==
commit refs/heads/master
mark :102
committer d <b@c> 1234798653 +0000
data 8
test
ing
from :100
M 644 :3 README.txt
M 644 :4 index.txt
""")

    def test_multiple_files_in_subdir(self):
        # The new root should be the subdrectory
        params = {b'include_paths': [b'doc/README.txt', b'doc/index.txt']}
        self.assertFiltering(_SAMPLE_WITH_DIR, params, b"""\
blob
mark :1
data 9
Welcome!
commit refs/heads/master
mark :100
committer a <b@c> 1234798653 +0000
data 4
test
M 644 :1 README.txt
blob
mark :3
data 19
Welcome!
my friend
blob
mark :4
data 11
== Docs ==
commit refs/heads/master
mark :102
committer d <b@c> 1234798653 +0000
data 8
test
ing
from :100
M 644 :3 README.txt
M 644 :4 index.txt
""")


class TestExcludePaths(TestCaseWithFiltering):

    def test_file_in_root(self):
        params = {b'exclude_paths': [b'NEWS']}
        self.assertFiltering(_SAMPLE_WITH_DIR, params, b"""\
blob
mark :1
data 9
Welcome!
commit refs/heads/master
mark :100
committer a <b@c> 1234798653 +0000
data 4
test
M 644 :1 doc/README.txt
blob
mark :3
data 19
Welcome!
my friend
blob
mark :4
data 11
== Docs ==
commit refs/heads/master
mark :102
committer d <b@c> 1234798653 +0000
data 8
test
ing
from :100
M 644 :3 doc/README.txt
M 644 :4 doc/index.txt
""")

    def test_file_in_subdir(self):
        params = {b'exclude_paths': [b'doc/README.txt']}
        self.assertFiltering(_SAMPLE_WITH_DIR, params, b"""\
blob
mark :2
data 17
Life
is
good ...
commit refs/heads/master
mark :101
committer a <b@c> 1234798653 +0000
data 8
test
ing
M 644 :2 NEWS
blob
mark :4
data 11
== Docs ==
commit refs/heads/master
mark :102
committer d <b@c> 1234798653 +0000
data 8
test
ing
from :101
M 644 :4 doc/index.txt
""")

    def test_subdir(self):
        params = {b'exclude_paths': [b'doc/']}
        self.assertFiltering(_SAMPLE_WITH_DIR, params, b"""\
blob
mark :2
data 17
Life
is
good ...
commit refs/heads/master
mark :101
committer a <b@c> 1234798653 +0000
data 8
test
ing
M 644 :2 NEWS
""")

    def test_multple_files(self):
        params = {b'exclude_paths': [b'doc/index.txt', b'NEWS']}
        self.assertFiltering(_SAMPLE_WITH_DIR, params, b"""\
blob
mark :1
data 9
Welcome!
commit refs/heads/master
mark :100
committer a <b@c> 1234798653 +0000
data 4
test
M 644 :1 doc/README.txt
blob
mark :3
data 19
Welcome!
my friend
commit refs/heads/master
mark :102
committer d <b@c> 1234798653 +0000
data 8
test
ing
from :100
M 644 :3 doc/README.txt
""")


class TestIncludeAndExcludePaths(TestCaseWithFiltering):

    def test_included_dir_and_excluded_file(self):
        params = {
            b'include_paths': [b'doc/'],
            b'exclude_paths': [b'doc/index.txt']}
        self.assertFiltering(_SAMPLE_WITH_DIR, params, b"""\
blob
mark :1
data 9
Welcome!
commit refs/heads/master
mark :100
committer a <b@c> 1234798653 +0000
data 4
test
M 644 :1 README.txt
blob
mark :3
data 19
Welcome!
my friend
commit refs/heads/master
mark :102
committer d <b@c> 1234798653 +0000
data 8
test
ing
from :100
M 644 :3 README.txt
""")


# A sample input stream creating the following tree:
#
#  NEWS
#  doc/README.txt
#  doc/index.txt
#
# It then renames doc/README.txt => doc/README
_SAMPLE_WITH_RENAME_INSIDE = _SAMPLE_WITH_DIR + b"""\
commit refs/heads/master
mark :103
committer d <b@c> 1234798653 +0000
data 10
move intro
from :102
R doc/README.txt doc/README
"""

# A sample input stream creating the following tree:
#
#  NEWS
#  doc/README.txt
#  doc/index.txt
#
# It then renames doc/README.txt => README
_SAMPLE_WITH_RENAME_TO_OUTSIDE = _SAMPLE_WITH_DIR + b"""\
commit refs/heads/master
mark :103
committer d <b@c> 1234798653 +0000
data 10
move intro
from :102
R doc/README.txt README
"""

# A sample input stream creating the following tree:
#
#  NEWS
#  doc/README.txt
#  doc/index.txt
#
# It then renames NEWS => doc/NEWS
_SAMPLE_WITH_RENAME_TO_INSIDE = _SAMPLE_WITH_DIR + b"""\
commit refs/heads/master
mark :103
committer d <b@c> 1234798653 +0000
data 10
move intro
from :102
R NEWS doc/NEWS
"""


class TestIncludePathsWithRenames(TestCaseWithFiltering):

    def test_rename_all_inside(self):
        # These rename commands ought to be kept but adjusted for the new root
        params = {b'include_paths': [b'doc/']}
        self.assertFiltering(_SAMPLE_WITH_RENAME_INSIDE, params, b"""\
blob
mark :1
data 9
Welcome!
commit refs/heads/master
mark :100
committer a <b@c> 1234798653 +0000
data 4
test
M 644 :1 README.txt
blob
mark :3
data 19
Welcome!
my friend
blob
mark :4
data 11
== Docs ==
commit refs/heads/master
mark :102
committer d <b@c> 1234798653 +0000
data 8
test
ing
from :100
M 644 :3 README.txt
M 644 :4 index.txt
commit refs/heads/master
mark :103
committer d <b@c> 1234798653 +0000
data 10
move intro
from :102
R README.txt README
""")

    def test_rename_to_outside(self):
        # These rename commands become deletes
        params = {b'include_paths': [b'doc/']}
        self.assertFiltering(_SAMPLE_WITH_RENAME_TO_OUTSIDE, params, b"""\
blob
mark :1
data 9
Welcome!
commit refs/heads/master
mark :100
committer a <b@c> 1234798653 +0000
data 4
test
M 644 :1 README.txt
blob
mark :3
data 19
Welcome!
my friend
blob
mark :4
data 11
== Docs ==
commit refs/heads/master
mark :102
committer d <b@c> 1234798653 +0000
data 8
test
ing
from :100
M 644 :3 README.txt
M 644 :4 index.txt
commit refs/heads/master
mark :103
committer d <b@c> 1234798653 +0000
data 10
move intro
from :102
D README.txt
""")

    def test_rename_to_inside(self):
        # This ought to create a new file but doesn't yet
        params = {b'include_paths': [b'doc/']}
        self.assertFiltering(_SAMPLE_WITH_RENAME_TO_INSIDE, params, b"""\
blob
mark :1
data 9
Welcome!
commit refs/heads/master
mark :100
committer a <b@c> 1234798653 +0000
data 4
test
M 644 :1 README.txt
blob
mark :3
data 19
Welcome!
my friend
blob
mark :4
data 11
== Docs ==
commit refs/heads/master
mark :102
committer d <b@c> 1234798653 +0000
data 8
test
ing
from :100
M 644 :3 README.txt
M 644 :4 index.txt
""")


# A sample input stream creating the following tree:
#
#  NEWS
#  doc/README.txt
#  doc/index.txt
#
# It then copies doc/README.txt => doc/README
_SAMPLE_WITH_COPY_INSIDE = _SAMPLE_WITH_DIR + b"""\
commit refs/heads/master
mark :103
committer d <b@c> 1234798653 +0000
data 10
move intro
from :102
C doc/README.txt doc/README
"""

# A sample input stream creating the following tree:
#
#  NEWS
#  doc/README.txt
#  doc/index.txt
#
# It then copies doc/README.txt => README
_SAMPLE_WITH_COPY_TO_OUTSIDE = _SAMPLE_WITH_DIR + b"""\
commit refs/heads/master
mark :103
committer d <b@c> 1234798653 +0000
data 10
move intro
from :102
C doc/README.txt README
"""

# A sample input stream creating the following tree:
#
#  NEWS
#  doc/README.txt
#  doc/index.txt
#
# It then copies NEWS => doc/NEWS
_SAMPLE_WITH_COPY_TO_INSIDE = _SAMPLE_WITH_DIR + b"""\
commit refs/heads/master
mark :103
committer d <b@c> 1234798653 +0000
data 10
move intro
from :102
C NEWS doc/NEWS
"""


class TestIncludePathsWithCopies(TestCaseWithFiltering):

    def test_copy_all_inside(self):
        # These copy commands ought to be kept but adjusted for the new root
        params = {b'include_paths': [b'doc/']}
        self.assertFiltering(_SAMPLE_WITH_COPY_INSIDE, params, b"""\
blob
mark :1
data 9
Welcome!
commit refs/heads/master
mark :100
committer a <b@c> 1234798653 +0000
data 4
test
M 644 :1 README.txt
blob
mark :3
data 19
Welcome!
my friend
blob
mark :4
data 11
== Docs ==
commit refs/heads/master
mark :102
committer d <b@c> 1234798653 +0000
data 8
test
ing
from :100
M 644 :3 README.txt
M 644 :4 index.txt
commit refs/heads/master
mark :103
committer d <b@c> 1234798653 +0000
data 10
move intro
from :102
C README.txt README
""")

    def test_copy_to_outside(self):
        # This can be ignored
        params = {b'include_paths': [b'doc/']}
        self.assertFiltering(_SAMPLE_WITH_COPY_TO_OUTSIDE, params, b"""\
blob
mark :1
data 9
Welcome!
commit refs/heads/master
mark :100
committer a <b@c> 1234798653 +0000
data 4
test
M 644 :1 README.txt
blob
mark :3
data 19
Welcome!
my friend
blob
mark :4
data 11
== Docs ==
commit refs/heads/master
mark :102
committer d <b@c> 1234798653 +0000
data 8
test
ing
from :100
M 644 :3 README.txt
M 644 :4 index.txt
""")

    def test_copy_to_inside(self):
        # This ought to create a new file but doesn't yet
        params = {b'include_paths': [b'doc/']}
        self.assertFiltering(_SAMPLE_WITH_COPY_TO_INSIDE, params, b"""\
blob
mark :1
data 9
Welcome!
commit refs/heads/master
mark :100
committer a <b@c> 1234798653 +0000
data 4
test
M 644 :1 README.txt
blob
mark :3
data 19
Welcome!
my friend
blob
mark :4
data 11
== Docs ==
commit refs/heads/master
mark :102
committer d <b@c> 1234798653 +0000
data 8
test
ing
from :100
M 644 :3 README.txt
M 644 :4 index.txt
""")


# A sample input stream with deleteall's creating the following tree:
#
#  NEWS
#  doc/README.txt
#  doc/index.txt
_SAMPLE_WITH_DELETEALL = b"""\
blob
mark :1
data 9
Welcome!
commit refs/heads/master
mark :100
committer a <b@c> 1234798653 +0000
data 4
test
deleteall
M 644 :1 doc/README.txt
blob
mark :3
data 19
Welcome!
my friend
blob
mark :4
data 11
== Docs ==
commit refs/heads/master
mark :102
committer d <b@c> 1234798653 +0000
data 8
test
ing
from :100
deleteall
M 644 :3 doc/README.txt
M 644 :4 doc/index.txt
"""


class TestIncludePathsWithDeleteAll(TestCaseWithFiltering):

    def test_deleteall(self):
        params = {b'include_paths': [b'doc/index.txt']}
        self.assertFiltering(_SAMPLE_WITH_DELETEALL, params, b"""\
blob
mark :4
data 11
== Docs ==
commit refs/heads/master
mark :102
committer d <b@c> 1234798653 +0000
data 8
test
ing
from :100
deleteall
M 644 :4 index.txt
""")


_SAMPLE_WITH_TAGS = _SAMPLE_WITH_DIR + b"""\
tag v0.1
from :100
tagger d <b@c> 1234798653 +0000
data 12
release v0.1
tag v0.2
from :102
tagger d <b@c> 1234798653 +0000
data 12
release v0.2
"""


class TestIncludePathsWithTags(TestCaseWithFiltering):

    def test_tag_retention(self):
        # If a tag references a commit with a parent we kept,
        # keep the tag but adjust 'from' accordingly.
        # Otherwise, delete the tag command.
        params = {b'include_paths': [b'NEWS']}
        self.assertFiltering(_SAMPLE_WITH_TAGS, params, b"""\
blob
mark :2
data 17
Life
is
good ...
commit refs/heads/master
mark :101
committer a <b@c> 1234798653 +0000
data 8
test
ing
M 644 :2 NEWS
tag v0.2
from :101
tagger d <b@c> 1234798653 +0000
data 12
release v0.2
""")


_SAMPLE_WITH_RESETS = _SAMPLE_WITH_DIR + b"""\
reset refs/heads/foo
reset refs/heads/bar
from :102
"""


class TestIncludePathsWithResets(TestCaseWithFiltering):

    def test_reset_retention(self):
        # Resets init'ing a branch (without a from) are passed through.
        # If a reset references a commit with a parent we kept,
        # keep the reset but adjust 'from' accordingly.
        params = {b'include_paths': [b'NEWS']}
        self.assertFiltering(_SAMPLE_WITH_RESETS, params, b"""\
blob
mark :2
data 17
Life
is
good ...
commit refs/heads/master
mark :101
committer a <b@c> 1234798653 +0000
data 8
test
ing
M 644 :2 NEWS
reset refs/heads/foo
reset refs/heads/bar
from :101
""")


# A sample input stream containing empty commit
_SAMPLE_EMPTY_COMMIT = b"""\
blob
mark :1
data 4
foo
commit refs/heads/master
mark :2
committer Joe <joe@example.com> 1234567890 +1000
data 14
Initial import
M 644 :1 COPYING
commit refs/heads/master
mark :3
committer Joe <joe@example.com> 1234567890 +1000
data 12
empty commit
"""

# A sample input stream containing unresolved from and merge references
_SAMPLE_FROM_MERGE_COMMIT = b"""\
blob
mark :1
data 4
foo
commit refs/heads/master
mark :3
committer Joe <joe@example.com> 1234567890 +1000
data 6
import
M 644 :1 COPYING
blob
mark :2
data 4
bar
commit refs/heads/master
mark :4
committer Joe <joe@example.com> 1234567890 +1000
data 19
unknown from commit
from :999
M 644 :2 data/DATA
blob
mark :99
data 4
bar
commit refs/heads/master
mark :5
committer Joe <joe@example.com> 1234567890 +1000
data 12
merge commit
from :3
merge :4
merge :1001
M 644 :99 data/DATA2
"""


class TestSquashEmptyCommitsFlag(TestCaseWithFiltering):

    def test_squash_empty_commit(self):
        params = {b'include_paths': None, b'exclude_paths': None}
        self.assertFiltering(_SAMPLE_EMPTY_COMMIT, params, b"""\
blob
mark :1
data 4
foo
commit refs/heads/master
mark :2
committer Joe <joe@example.com> 1234567890 +1000
data 14
Initial import
M 644 :1 COPYING
""")

    def test_keep_empty_commit(self):
        params = {
            b'include_paths': None,
            b'exclude_paths': None,
            b'squash_empty_commits': False,
            }
        self.assertFiltering(
            _SAMPLE_EMPTY_COMMIT, params, _SAMPLE_EMPTY_COMMIT)

    def test_squash_unresolved_references(self):
        params = {b'include_paths': None, b'exclude_paths': None}
        self.assertFiltering(_SAMPLE_FROM_MERGE_COMMIT, params, b"""\
blob
mark :1
data 4
foo
commit refs/heads/master
mark :3
committer Joe <joe@example.com> 1234567890 +1000
data 6
import
M 644 :1 COPYING
blob
mark :2
data 4
bar
commit refs/heads/master
mark :4
committer Joe <joe@example.com> 1234567890 +1000
data 19
unknown from commit
from :999
M 644 :2 data/DATA
blob
mark :99
data 4
bar
commit refs/heads/master
mark :5
committer Joe <joe@example.com> 1234567890 +1000
data 12
merge commit
from :3
merge :4
merge :1001
M 644 :99 data/DATA2
""")

    def test_keep_unresolved_from_and_merge(self):
        params = {
            b'include_paths': None,
            b'exclude_paths': None,
            b'squash_empty_commits': False,
            }
        self.assertFiltering(
            _SAMPLE_FROM_MERGE_COMMIT, params, _SAMPLE_FROM_MERGE_COMMIT)

    def test_with_excludes(self):
        params = {b'include_paths': None,
                  b'exclude_paths': [b'data/DATA'],
                  b'squash_empty_commits': False}
        self.assertFiltering(_SAMPLE_FROM_MERGE_COMMIT, params, b"""\
blob
mark :1
data 4
foo
commit refs/heads/master
mark :3
committer Joe <joe@example.com> 1234567890 +1000
data 6
import
M 644 :1 COPYING
commit refs/heads/master
mark :4
committer Joe <joe@example.com> 1234567890 +1000
data 19
unknown from commit
from :999
blob
mark :99
data 4
bar
commit refs/heads/master
mark :5
committer Joe <joe@example.com> 1234567890 +1000
data 12
merge commit
from :3
merge :4
merge :1001
M 644 :99 data/DATA2
""")

    def test_with_file_includes(self):
        params = {b'include_paths': [b'COPYING', b'data/DATA2'],
                  b'exclude_paths': None,
                  b'squash_empty_commits': False}
        self.assertFiltering(_SAMPLE_FROM_MERGE_COMMIT, params, b"""\
blob
mark :1
data 4
foo
commit refs/heads/master
mark :3
committer Joe <joe@example.com> 1234567890 +1000
data 6
import
M 644 :1 COPYING
commit refs/heads/master
mark :4
committer Joe <joe@example.com> 1234567890 +1000
data 19
unknown from commit
from :999
blob
mark :99
data 4
bar
commit refs/heads/master
mark :5
committer Joe <joe@example.com> 1234567890 +1000
data 12
merge commit
from :3
merge :4
merge :1001
M 644 :99 data/DATA2
""")

    def test_with_directory_includes(self):
        params = {b'include_paths': [b'data/'],
                  b'exclude_paths': None,
                  b'squash_empty_commits': False}
        self.assertFiltering(_SAMPLE_FROM_MERGE_COMMIT, params, b"""\
commit refs/heads/master
mark :3
committer Joe <joe@example.com> 1234567890 +1000
data 6
import
blob
mark :2
data 4
bar
commit refs/heads/master
mark :4
committer Joe <joe@example.com> 1234567890 +1000
data 19
unknown from commit
from :999
M 644 :2 DATA
blob
mark :99
data 4
bar
commit refs/heads/master
mark :5
committer Joe <joe@example.com> 1234567890 +1000
data 12
merge commit
from :3
merge :4
merge :1001
M 644 :99 DATA2
""")
