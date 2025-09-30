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

"""Processor for fast-import commands.

This module provides the skeleton of a fast-import backend.
To import from a fast-import stream to your version-control system:

 - derive a class from the abstract ImportProcessor class and
   implement the *_helper methods.

 - parse a fast-import stream into a sequence of commands, for example
   using the helpers from the parser module.

 - pass that command sequence to the process method of your processor.

See git-fast-import.1 for the meaning of each command and the
processors package for examples.
"""

import sys
import time
from typing import List, Optional, Dict, Any, TextIO

from . import errors
from .helpers import newobject as object


class ImportProcessor(object):
    """Base class for fast-import stream processors.

    Subclasses should override the pre_*, post_* and *_handler
    methods as appropriate.
    """

    known_params: List[bytes] = []

    def __init__(
        self,
        params: Optional[Dict[bytes, Any]] = None,
        verbose: bool = False,
        outf: Optional[TextIO] = None,
    ) -> None:
        if outf is None:
            self.outf = sys.stdout
        else:
            self.outf = outf
        self.verbose = verbose
        if params is None:
            self.params = {}
        else:
            self.params = params
            self.validate_parameters()

        # Handlers can set this to request exiting cleanly without
        # iterating through the remaining commands
        self.finished = False

    def validate_parameters(self) -> None:
        """Validate that the parameters are correctly specified."""
        for p in self.params:
            if p not in self.known_params:
                raise errors.UnknownParameter(p.decode("utf-8"), str(self.known_params))

    def process(self, command_iter: Any) -> None:
        """Import data into Bazaar by processing a stream of commands.

        :param command_iter: an iterator providing commands
        """
        self._process(command_iter)

    def _process(self, command_iter: Any) -> None:
        self.pre_process()
        for cmd in command_iter():
            try:
                name = (cmd.name + b"_handler").decode("utf8")
                handler = getattr(self.__class__, name)
            except KeyError:
                raise errors.MissingHandler(cmd.name)
            else:
                self.pre_handler(cmd)
                handler(self, cmd)
                self.post_handler(cmd)
            if self.finished:
                break
        self.post_process()

    def warning(self, msg: str, *args: Any) -> None:
        """Output a warning but timestamp it."""
        pass

    def debug(self, msg: str, *args: Any) -> None:
        """Output a debug message."""
        pass

    def _time_of_day(self) -> str:
        """Time of day as a string."""
        # Note: this is a separate method so tests can patch in a fixed value
        return time.strftime("%H:%M:%S")

    def pre_process(self) -> None:
        """Hook for logic at start of processing."""
        pass

    def post_process(self) -> None:
        """Hook for logic at end of processing."""
        pass

    def pre_handler(self, cmd: Any) -> None:
        """Hook for logic before each handler starts."""
        pass

    def post_handler(self, cmd: Any) -> None:
        """Hook for logic after each handler finishes."""
        pass

    def progress_handler(self, cmd: Any) -> None:
        """Process a ProgressCommand."""
        raise NotImplementedError(self.progress_handler)

    def blob_handler(self, cmd: Any) -> None:
        """Process a BlobCommand."""
        raise NotImplementedError(self.blob_handler)

    def checkpoint_handler(self, cmd: Any) -> None:
        """Process a CheckpointCommand."""
        raise NotImplementedError(self.checkpoint_handler)

    def commit_handler(self, cmd: Any) -> None:
        """Process a CommitCommand."""
        raise NotImplementedError(self.commit_handler)

    def reset_handler(self, cmd: Any) -> None:
        """Process a ResetCommand."""
        raise NotImplementedError(self.reset_handler)

    def tag_handler(self, cmd: Any) -> None:
        """Process a TagCommand."""
        raise NotImplementedError(self.tag_handler)

    def feature_handler(self, cmd: Any) -> None:
        """Process a FeatureCommand."""
        raise NotImplementedError(self.feature_handler)


class CommitHandler(object):
    """Base class for commit handling.

    Subclasses should override the pre_*, post_* and *_handler
    methods as appropriate.
    """

    def __init__(self, command: Any) -> None:
        self.command = command

    def process(self) -> None:
        self.pre_process_files()
        for fc in self.command.iter_files():
            try:
                name = (fc.name[4:] + b"_handler").decode("utf8")
                handler = getattr(self.__class__, name)
            except KeyError:
                raise errors.MissingHandler(fc.name)
            else:
                handler(self, fc)
        self.post_process_files()

    def warning(self, msg: str, *args: Any) -> None:
        """Output a warning but add context."""
        pass

    def pre_process_files(self) -> None:
        """Prepare for committing."""
        pass

    def post_process_files(self) -> None:
        """Save the revision."""
        pass

    def modify_handler(self, filecmd: Any) -> None:
        """Handle a filemodify command."""
        raise NotImplementedError(self.modify_handler)

    def delete_handler(self, filecmd: Any) -> None:
        """Handle a filedelete command."""
        raise NotImplementedError(self.delete_handler)

    def copy_handler(self, filecmd: Any) -> None:
        """Handle a filecopy command."""
        raise NotImplementedError(self.copy_handler)

    def rename_handler(self, filecmd: Any) -> None:
        """Handle a filerename command."""
        raise NotImplementedError(self.rename_handler)

    def deleteall_handler(self, filecmd: Any) -> None:
        """Handle a filedeleteall command."""
        raise NotImplementedError(self.deleteall_handler)
