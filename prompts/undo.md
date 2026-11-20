# Undo Pi-hole Awesome-a-fyer

Copy the entire block into your LLM. If you have the original installation report, include it so the LLM can use the exact patch revision and backup.

```text
Remove the Pi-hole Awesome-a-fyer DHCP and Query Log web patches from my
chosen instance. Preserve DNS settings, reservations, leases, query history
and unrelated edits.

First ask me for the device address, my usual Pi-hole Admin URL, and how I
SSH into the machine that manages it. An SSH alias or my usual SSH command
is enough. Ask for the username, port, jump host, and local key path only if
needed. The web address and SSH host may differ. If I have already supplied
a detail, use it. Let me enter passwords or key passphrases in my own
terminal. Use normal SSH host-key verification.

If I don't know how Pi-hole was installed, discover it. If SSH is
unavailable, ask which management console or deployment project I can use.
If you only have chat access, guide me one step at a time and use my output
to choose the next step. Put commands in fenced code blocks labeled by
machine and shell.

Locate the install report or recovery copy and identify the revision
actually installed. The links below match this edition of the prompt.
If the report records a different commit, retrieve its patches from that
commit of micassa-pics/pihole-awesome-a-fyer and verify the recorded hashes.

Fetch these two patches over HTTPS on the workstation. Both links point to the
same Git commit. Verify each file's SHA-256 before using it.

pihole-dhcp-table.patch
https://raw.githubusercontent.com/micassa-pics/pihole-awesome-a-fyer/27baeefcd1060e57e8934773e5a80371eca7534f/patches/pihole-dhcp-table.patch
SHA-256 0412578cab30d15d7edd13efee9ce5ce7174713b261020db96f93629e8090f24

pihole-query-log-grouping.patch
https://raw.githubusercontent.com/micassa-pics/pihole-awesome-a-fyer/27baeefcd1060e57e8934773e5a80371eca7534f/patches/pihole-query-log-grouping.patch
SHA-256 813d9ec084b4d177b472db5660db6d240cb9e45587f4dc46ec417141434a0e9a

The DHCP patch touches settings-dhcp.lp, scripts/js/settings-dhcp.js and
scripts/js/footer.js. The Query Log patch touches scripts/js/queries.js.
All four paths are relative to the Pi-hole web interface directory.

1. Identify the installed Web version, served web directory, and persistent
   owner of the files. On native, VM, or LXC installs, locate the actual
   web tree. For Docker, Podman, Compose, NAS, Kubernetes, or another
   managed deployment, trace mounts, custom images, and deployment
   definitions. Check whether an update already removed the changes.

2. Stage copies of the four current files. Check each patch independently
   with git apply --reverse --check and git apply --check. Reverse a
   cleanly installed patch in staging. Skip one already absent. If results
   are ambiguous, compare with stock files from the exact installed Web
   version and any verified backup. If you cannot isolate the customization,
   stop before deploying and explain the conflict. Preserve later edits.

3. Save the pre-undo files or deployment revision outside the web root
   and disposable containers. Verify the staged diff removes only these
   patches and the live hashes still match the originals.

4. Undo the change at its persistent source. Remove any build or deployment
   step that would reapply it. Use an earlier image or revision only if it
   preserves the current Pi-hole version and unrelated changes. Ask before
   a rollout that could interrupt DNS or DHCP. Restore file metadata and
   verify the result inside every serving replica. If it fails partway,
   restore and verify the pre-undo state.

5. In a fresh browser session, check the stock DHCP and Query Log pages at
   the real admin URL. Use read-only checks. Report each patch's status,
   checks actually performed, and the recovery copy or revision.
```

[Patch files](../patches/README.md) · [Install prompt](install.md)
