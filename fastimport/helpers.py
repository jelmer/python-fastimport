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

"""Miscellaneous useful stuff."""

from typing import List, Optional, Dict, Any, Union, Tuple, Set, TextIO, BinaryIO


def _common_path_and_rest(
    l1: bytes, l2: bytes, common: Optional[List[bytes]] = None
) -> Tuple[List[bytes], bytes, bytes]:
    if common is None:
        common = []
    # From http://code.activestate.com/recipes/208993/
    if len(l1) < 1:
        return (common, l1, l2)
    if len(l2) < 1:
        return (common, l1, l2)
    if l1[0] != l2[0]:
        return (common, l1, l2)
    return _common_path_and_rest(
        l1[1:],
        l2[1:],
        common
        + [
            l1[0:1]  # return a byte string in python 3 unlike l1[0] that
            # would return an integer.
        ],
    )


def common_path(path1: bytes, path2: bytes) -> bytes:
    """Find the common bit of 2 paths."""
    return b"".join(_common_path_and_rest(path1, path2)[0])


def common_directory(paths: List[bytes]) -> Optional[bytes]:
    """Find the deepest common directory of a list of paths.

    :return: if no paths are provided, None is returned;
      if there is no common directory, '' is returned;
      otherwise the common directory with a trailing / is returned.
    """
    import posixpath

    def get_dir_with_slash(path: bytes) -> bytes:
        if path == b"" or path.endswith(b"/"):
            return path
        else:
            dirname, basename = posixpath.split(path)
            if dirname == b"":
                return dirname
            else:
                return dirname + b"/"

    if not paths:
        return None
    elif len(paths) == 1:
        return get_dir_with_slash(paths[0])
    else:
        common = common_path(paths[0], paths[1])
        for path in paths[2:]:
            common = common_path(common, path)
        return get_dir_with_slash(common)


def is_inside(directory: bytes, fname: bytes) -> bool:
    """True if fname is inside directory.

    The parameters should typically be passed to osutils.normpath first, so
    that . and .. and repeated slashes are eliminated, and the separators
    are canonical for the platform.

    The empty string as a dir name is taken as top-of-tree and matches
    everything.
    """
    # XXX: Most callers of this can actually do something smarter by
    # looking at the inventory
    if directory == fname:
        return True

    if directory == b"":
        return True

    if not directory.endswith(b"/"):
        directory += b"/"

    return fname.startswith(directory)


def is_inside_any(dir_list: List[bytes], fname: bytes) -> bool:
    """True if fname is inside any of given dirs."""
    for dirname in dir_list:
        if is_inside(dirname, fname):
            return True
    return False


def utf8_bytes_string(s: Union[str, bytes]) -> bytes:
    """Convert a string to a bytes string (if necessary, encode in utf8)"""
    if isinstance(s, str):
        return bytes(s, encoding="utf8")
    else:
        return s


class newobject(object):
    """
    A magical object class that provides Python 2 compatibility methods::
        next
        __unicode__
        __nonzero__

    Subclasses of this class can merely define the Python 3 methods (__next__,
    __str__, and __bool__).

    This is a copy/paste of the future.types.newobject class of the future
    package.
    """

    def next(self) -> Any:
        if hasattr(self, "__next__"):
            return type(self).__next__(self)
        raise TypeError("newobject is not an iterator")

    def __unicode__(self) -> str:
        # All subclasses of the builtin object should have __str__ defined.
        # Note that old-style classes do not have __str__ defined.
        if hasattr(self, "__str__"):
            s = type(self).__str__(self)
        else:
            s = str(self)
        try:
            # Python 2 compatibility
            unicode_type = unicode  # type: ignore # noqa: F821
            if isinstance(s, unicode_type):
                return str(s)
            elif hasattr(s, "decode"):
                return str(s.decode("utf-8"))
            else:
                return str(s)
        except NameError:
            # Python 3 - unicode is str
            if isinstance(s, str):
                return s
            elif isinstance(s, bytes):
                return s.decode("utf-8")
            else:
                return str(s)

    def __nonzero__(self) -> bool:
        if hasattr(self, "__bool__"):
            return bool(type(self).__bool__(self))
        # object has no __nonzero__ method
        return True

    # Are these ever needed?
    # def __div__(self):
    #     return self.__truediv__()

    # def __idiv__(self, other):
    #     return self.__itruediv__(other)

    def __long__(self) -> int:
        if not hasattr(self, "__int__"):
            return NotImplemented  # type: ignore
        return int(self.__int__())  # not type(self).__int__(self)

    # def __new__(cls, *args, **kwargs):
    #     """
    #     dict() -> new empty dictionary
    #     dict(mapping) -> new dictionary initialized from a mapping object's
    #         (key, value) pairs
    #     dict(iterable) -> new dictionary initialized as if via:
    #         d = {}
    #         for k, v in iterable:
    #             d[k] = v
    #     dict(**kwargs) -> new dictionary initialized with the name=value
    #         pairs in the keyword argument list.
    #         For example:  dict(one=1, two=2)
    #     """

    #     if len(args) == 0:
    #         return super(newdict, cls).__new__(cls)
    #     elif type(args[0]) == newdict:
    #         return args[0]
    #     else:
    #         value = args[0]
    #     return super(newdict, cls).__new__(cls, value)

    def __native__(self) -> object:
        """
        Hook for the future.utils.native() function
        """
        return object()


def binary_stream(stream: TextIO) -> TextIO:
    """Ensure a stream is binary on Windows.

    :return: the stream
    """
    try:
        import os

        if os.name == "nt":
            fileno = getattr(stream, "fileno", None)
            if fileno:
                no = fileno()
                if no >= 0:  # -1 means we're working as subprocess
                    import msvcrt

                    msvcrt.setmode(no, os.O_BINARY)  # type: ignore[attr-defined,unused-ignore]
    except ImportError:
        pass
    return stream


def invert_dictset(d: Dict[Any, Set[Any]]) -> Dict[Any, List[Any]]:
    """Invert a dict with keys matching a set of values, turned into lists."""
    # Based on recipe from ASPN
    result: Dict[Any, List[Any]] = {}
    for k, c in d.items():
        for v in c:
            keys = result.setdefault(v, [])
            keys.append(k)
    return result


def invert_dict(d: Dict[Any, Any]) -> Dict[Any, List[Any]]:
    """Invert a dictionary with keys matching each value turned into a list."""
    # Based on recipe from ASPN
    result: Dict[Any, List[Any]] = {}
    for k, v in d.items():
        keys = result.setdefault(v, [])
        keys.append(k)
    return result


def defines_to_dict(defines: Optional[List[str]]) -> Optional[Dict[str, str]]:
    """Convert a list of definition strings to a dictionary."""
    if defines is None:
        return None
    result = {}
    for define in defines:
        kv = define.split("=", 1)
        if len(kv) == 1:
            result[define.strip()] = ""
        else:
            result[kv[0].strip()] = kv[1].strip()
    return result


def get_source_stream(source: Optional[str]) -> Union[TextIO, BinaryIO]:
    if source == "-" or source is None:
        import sys

        return binary_stream(sys.stdin)
    elif source.endswith(".gz"):
        import gzip

        return gzip.open(source, "rb")  # type: ignore
    else:
        return open(source, "rb")
