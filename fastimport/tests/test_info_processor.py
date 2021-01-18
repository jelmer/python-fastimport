# Copyright (C) 2018 Jelmer Vernooij
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

"""Test InfoProcessor"""
from io import BytesIO

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from unittest import TestCase

from fastimport import (
    parser,
    )

from fastimport.processors import (
    info_processor,
    )

simple_fast_import_stream = b"""commit refs/heads/master
mark :1
committer Jelmer Vernooij <jelmer@samba.org> 1299718135 +0100
data 7
initial

"""


class TestFastImportInfo(TestCase):

    def test_simple(self):
        stream = BytesIO(simple_fast_import_stream)
        outf = StringIO()
        proc = info_processor.InfoProcessor(outf=outf)
        p = parser.ImportParser(stream)
        proc.process(p.iter_commands)

        self.maxDiff = None
        self.assertEqual(outf.getvalue(), """Command counts:
\t0\tblob
\t0\tcheckpoint
\t1\tcommit
\t0\tfeature
\t0\tprogress
\t0\treset
\t0\ttag
File command counts:
\t0\tfilemodify
\t0\tfiledelete
\t0\tfilecopy
\t0\tfilerename
\t0\tfiledeleteall
Parent counts:
\t1\tparents-0
\t0\ttotal revisions merged
Commit analysis:
\tno\tblobs referenced by SHA
\tno\texecutables
\tno\tseparate authors found
\tno\tsymlinks
Head analysis:
\t:1\trefs/heads/master
Merges:
""")
