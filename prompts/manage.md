# Manage Pi-hole Awesome-a-fyer

Copy the full block into your LLM. It will ask which page you want to change before asking how to reach your Pi-hole. For a read-only version comparison, choose **Check only**.

```text
First ask me: “Which Pi-hole page: DHCP, Query Log, or both?”
Then ask: “What would you like to do: check only, install/update, or undo?”
Use any choices I already gave you. Wait for both choices before downloading
patches or connecting. Work only on the selected features.

Connect to my Pi-hole

Ask for the device address, my usual Admin URL, and how I normally SSH in.
A host alias or SSH command is sufficient. Ask for a jump host, port, or
local key path if needed. The SSH host and web address can be different.
Use SSH host-key verification and let me enter secrets in my own terminal.
If SSH is unavailable, ask which console or deployment project I can use.
If you only have chat access, give one step at a time with commands in
fenced blocks labeled by machine and shell.

Find what serves the UI

Identify the running instance, Web and FTL versions, served admin directory,
and persistent owner of the files. Account for custom webroot, webhome and
reverse-proxy prefixes. If several instances match, ask which one I mean.
On a dedicated device, VM or LXC, work inside the OS serving Pi-hole. For
Docker, Podman, Compose or a NAS app, identify the service, image and mounts.
For Kubernetes, Helm, GitOps or other managed deployments, trace the workload
to its deployment definition and account for each serving replica.

Find the patches and identify the installed versions

1. Look up https://api.github.com/repositories/1464872803 and resolve
   refs/heads/main from its clone_url to a full commit SHA for this run.
   For each selected feature, request its GitHub Contents API record at
   <returned API url>/contents/patches/<filename>?ref=<commit>.
   Decode the base64 bytes on the workstation. Compare git hash-object
   --no-filters for the downloaded file with the record's sha, and compute
   its SHA-256 for the report. If the lookup fails, report that the latest
   version is unknown. Stop before installing an unverified update.

   DHCP: pihole-dhcp-table.patch currently touches settings-dhcp.lp,
   scripts/js/settings-dhcp.js and scripts/js/footer.js.
   Query Log: pihole-query-log-grouping.patch currently touches
   scripts/js/queries.js. Inspect the selected diffs for their exact paths.
   All paths are relative to the web interface directory.

2. Copy selected target files into private staging on the workstation.
   Record their paths, hashes, permissions, ownership and symlinks. Read any
   installation report or unpatched backup. Determine the state of each
   feature independently by comparing actual files and patch contents.
   A documentation-only commit does not change a patch's version.

   Current: The latest patch's changes are present and it reverses cleanly
   in staging with git apply --reverse --check. Resolve any disagreement
   with the install report against stock files from the installed Web version.

   Older version installed: Retrieve the recorded patch by commit, verify
   its SHA-256, and test its reversal on a fresh staged copy. Without a
   reliable report, check the selected patch path's GitHub commit history,
   following pagination. Verify candidate blob IDs, try each distinct version
   on its own copy, and confirm the result against stock files or a verified
   backup. Include any files the older version changed.

   Missing: The affected areas match this Web version's stock files or a
   verified unpatched backup, and the latest patch passes git apply --check.
   A Pi-hole update can remove a previously recorded patch.

   Conflict or unknown: If a patch is partially applied, several revisions
   fit, or the installed Web version is incompatible, identify the conflicting
   files and stop before changing any part of the live batch. Ask before
   porting a patch or upgrading Pi-hole itself.

Carry out my chosen action

- Check only: Report the installed and available patch revisions and each
  feature's status. Finish here with no live changes.
- Install/update: Skip current features. For an older installation, reverse
  the identified installed patch in staging first. Apply the latest selected
  patch to the staged files after git apply --check. Compare the result to
  the intended changes and preserve unrelated edits.
- Undo: Skip absent features. Reverse the exact installed patch in staging,
  even when GitHub has a newer version. Verify that only the selected
  customizations were removed. Preserve any unselected patch.

If the batch needs no changes, report that and finish. Otherwise validate
the whole batch before deployment. Keep a timestamped recovery copy outside
the web root and disposable containers. For managed deployments, record
the image digest or revision and rollback procedure. Recheck the live file
hashes or deployment revision before switching to the validated result.

Apply at the persistent source. Update native web files or the source of a
web mount. For image-owned or read-only files, use the existing build and
deployment mechanism; /etc/pihole alone does not persist web assets. On
undo, adjust any build step that would reapply the removed patch, retaining
the other patch if selected previously. If the only option is a temporary
container edit, explain when it expires and ask whether I want that.
Ask before a DNS/DHCP interruption, a serving-instance replacement, or
publication of an image outside my deployment. Deploy once, preserve file
metadata, and check what each replica actually serves. On partial failure,
restore the pre-operation files or deployment and verify recovery.

Verify the selected pages through my usual Admin URL in a fresh browser
session. Let me sign in locally. Use read-only checks and cancel any test
drafts or deletion prompts. For an installation or update:

- DHCP: Check Expert mode, collapsible sections, static search and sorting.
  On an eligible lease, + should reopen a collapsed static table with an
  editable draft. The checkmark stages the draft for Save & Apply and the
  curved arrow cancels it. Verify the eye link opens queries for that client.
  A reserved lease has no +.
- Query Log: Open it from the sidebar. Check Group, Count, Ungroup and the
  All / Blocked / Allowed toggle with the client filter retained. Compare
  group counts to the same fixed-time API result if data is available.

For undo, verify that the selected pages have returned to their expected
pre-patch behavior. Report the target and Web version, selected pages and
action, installed and available revisions and hashes, checks performed,
any unverified UI behavior, and (if live files changed) the recovery copy,
exact rollback commands, and what survives an update or replacement.
Keep credentials, reservation details and client query histories out of the report.
```

[Patch files](../patches/README.md) · [Back to the README](../README.md)
