# Install Pi-hole Awesome-a-fyer

Copy the entire block into your LLM. You can install DHCP only, Query Log only, or both.

```text
First ask me: “Which would you like to install: DHCP only, Query Log only,
or both?” Use my choice if I already gave one. Wait for a clear selection
before downloading files or connecting. Each patch works independently.
Carry out the selected installation and verification if you have terminal access.

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

Fetch only the selected patch files over HTTPS on the workstation.
Verify each downloaded file's SHA-256 before using it.

pihole-dhcp-table.patch
https://raw.githubusercontent.com/micassa-pics/pihole-awesome-a-fyer/27baeefcd1060e57e8934773e5a80371eca7534f/patches/pihole-dhcp-table.patch
SHA-256 0412578cab30d15d7edd13efee9ce5ce7174713b261020db96f93629e8090f24

pihole-query-log-grouping.patch
https://raw.githubusercontent.com/micassa-pics/pihole-awesome-a-fyer/27baeefcd1060e57e8934773e5a80371eca7534f/patches/pihole-query-log-grouping.patch
SHA-256 813d9ec084b4d177b472db5660db6d240cb9e45587f4dc46ec417141434a0e9a

The DHCP patch touches settings-dhcp.lp, scripts/js/settings-dhcp.js and
scripts/js/footer.js. The Query Log patch touches scripts/js/queries.js.
Paths are relative to the Pi-hole web interface directory. Use the selected
patches and their target files for staging, backup, deployment and reporting.

1. Identify the running instance, Web and FTL versions, and the directory
   actually serving the selected files. Account for a reverse-proxy prefix,
   custom webroot and webhome, or separate web host. If several independent
   instances match, ask which one I want. Inspect only the settings and
   mounts needed to locate the files.

2. Find what maintains those files. On a dedicated device, VM, or LXC
   system container, work inside the OS serving Pi-hole. For Docker,
   Podman, Compose, Portainer, or NAS apps, identify the service, image and
   mounts. Patch a persistent web mount at its source. For image-owned or
   read-only files, use the existing image or deployment project. For
   Kubernetes, Helm, GitOps, or another managed system, trace the running
   workload back to its owning definition and account for every replica.
   An /etc/pihole volume alone does not persist edits to the web assets.
   If only a temporary container-layer change is possible, explain when it
   will disappear and ask whether I want that. Ask before interrupting DNS
   or DHCP, replacing a running instance, or publishing an image externally.

3. Copy the selected target files into a private staging tree with their paths
   intact. Record their hashes, permissions, ownership, and any symlinks.
   Keep a timestamped recovery copy outside the web root and disposable
   containers. For managed deployments also record the current revision,
   image digest, and rollback procedure. The workstation can stage the files
   if Git is unavailable on the target.

4. From the staged web root, run git apply --check for each selected patch. If it
   fails, try git apply --reverse --check to identify an installed patch.
   Apply the missing patches to staging and verify the combined result.
   If all selected patches are already installed, go straight to verification. If a
   patch is ambiguous, partially applied, or incompatible, identify the
   conflicting files before making live changes. Ask before porting a
   patch or upgrading Pi-hole.

5. Confirm the live file hashes or deployment revision still match the
   originals. Deploy the complete validated change once, preserving file
   metadata, settings, volumes, leases, query history and existing customizations
   outside the selection. Verify the served
   files against staging, including bind mounts and every serving replica.
   If deployment fails partway, restore and verify the pre-install state.

6. Check the admin UI in a fresh browser session. Let me sign in locally
   if necessary. Use read-only checks and cancel any test drafts or delete
   prompts. Run the following UI checks for the selected features:

   DHCP: Verify Expert mode, independent collapsible headings,
   search and sorting in the static table, and the collapsed manual editor.
   With an eligible lease, collapse the static table and press +. It should
   reopen with an editable draft at the bottom. Save & Apply should wait for
   Confirm or Cancel. A reserved lease has no +. The eye should open Query
   Log filtered to the lease IP.

   Query Log: Open it directly from the sidebar. Check Group, Count, and the
   All / Blocked / Allowed toggle with the client filter retained. Compare
   counts with the same fixed-time API result if data is available.

7. Report the target, Web version, installed patch commit and hashes, the
   status of each selected patch, checks performed, backup location, and exact undo
   commands. Explain what survives container replacement or a Pi-hole
   update. Keep client query histories and credentials out of the report.
```

[Patch files](../patches/README.md) · [Undo prompt](undo.md)
