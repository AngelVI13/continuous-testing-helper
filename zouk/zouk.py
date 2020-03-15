#!/usr/bin/env python
"""
Continuous Task Execution Helper.

Usage:
  zouk

"""
import re
import sys
import time
import hashlib
import os.path
import logging
import subprocess
from enum import Enum, auto
from typing import List, Dict, Union, Callable


# setup logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
    level=logging.DEBUG,
)


class Method(Enum):
    """Enum variants that specify what method to use when computing file state."""

    HASHES = auto()
    TIMES = auto()


# setup type aliases for cleaner type hints
FileStatus = Union[str, float, None]
FileStatusDict = Dict[str, FileStatus]


# default ignore dirs, extensions, prefixes
IGNORE_PREFIXES = (".", "#")
IGNORE_EXTENSIONS = ("pyc", "pyo", "_flymake.py")
IGNORE_DIRS = (".git", ".hg", ".svn")


def include_file_in_checks(path: str, excludes: List[str]) -> bool:
    """
    Determine whether file should be included in checks; reject if
    file has an undesired prefix, an undesired file extension, or
    lives in an undesired directory.

    Example:
    >>> include_file_in_checks("myfile.py", excludes=[r".*exe"])
    True
    >>> include_file_in_checks("myfile.py", excludes=[r"my.*"])
    False
    >>> include_file_in_checks("myfile.pyc", excludes=[])
    False
    >>> include_file_in_checks(".myfile.py", excludes=[])
    False
    """

    basename = os.path.basename(path)
    for prefix in IGNORE_PREFIXES:
        if basename.startswith(prefix):
            return False
    for extension in IGNORE_EXTENSIONS:
        if path.endswith(extension):
            return False
    parts = path.split(os.path.sep)
    for part in parts:
        if part in IGNORE_DIRS:
            return False
    return not excluded_pattern(path, excludes)


def excluded_pattern(root: str, excludes: List[str]) -> bool:
    """
    Check if the given path or filename matches any of the provided
    exclude patterns.
    """
    for pattern in excludes:
        if re.search(pattern, root):
            return True
    return False


def getstate(full_path: str, method: Method) -> FileStatus:
    """
    Get current file state based on provided method: i.e. either
    via hashing (sha224) or modified time.

    Example:
    >>> getstate("does_not_exist.py", Method.TIMES) is None
    True
    >>> isinstance(getstate("zoukfile.py", Method.TIMES), float)
    True
    >>> isinstance(getstate("zoukfile.py", Method.HASHES), str)
    True
    """
    if method == Method.HASHES:
        try:
            content = open(full_path, "br").read()
        except IOError:
            return None  # will trigger our action
        return hashlib.sha224(content).hexdigest()

    assert method == Method.TIMES
    try:
        return os.path.getmtime(full_path)
    except OSError:  # e.g., broken link
        return None


def walk(top: str, method: Method, excludes: List[str]) -> FileStatusDict:
    """
    Walk directory recursively, storing a hash value for any
    non-excluded file; return a dictionary for all such files.
    """
    filestates: Dict[str, Union[float, str, None]] = {}
    for root, _, files in os.walk(top, topdown=False):
        for name in files:
            if excluded_pattern(name, excludes):
                continue
            full_path = os.path.join(root, name)
            if include_file_in_checks(full_path, excludes):
                filestates[full_path] = getstate(full_path, method)
    return filestates


def get_exclude_patterns_from_file(path: str) -> List[str]:
    """
    Get all exlude patterns specified in a given file. It is assumed
    that every pattern is whitespace/newline separated.
    """
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as file_:
        return file_.read().split()


def get_diffs(new: FileStatusDict, old: FileStatusDict) -> List[str]:
    """
    Get list of all files which have changed since last check.
    """
    if new.keys() != old.keys():
        return list(set(new.keys()) - set(old.keys()))

    return [key for key in new.keys() if new[key] != old[key]]


def watch_dir(dir_: str, callback: Callable, method: Method = Method.HASHES):
    """
    Loop continuously, calling function <callback> if any non-excluded
    file has changed.
    """
    # compute excludes only in the beginning
    excludes = get_exclude_patterns_from_file(dir_ + "/.zouk-excludes")
    # don't run immediatelly, wait for change to occur first
    filedict = walk(dir_, method, excludes=excludes)

    while True:
        new = walk(dir_, method, excludes=excludes)
        if new != filedict:
            callback(get_diffs(new, filedict))
            # Do it again, in case command changed files (don't retrigger)
            filedict = walk(dir_, method, excludes=excludes)
        time.sleep(0.3)


# global variable contaning all commands to be executed and their aliases
# this dictionary gets populated when the zoukfile.py is evaluated
commands: Dict[str, str] = {
    # example:
    # "black": "py -3 -m black {changed_files}",
    # "flake8": "py -3 -m flake8 {changed_files}",
    # "pytest": "py -3 -m pytest tests/",
}


def run_tasks(changed_files: List[str]):
    """
    Run all provided commands (from zoukfile.py). For commands that
    accept it, a list of changed files is provided.
    """
    for name, cmd in commands.items():
        if "{changed_files}" in cmd:
            cmd = cmd.format(changed_files=" ".join(changed_files))

        logging.info(f"Running command: {name} -> `{cmd}`")
        # todo disable output if return code is 0
        subprocess.call(cmd, shell=True)


def run_callback_on_update(callback: Callable):
    """
    Main entry point fo `zouk`: starts file watcher and provides it
    a callable which to execute on any file change.
    """
    try:
        watch_dir(".", callback, method=Method.TIMES)
    except KeyboardInterrupt:
        print()


def main():
    logging.info(f"Started watching directory: `{os.getcwd()}`")

    zoukfile = "./zoukfile.py"
    if not os.path.exists(zoukfile):
        logging.error(
            "Zoukfile does not exists. Please create a zoukfile.py in your "
            "projects top level directory and specify what commands you "
            "would like to run continously."
        )
        sys.exit(1)

    # evaluate zoukfile.py and update contents of `commands` dict with
    # the ones provided inside the zoukfile.py
    with open(zoukfile, "r") as file_:
        exec(file_.read(), globals())

    run_callback_on_update(run_tasks)


if __name__ == "__main__":
    main()
