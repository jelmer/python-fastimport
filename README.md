python-fastimport
=================

This package provides a parser for and generator of the Git fastimport format.
(https://www.kernel.org/pub/software/scm/git/docs/git-fast-import.html)

## Installation

```bash
pip install fastimport
```

## Example

Here's a simple example of how to parse a fastimport stream:

```python
from fastimport import parser

# Parse a fastimport stream from a file
with open('export.dat', 'rb') as f:
    p = parser.ImportParser(f)
    for cmd in p.iter_commands():
        if cmd.name == b'commit':
            print(f"Commit to branch: {cmd.ref}")
            print(f"Author: {cmd.author}")
            print(f"Message: {cmd.message}")
        elif cmd.name == b'blob':
            print(f"Blob mark: {cmd.mark}, size: {len(cmd.data)}")
```

And here's how to generate a fastimport stream:

```python
from fastimport import commands

# Create a new blob
blob = commands.BlobCommand(
    mark=b'1',
    data=b'Hello, World!\n',
    lineno=0
)

# Create a commit
commit = commands.CommitCommand(
    ref=b'refs/heads/main',
    mark=b'2',
    author=(b'John Doe', b'john@example.com', 1234567890, 0),
    committer=(b'John Doe', b'john@example.com', 1234567890, 0),
    message=b'Initial commit\n',
    from_=None,
    merges=None,
    file_iter=[
        commands.FileModifyCommand(
            path=b'hello.txt',
            mode=0o100644,
            dataref=b':1',
            data=None
        )
    ]
)

# Write to a fastimport stream
with open('import.dat', 'wb') as f:
    f.write(bytes(blob))
    f.write(b'\n')
    f.write(bytes(commit))
```
