#!/usr/bin/env python
"""
Continuous Testing Helper

Usage:
  conttest <cmd> ...

"""
import argparse
import hashlib
import os.path
import re
import subprocess
import time

HASHES = "hashes"
TIMES = "times"

IGNORE_PREFIXES = (".", "#")
IGNORE_EXTENSIONS = ("pyc", "pyo", "_flymake.py")
IGNORE_DIRS = (".git", ".hg", ".svn")


def include_file_in_checks(path, excludes):
    """
    Determine whether file should be included in checks; reject if
    file has an undesired prefix, an undesired file extension, or
    lives in an undesired directory.
    """

    basename = os.path.basename(path)
    for p in IGNORE_PREFIXES:
        if basename.startswith(p):
            return False
    for extension in IGNORE_EXTENSIONS:
        if path.endswith(extension):
            return False
    parts = path.split(os.path.sep)
    for part in parts:
        if part in IGNORE_DIRS:
            return False
    return not excluded_pattern(path, excludes)


def excluded_pattern(root, excludes):
    for pat in excludes:
        if re.search(pat, root):
            return True


def getstate(full_path, method):
    if method == HASHES:
        try:
            content = open(full_path).read()
        except IOError:
            return None  # will trigger our action
        return hashlib.sha224(content).hexdigest()
    assert method == TIMES
    try:
        return os.path.getmtime(full_path)
    except OSError:  # e.g., broken link
        return None


def walk(top, method, filestates, excludes):
    """
    Walk directory recursively, storing a hash value for any
    non-excluded file; return a dictionary for all such files.
    """
    for root, _, files in os.walk(top, topdown=False):
        for name in files:
            if excluded_pattern(name, excludes):
                continue
            full_path = os.path.join(root, name)
            if include_file_in_checks(full_path, excludes):
                filestates[full_path] = getstate(full_path, method)
    return filestates


def get_exclude_patterns_from_file(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [s.strip() for s in f.read().split() if s.strip() != ""]


def show_diffs(a, b):
    """
    For debugging: print relevant diffs.
    """
    if abs((len(a.keys()) - len(b.keys()))) > 100:
        print("Massive change of keys:", len(a.keys()), "->", len(b.keys()))
    elif a.keys() != b.keys():
        print(set(a.keys()) - set(b.keys()))
    else:
        print([(k, a[k], b[k]) for k in a.keys() if a[k] != b[k]])


def get_diffs(a, b):
    """
    Get all differences between files.
    """
    if a.keys() != b.keys():
        return list(set(a.keys()) - set(b.keys()))
    else:
        return [k for k in a.keys() if a[k] != b[k]]


def watch_dir(dir_, callback, method=HASHES):
    """
    Loop continuously, calling function <callback> if any non-excluded
    file has changed.
    """
    # don't run immediatelly, wait for change to occur first
    excludes = get_exclude_patterns_from_file(dir_ + "/.conttest-excludes")
    filedict = walk(dir_, method, {}, excludes=excludes)

    while True:
        new = walk(dir_, method, {}, excludes=excludes)
        if new != filedict:
            callback(get_diffs(new, filedict))
            # Do it again, in case command changed files (don't retrigger)
            filedict = walk(dir_, method, {}, excludes=excludes)
        time.sleep(0.3)


callbacks = {
    "black": "py -3 -m black {changed_files}",
    "flake8": "py -3 -m flake8 {changed_files}",
    "pytest": "py -3 -m pytest tests/",
}


def run_tasks(changed_files):
    for name, cmd in callbacks.items():
        if "{changed_files}" in cmd:
            cmd = cmd.format(changed_files=" ".join(changed_files))

        print(f"Running command `{cmd}`")
        subprocess.call(cmd, shell=True)


def run_callback_on_update(callback):
    try:
        watch_dir(".", callback, method=TIMES)
    except KeyboardInterrupt:
        print()


def main(directory):
    if not os.path.isdir(directory):
        print(f"Usage: {__file__} directory")
        return

    os.chdir(directory)
    print(f"Started watching directory: `{directory}`")
    run_callback_on_update(run_tasks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Watch a given folder for changes. If a file is changed, run the provided commands for it."
    )
    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        required=True,
        help="Directory to be watched for changes.",
    )

    args = parser.parse_args()
    main(directory=args.directory)
