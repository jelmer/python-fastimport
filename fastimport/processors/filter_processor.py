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

"""Import processor that filters the input (and doesn't import)."""

from .. import (
    commands,
    helpers,
    processor,
)
import stat
from typing import List, Optional, Dict, Any, Set


class FilterProcessor(processor.ImportProcessor):
    """An import processor that filters the input to include/exclude objects.

    No changes to the current repository are made.

    Here are the supported parameters:

    * include_paths - a list of paths that commits must change in order to
      be kept in the output stream

    * exclude_paths - a list of paths that should not appear in the output
      stream

    * squash_empty_commits - if set to False, squash commits that don't have
      any changes after the filter has been applied
    """

    known_params = [b"include_paths", b"exclude_paths", b"squash_empty_commits"]

    def pre_process(self) -> None:
        self.includes: Optional[List[bytes]] = self.params.get(b"include_paths")
        self.excludes: Optional[List[bytes]] = self.params.get(b"exclude_paths")
        self.squash_empty_commits: bool = bool(
            self.params.get(b"squash_empty_commits", True)
        )
        # What's the new root, if any
        self.new_root: Optional[bytes] = (
            helpers.common_directory(self.includes) if self.includes else None
        )
        # Buffer of blobs until we know we need them: mark -> cmd
        self.blobs: Dict[bytes, "commands.BlobCommand"] = {}
        # These are the commits we've squashed so far
        self.squashed_commits: Set[bytes] = set()
        # Map of commit-id to list of parents
        self.parents: Dict[bytes, Optional[List[bytes]]] = {}

    def pre_handler(self, cmd: "commands.ImportCommand") -> None:
        self.command: "commands.ImportCommand" = cmd
        # Should this command be included in the output or not?
        self.keep: bool = False
        # Blobs to dump into the output before dumping the command itself
        self.referenced_blobs: List[bytes] = []

    def post_handler(self, cmd: "commands.ImportCommand") -> None:
        if not self.keep:
            return
        # print referenced blobs and the command
        for blob_id in self.referenced_blobs:
            self._print_command(self.blobs[blob_id])
        self._print_command(self.command)

    def progress_handler(self, cmd: "commands.ProgressCommand") -> None:
        """Process a ProgressCommand."""
        # These always pass through
        self.keep = True

    def blob_handler(self, cmd: "commands.BlobCommand") -> None:
        """Process a BlobCommand."""
        # These never pass through directly. We buffer them and only
        # output them if referenced by an interesting command.
        self.blobs[cmd.id] = cmd
        self.keep = False

    def checkpoint_handler(self, cmd: "commands.CheckpointCommand") -> None:
        """Process a CheckpointCommand."""
        # These always pass through
        self.keep = True

    def commit_handler(self, cmd: "commands.CommitCommand") -> None:
        """Process a CommitCommand."""
        # These pass through if they meet the filtering conditions
        interesting_filecmds = self._filter_filecommands(cmd.iter_files)
        if interesting_filecmds or not self.squash_empty_commits:
            # If all we have is a single deleteall, skip this commit
            if len(interesting_filecmds) == 1 and isinstance(
                interesting_filecmds[0], commands.FileDeleteAllCommand
            ):
                pass
            else:
                # Remember just the interesting file commands
                self.keep = True
                cmd.file_iter = iter(interesting_filecmds)

                # Record the referenced blobs
                for fc in interesting_filecmds:
                    if isinstance(fc, commands.FileModifyCommand):
                        if fc.dataref is not None and not stat.S_ISDIR(fc.mode):
                            self.referenced_blobs.append(fc.dataref)

                # Update from and merges to refer to commits in the output
                cmd.from_ = self._find_interesting_from(cmd.from_)
                merges = self._find_interesting_merges(cmd.merges)
                if merges is not None:
                    cmd.merges = merges
        else:
            self.squashed_commits.add(cmd.id)

        # Keep track of the parents
        if cmd.from_ and cmd.merges:
            parents = [cmd.from_] + cmd.merges
        elif cmd.from_:
            parents = [cmd.from_]
        else:
            parents = None
        if cmd.mark is not None:
            if isinstance(cmd.mark, bytes):
                self.parents[b":" + cmd.mark] = parents
            elif isinstance(cmd.mark, int):
                self.parents[b":" + str(cmd.mark).encode("ascii")] = parents

    def reset_handler(self, cmd: "commands.ResetCommand") -> None:
        """Process a ResetCommand."""
        if cmd.from_ is None:
            # We pass through resets that init a branch because we have to
            # assume the branch might be interesting.
            self.keep = True
        else:
            # Keep resets if they indirectly reference something we kept
            cmd.from_ = self._find_interesting_from(cmd.from_)
            self.keep = cmd.from_ is not None

    def tag_handler(self, cmd: "commands.TagCommand") -> None:
        """Process a TagCommand."""
        # Keep tags if they indirectly reference something we kept
        cmd.from_ = self._find_interesting_from(cmd.from_)
        self.keep = cmd.from_ is not None

    def feature_handler(self, cmd: "commands.FeatureCommand") -> None:
        """Process a FeatureCommand."""
        feature = cmd.feature_name
        if feature not in commands.FEATURE_NAMES:
            self.warning(
                "feature %s is not supported - parsing may fail"
                % (feature.decode("utf-8"),)
            )
        # These always pass through
        self.keep = True

    def _print_command(self, cmd: "commands.ImportCommand") -> None:
        """Wrapper to avoid adding unnecessary blank lines."""
        text = bytes(cmd)
        try:
            # Try to write bytes first (for BytesIO, binary files, stdout.buffer)
            if hasattr(self.outf, "buffer"):
                self.outf.buffer.write(text)
                if not text.endswith(b"\n"):
                    self.outf.buffer.write(b"\n")
            else:
                # For binary output streams
                self.outf.write(text)  # type: ignore
                if not text.endswith(b"\n"):
                    self.outf.write(b"\n")  # type: ignore
        except (TypeError, AttributeError):
            # Last resort: decode and write as text
            self.outf.write(text.decode("utf-8"))
            if not text.endswith(b"\n"):
                self.outf.write("\n")

    def _filter_filecommands(self, filecmd_iter: Any) -> List["commands.FileCommand"]:
        """Return the filecommands filtered by includes & excludes.

        :return: a list of FileCommand objects
        """
        if self.includes is None and self.excludes is None:
            return list(filecmd_iter() if callable(filecmd_iter) else filecmd_iter)

        # Do the filtering, adjusting for the new_root
        result = []
        for fc in filecmd_iter() if callable(filecmd_iter) else filecmd_iter:
            if isinstance(fc, commands.FileModifyCommand) or isinstance(
                fc, commands.FileDeleteCommand
            ):
                if self._path_to_be_kept(fc.path):
                    fc.path = self._adjust_for_new_root(fc.path)
                else:
                    continue
            elif isinstance(fc, commands.FileDeleteAllCommand):
                pass
            elif isinstance(fc, commands.FileRenameCommand):
                fc = self._convert_rename(fc)
            elif isinstance(fc, commands.FileCopyCommand):
                fc = self._convert_copy(fc)
            else:
                self.warning(
                    "cannot handle FileCommands of class %s - ignoring", fc.__class__
                )
                continue
            if fc is not None:
                result.append(fc)
        return result

    def _path_to_be_kept(self, path: bytes) -> bool:
        """Does the given path pass the filtering criteria?"""
        if self.excludes and (
            path in self.excludes or helpers.is_inside_any(self.excludes, path)
        ):
            return False
        if self.includes:
            return path in self.includes or helpers.is_inside_any(self.includes, path)
        return True

    def _adjust_for_new_root(self, path: bytes) -> bytes:
        """Adjust a path given the new root directory of the output."""
        if self.new_root is None:
            return path
        elif path.startswith(self.new_root):
            return path[len(self.new_root) :]
        else:
            return path

    def _find_interesting_parent(self, commit_ref: bytes) -> Optional[bytes]:
        while True:
            if commit_ref not in self.squashed_commits:
                return commit_ref
            parents = self.parents.get(commit_ref)
            if not parents:
                return None
            commit_ref = parents[0]

    def _find_interesting_from(self, commit_ref: Optional[bytes]) -> Optional[bytes]:
        if commit_ref is None:
            return None
        return self._find_interesting_parent(commit_ref)

    def _find_interesting_merges(
        self, commit_refs: Optional[List[bytes]]
    ) -> Optional[List[bytes]]:
        if commit_refs is None:
            return None
        merges = []
        for commit_ref in commit_refs:
            parent = self._find_interesting_parent(commit_ref)
            if parent is not None:
                merges.append(parent)
        if merges:
            return merges
        else:
            return None

    def _convert_rename(
        self, fc: "commands.FileRenameCommand"
    ) -> Optional["commands.FileCommand"]:
        """Convert a FileRenameCommand into a new FileCommand.

        :return: None if the rename is being ignored, otherwise a
          new FileCommand based on the whether the old and new paths
          are inside or outside of the interesting locations.
        """
        old = fc.old_path
        new = fc.new_path
        keep_old = self._path_to_be_kept(old)
        keep_new = self._path_to_be_kept(new)
        if keep_old and keep_new:
            fc.old_path = self._adjust_for_new_root(old)
            fc.new_path = self._adjust_for_new_root(new)
            return fc
        elif keep_old:
            # The file has been renamed to a non-interesting location.
            # Delete it!
            old = self._adjust_for_new_root(old)
            return commands.FileDeleteCommand(old)
        elif keep_new:
            # The file has been renamed into an interesting location
            # We really ought to add it but we don't currently buffer
            # the contents of all previous files and probably never want
            # to. Maybe fast-import-info needs to be extended to
            # remember all renames and a config file can be passed
            # into here ala fast-import?
            self.warning(
                "cannot turn rename of %s into an add of %s yet"
                % (old.decode("utf-8"), new.decode("utf-8"))
            )
        return None

    def _convert_copy(
        self, fc: "commands.FileCopyCommand"
    ) -> Optional["commands.FileCommand"]:
        """Convert a FileCopyCommand into a new FileCommand.

        :return: None if the copy is being ignored, otherwise a
          new FileCommand based on the whether the source and destination
          paths are inside or outside of the interesting locations.
        """
        src = fc.src_path
        dest = fc.dest_path
        keep_src = self._path_to_be_kept(src)
        keep_dest = self._path_to_be_kept(dest)
        if keep_src and keep_dest:
            fc.src_path = self._adjust_for_new_root(src)
            fc.dest_path = self._adjust_for_new_root(dest)
            return fc
        elif keep_src:
            # The file has been copied to a non-interesting location.
            # Ignore it!
            return None
        elif keep_dest:
            # The file has been copied into an interesting location
            # We really ought to add it but we don't currently buffer
            # the contents of all previous files and probably never want
            # to. Maybe fast-import-info needs to be extended to
            # remember all copies and a config file can be passed
            # into here ala fast-import?
            self.warning(
                "cannot turn copy of %s into an add of %s yet"
                % (src.decode("utf-8"), dest.decode("utf-8"))
            )
        return None
