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

"""Import processor that queries the input (and doesn't import)."""

from __future__ import print_function
from typing import Dict, List, Optional, Any

from .. import (
    commands,
    processor,
)


class QueryProcessor(processor.ImportProcessor):
    """An import processor that queries the input.

    No changes to the current repository are made.
    """

    known_params = (
        commands.COMMAND_NAMES + commands.FILE_COMMAND_NAMES + [b"commit-mark"]
    )

    def __init__(
        self, params: Optional[Dict[bytes, Any]] = None, verbose: bool = False
    ) -> None:
        processor.ImportProcessor.__init__(self, params, verbose)
        self.parsed_params: Dict[bytes, Optional[List[str]]] = {}
        self.interesting_commit: Optional[str] = None
        self._finished: bool = False
        if params:
            if b"commit-mark" in params:
                commit_mark = params[b"commit-mark"]
                self.interesting_commit = (
                    commit_mark.decode("utf-8")
                    if isinstance(commit_mark, bytes)
                    else commit_mark
                )
                del params[b"commit-mark"]
            for name, value in params.items():
                if value == 1:
                    # All fields
                    fields = None
                else:
                    fields = (
                        value.split(",")
                        if isinstance(value, str)
                        else value.decode("utf-8").split(",")
                    )
                self.parsed_params[name] = fields

    def pre_handler(self, cmd: "commands.ImportCommand") -> None:
        """Hook for logic before each handler starts."""
        if self._finished:
            return
        if self.interesting_commit and cmd.name == b"commit":
            # Cast to CommitCommand to access mark and to_string
            if hasattr(cmd, "mark") and hasattr(cmd, "to_string"):
                commit_cmd = cmd
                mark_str = (
                    commit_cmd.mark.decode("utf-8")
                    if isinstance(commit_cmd.mark, bytes)
                    else str(commit_cmd.mark)
                )
                if mark_str == self.interesting_commit:
                    print(commit_cmd.to_string())
                    self._finished = True
            return
        if cmd.name in self.parsed_params:
            fields = self.parsed_params[cmd.name]
            # Convert bytes fields to str for dump_str
            str_fields = None if fields is None else fields
            str_params = {k.decode("utf-8"): v for k, v in self.parsed_params.items()}
            result_str = cmd.dump_str(str_fields, str_params, self.verbose)
            print("%s" % (result_str,))

    def progress_handler(self, cmd: "commands.ProgressCommand") -> None:
        """Process a ProgressCommand."""
        pass

    def blob_handler(self, cmd: "commands.BlobCommand") -> None:
        """Process a BlobCommand."""
        pass

    def checkpoint_handler(self, cmd: "commands.CheckpointCommand") -> None:
        """Process a CheckpointCommand."""
        pass

    def commit_handler(self, cmd: "commands.CommitCommand") -> None:
        """Process a CommitCommand."""
        pass

    def reset_handler(self, cmd: "commands.ResetCommand") -> None:
        """Process a ResetCommand."""
        pass

    def tag_handler(self, cmd: "commands.TagCommand") -> None:
        """Process a TagCommand."""
        pass

    def feature_handler(self, cmd: "commands.FeatureCommand") -> None:
        """Process a FeatureCommand."""
        feature = cmd.feature_name
        if feature not in commands.FEATURE_NAMES:
            self.warning(
                "feature %s is not supported - parsing may fail"
                % (feature.decode("utf-8"),)
            )
