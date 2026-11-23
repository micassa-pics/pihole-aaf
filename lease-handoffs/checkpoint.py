"""Commit the private checkpoint and public view with one generation marker."""

import json
import os
from contextlib import contextmanager


@contextmanager
def publication_lock(root, *, exclusive=False):
    import fcntl
    with (root / "publication.lock").open("a") as lock:
        operation = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        fcntl.flock(lock, operation | fcntl.LOCK_NB)
        yield


def sync_directory(path):
    directory = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def write(path, data, mode):
    tmp = path.with_suffix(".tmp")
    with tmp.open("w") as file:
        file.write(data)
        file.flush()
        os.fchmod(file.fileno(), mode)
        os.fsync(file.fileno())
    tmp.replace(path)
    sync_directory(path.parent)


def view_generation(path):
    with path.open() as file:
        marker, number = file.readline().split()
    if marker != "T":
        raise ValueError("Invalid handoff view generation")
    return int(number)


def read_committed(root, view):
    current = root / "state.json"
    previous = root / "state.previous.json"
    generation = view_generation(view)
    if generation == 0:
        return {}
    for path in (current, previous):
        try:
            state = json.loads(path.read_text())
            if state["last"] == generation and view_generation(view) == generation:
                return state
        except (FileNotFoundError, ValueError, KeyError, TypeError):
            continue
    raise ValueError("No private checkpoint matches the published handoff view")


def publish(root, view, previous, state, rows):
    # Keep the committed checkpoint until the public view advances. A retry
    # must preserve the same checkpoint if the prior attempt stopped midway.
    if previous:
        write(root / "state.previous.json", json.dumps(previous), 0o600)
    write(root / "state.json", json.dumps(state), 0o600)
    write(view, rows, 0o640)
