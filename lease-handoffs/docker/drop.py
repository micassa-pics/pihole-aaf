"""Drop the root identity after chroot and before starting a helper."""
import ctypes
import os
import sys

uid, gid = map(int, sys.argv[1:3])
if min(uid, gid) < 1:
    raise SystemExit("A non-root helper identity is required")
os.setgroups([])
os.setgid(gid)
os.setuid(uid)
if ctypes.CDLL(None).prctl(38, 1, 0, 0, 0):
    raise SystemExit("Cannot set no-new-privileges")
args = [sys.executable, "-EBs", *sys.argv[3:]]
# Pass only the publication path. Pi-hole environment variables may contain secrets.
os.execve(sys.executable, args, {"HANDOFF_PUBLISH": "/state/published"})
