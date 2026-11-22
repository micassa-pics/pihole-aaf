"""Start the OpenWrt worker in a private filesystem and network namespace."""
import ctypes
import os
from pathlib import Path
import sys

uid, gid = map(int, sys.argv[1:3])
gravity, state, runtime = map(Path, sys.argv[3:6])
if uid <= 0 or gid <= 0:
    raise SystemExit("Expected a non-root database owner and group")

libc = ctypes.CDLL(None, use_errno=True)
if libc.unshare(0x00020000 | 0x40000000) != 0:  # CLONE_NEWNS | CLONE_NEWNET
    raise OSError(ctypes.get_errno(), "Cannot isolate the pause worker")

def mount(src, target, kind=None, flags=0, data=None):
    source = os.fsencode(src) if src is not None else None
    if libc.mount(source, os.fsencode(target), kind, ctypes.c_ulong(flags), data) != 0:
        raise OSError(ctypes.get_errno(), f"Cannot mount {target}")

mount(None, "/", flags=0x4000 | 0x40000)  # MS_REC | MS_PRIVATE
root = runtime / "root"
mount("tmpfs", root, b"tmpfs", 2 | 4, b"mode=0755")
for src, dst, read_only in (
    (Path("/usr"), "usr", True),
    (Path("/lib"), "lib", True),
    (gravity, "gravity", False),
    (state, "state", False),
    (runtime / "socket", "socket", True),
):
    target = root / dst
    target.mkdir()
    mount(src, target, flags=4096)  # MS_BIND
    if read_only:
        mount(None, target, flags=4096 | 32 | 1 | 2 | 4)  # bind remount, ro, nosuid, nodev

os.chroot(root)
os.chdir("/")
os.setgroups([])
os.setgid(gid)
os.setuid(uid)
if libc.prctl(38, 1, 0, 0, 0) != 0:  # PR_SET_NO_NEW_PRIVS
    raise OSError(ctypes.get_errno(), "Cannot disable privilege escalation")
os.umask(0o077)
os.execv(sys.executable, [
    sys.executable, "-IB", "/usr/lib/pihole-pause/worker.py",
    "/gravity/gravity.db", "/state/timers.db", "/socket/reload.sock",
])
