# Undo Pi-hole Awesome-a-fyer

Copy the entire block into your LLM. If you have the original installation report, include it so the LLM can use the exact patch revision and backup.

```text
First ask me: “Which would you like to remove: DHCP only, Query Log only,
or both?” Use my choice if I already gave one. Wait for a clear selection
before downloading files or connecting. Remove only the selected patches.
Preserve any other installed patch, DNS settings, reservations, leases,
query history and unrelated edits.

Then ask me for the device address, my usual Pi-hole Admin URL, and how I
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

Locate the installation report or backup for each selected patch. Use the
exact installed revision for removal, even when GitHub has a newer one.
From https://github.com/micassa-pics/pihole-awesome-a-fyer fetch the selected
file at its recorded commit under patches/: pihole-dhcp-table.patch for DHCP
or pihole-query-log-grouping.patch for Query Log. Verify the recorded SHA-256.
Without a reliable report, resolve main to a commit and inspect the history
of that patch file up to that commit, including older pages. Retrieve distinct
revisions by commit and verify the bytes against GitHub's blob IDs. Identify
the installed revision by trial reversal on fresh staging copies and comparison
with the matching stock Web files or a verified unpatched backup.

The DHCP patch touches settings-dhcp.lp, scripts/js/settings-dhcp.js and
scripts/js/footer.js. The Query Log patch touches scripts/js/queries.js.
Paths are relative to the Pi-hole web interface directory.

1. Identify the installed Web version, served web directory, and persistent
   owner of the files. On native, VM, or LXC installs, locate the actual
   web tree. For Docker, Podman, Compose, NAS, Kubernetes, or another
   managed deployment, trace mounts, custom images, and deployment
   definitions. Check whether an update already removed the changes.

2. Stage the current files targeted by the selection. Check each selected patch
   with git apply --reverse --check and git apply --check. Reverse a
   cleanly installed patch in staging. Skip one already absent after checking
   its affected areas against the stock Web version or backup. If results
   are ambiguous, compare with stock files from the exact installed Web
   version and any verified backup. If you cannot isolate the customization,
   stop before deploying and explain the conflict. Preserve later edits.

3. Save the pre-undo files or deployment revision outside the web root
   and disposable containers. Verify the staged diff removes only these
   patches and the live hashes still match the originals.

4. Undo the change at its persistent source. If a build step applies both
   patches and I selected one, edit the step to keep applying the other.
   Use an earlier image or revision only if it preserves the current Pi-hole
   version, any unselected patch, and unrelated changes. Ask before
   a rollout that could interrupt DNS or DHCP. Restore file metadata and
   verify the result inside every serving replica. If it fails partway,
   restore and verify the pre-undo state.

5. In a fresh browser session, verify that the selected features have been
   removed from their respective admin pages. Use read-only checks.
   Report the status of each selected patch,
   checks actually performed, and the recovery copy or revision.
```

[Patch files](../patches/README.md) · [Install prompt](install.md)
