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

"""Test the processor base classes."""

from typing import Any, ClassVar
from unittest import TestCase

from fastimport import errors, processor


class _FileCommand:
    def __init__(self, name: bytes) -> None:
        self.name = name


class _Command:
    def __init__(self, files: list[_FileCommand]) -> None:
        self._files = files

    def iter_files(self) -> Any:
        return iter(self._files)


class TestCommitHandler(TestCase):
    def test_missing_handler(self) -> None:
        handler = processor.CommitHandler(_Command([_FileCommand(b"filebogus")]))
        with self.assertRaises(errors.MissingHandler) as cm:
            handler.process()
        self.assertEqual(b"filebogus", cm.exception.cmd)

    def test_known_handler_is_called(self) -> None:
        seen = []

        class Handler(processor.CommitHandler):
            def modify_handler(self, filecmd: Any) -> None:
                seen.append(filecmd.name)

        cmd = _FileCommand(b"filemodify")
        Handler(_Command([cmd])).process()
        self.assertEqual([b"filemodify"], seen)


class _Processor(processor.ImportProcessor):
    known_params: ClassVar[list[bytes]] = [b"known"]


class TestValidateParameters(TestCase):
    def test_known_parameter_accepted(self) -> None:
        proc = _Processor(params={b"known": b"value"})
        self.assertEqual({b"known": b"value"}, proc.params)

    def test_unknown_bytes_parameter(self) -> None:
        with self.assertRaises(errors.UnknownParameter) as cm:
            _Processor(params={b"unknown": b"value"})
        self.assertEqual("unknown", cm.exception.param)

    def test_unknown_str_parameter(self) -> None:
        with self.assertRaises(errors.UnknownParameter) as cm:
            _Processor(params={"unknown": "value"})  # type: ignore[dict-item]
        self.assertEqual("unknown", cm.exception.param)


class TestQueryProcessorParams(TestCase):
    """Parsing of the -C/--commands parameters."""

    def _parsed(self, params: dict[bytes, Any]) -> dict[bytes, list[str] | None]:
        from fastimport.processors import query_processor

        return query_processor.QueryProcessor(params=params).parsed_params

    def test_no_fields_means_all_fields(self) -> None:
        self.assertEqual({b"reset": None}, self._parsed({b"reset": ""}))

    def test_named_fields(self) -> None:
        self.assertEqual(
            {b"commit": ["mark", "merge"]}, self._parsed({b"commit": "mark,merge"})
        )

    def test_bytes_value(self) -> None:
        self.assertEqual({b"commit": ["mark"]}, self._parsed({b"commit": b"mark"}))
