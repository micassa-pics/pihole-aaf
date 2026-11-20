# Install or update Pi-hole Awesome-a-fyer

Copy the entire block into your LLM. Choose DHCP only, Query Log only, or both. You can also ask it to **check for updates only**.

```text
First ask me: “Which would you like to check or install: DHCP only, Query Log only,
or both?” Use my choice if I already gave one. Wait for a clear selection
before downloading files or connecting. Each patch works independently.
If I ask for a check only, report what you find and finish before deployment.

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

On each run, resolve refs/heads/main from
https://github.com/micassa-pics/pihole-awesome-a-fyer.git to its full commit SHA.
Use that same commit throughout this run. For each selected feature, fetch
its GitHub Contents API record from
https://api.github.com/repos/micassa-pics/pihole-awesome-a-fyer/contents/patches/FILENAME?ref=COMMIT
using pihole-dhcp-table.patch for DHCP and pihole-query-log-grouping.patch
for Query Log. Decode the base64 content as bytes on the workstation. Check
that git hash-object --no-filters on the file matches the record's sha, and
compute its SHA-256 for comparison with the installation report. Compare
patch contents per feature: a README change or a change to the other patch
is not an update to this one. If the lookup fails, report the available
version as unknown and stop before installing an unverified update.

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
   Use the workstation for staging. Read any previous installation report
   or recovery copy as evidence of the revision installed on this instance.

4. Determine each selected patch's status from the staged files.
   - Current: The latest patch reverses cleanly and its changes are present.
     If the report names an older patch, check its differences from the
     latest one against the actual files before declaring it current.
     Skip deployment for this feature.
   - Update available: The installed revision differs from the latest one.
     Find its exact patch from the recorded commit and verify its SHA-256.
     Without a reliable report, use the GitHub commit history for this patch
     path up to the resolved commit, following pagination. Try distinct
     historical patch contents on fresh staging copies. Confirm the old
     patch's blob ID and include any paths it formerly changed in the staging
     and backup. Confirm it reverses cleanly to the baseline for the installed Web
     version. Inspect the differences against that baseline so unrelated
     edits survive. Reverse the identified old patch in staging, then run
     git apply --check and apply the latest patch there. Verify the result.
   - Not installed: The affected areas match the stock Web version (or a
     verified unpatched backup) and the latest patch applies cleanly.
     Verify a fresh install in staging. This can happen after a Pi-hole
     update even when an older installation report exists.
   - Conflict or unknown: If checks disagree, multiple revisions fit, or
     the staged upgrade fails, report the affected files. Stop before
     deploying any part of the selected batch. Ask before porting a patch
     or upgrading Pi-hole itself.

   Report installed and available revisions per feature. For a check-only
   request, finish here. If everything is current, finish without a write.

5. Before deploying, keep a timestamped recovery copy of the current files
   outside the web root and disposable containers. For managed deployments
   also record the current revision, image digest, and rollback procedure.
   Confirm the live file hashes or deployment revision still match the
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
