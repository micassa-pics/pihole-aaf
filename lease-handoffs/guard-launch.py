"""OpenWrt launcher. Expose only Python, libraries and guard state after startup."""
import ctypes
import os
from pathlib import Path
import sys

state, ipc, api, identity, *origins = sys.argv[1:]
uid, gid = map(int, identity.split(":"))
if uid <= 0 or gid <= 0:
    raise SystemExit("Guard needs a non-root identity")
libc = ctypes.CDLL(None, use_errno=True)
root = Path("/var/run/pihole-reservation-guard/root")
root.mkdir(parents=True,exist_ok=True)
if libc.unshare(0x00020000):
    raise OSError(ctypes.get_errno(), "Cannot create private mount namespace")


def mount(source, path, kind=None, flags=0, data=None):
    if libc.mount(os.fsencode(source) if source else None, os.fsencode(path),kind,ctypes.c_ulong(flags),data):
        raise OSError(ctypes.get_errno(), "Guard mount failed")


mount(None,"/",flags=0x4000 | 0x40000)
mount("tmpfs",root,b"tmpfs",2 | 4,b"mode=0755")
for source,name in [("/usr","usr"),("/lib","lib"),(state,"state"),(ipc,"ipc")]:
    target = root/name
    target.mkdir()
    mount(source,target,flags=4096)
    if name not in ("state","ipc"):
        mount(None,target,flags=4096 | 32 | 1 | 2 | 4)
os.chroot(root)
os.chdir("/")
os.setgroups([])
os.setgid(gid)
os.setuid(uid)
if libc.prctl(38,1,0,0,0):
    raise OSError(ctypes.get_errno(),"Could not set no-new-privileges")
os.execv(sys.executable,[sys.executable,"-IB","/usr/lib/pihole-lease-handoffs/guard.py",
                         "/state","/ipc/guard.sock",api,
                         *[arg for origin in origins for arg in ("--web-origin",origin)]])

