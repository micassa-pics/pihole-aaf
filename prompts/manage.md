# Manage Pi-hole awesome-a-fyer

## Actions

Choose an action first.

- **Install or update** applies the selected changes. It skips current patches and keeps a recovery copy.
- **Check only** compares installed files and versions with the published patches. It leaves Pi-hole unchanged.
- **Undo to Stock** restores the selected pages to stock and removes the selected optional features. Select all installed patches and features to return the full installation to stock. The prompt checks dependencies before deployment.

## Install options

**The Full Monty** installs or updates Dashboard, DHCP, Query Log, group pause, and the address history and guarded saves bundle. Give the assistant the target and access details. It backs up, installs, and checks the result without routine prompts. This choice allows a brief restart if needed.

Choose any combination of page patches.

| Page | What it adds |
| --- | --- |
| Dashboard | Collapse sections. See query and client totals in the collapsed headings. |
| DHCP | Work with active leases and static reservations in separate tables. Edit reservations and open the Query Log for a device. |
| Query Log | Group repeated queries. See counts and activity charts. Filter for all, blocked, or allowed queries. |

Add optional features as needed.

| Feature | What it adds | What it needs |
| --- | --- | --- |
| Group pause | Pause blocking for selected groups or one IP address. Restore blocking when the timer ends. | A host service. You can add it independently of the page patches. |
| Address history and guarded saves | Follow a device's DNS history across IPv4 address changes. Check for conflicting reservation edits and record saves for recovery. | The DHCP and Query Log patches and persistent state. On Docker, the monitor, guard, and Nginx run inside the same Pi-hole container. |

Copy the entire block below into your AI assistant. Provide your Pi-hole Admin URL and how to reach the device.

```text
If I have not already chosen an action, ask which action I want first.
- Install or update. Apply the selected changes and keep a recovery copy.
- Check only. Compare installed and published versions without changes.
- Undo to Stock. Restore selected pages and remove selected optional features.

For Install or update, offer The Full Monty or a custom install. Explain
that The Full Monty installs all pages and optional features without
routine prompts. A short DNS or DHCP interruption can occur if the install
needs a restart. For Check only or Undo to Stock, ask which features to
check or remove. Offer a choice to include all features.

If I choose The Full Monty, select all features and proceed with Install
or update. Skip the individual feature choices. Use the
target and access details I already gave you. Ask only for missing details
or a blocker you cannot resolve. Then run the backup, install, and checks
without routine approval prompts. Check compatibility for all features
before changing the live instance. Report any blocker that prevents the
full install. Restore the previous deployment if the change fails.

When I choose individual features, let me select any combination.
Briefly explain each page choice.
- Dashboard. Collapse sections and see query and client totals.
- DHCP. Manage active leases and static reservations in separate tables.
- Query Log. Group repeated queries and filter by blocking status.

Offer these optional features separately from the page choices.
- Group pause. Pause blocking for selected groups or one IP address.
- Address history and guarded saves. Follow DNS history across IP changes
  and protect reservation edits from conflicts. This choice needs DHCP
  and Query Log. On Docker, it adds the monitor, guard, and Nginx inside
  the same Pi-hole container.

For group pause, follow group-pause/README.md at the verified commit.
Check the worker and loader separately.
For the address history and guarded saves option, follow the steps below.
Follow lease-handoffs/README.md and lease-handoffs/GUARD.md at the
verified commit. Check the monitor, writer, state, proxy route, UI script,
and both overlays. Report any older install that contains only the monitor.
Apply web.patch before guard-web.patch. Reverse them in the opposite
order before checking, updating, or removing either base patch in staging.
Preserve the existing LAN, TLS, and authentication rules. Check DNS and
the Admin URL after deployment.

Use the choices I already gave you. Confirm a custom selection before
you download files or connect to the device. Work on the selected features.
Check only uses read-only checks. Before Undo to Stock, check which installed
features depend on the selected patches. Confirm any dependent removals.

Find my Pi-hole

Ask for the device address, my usual Pi-hole Admin URL, and my SSH command
or alias. The SSH host can differ from the web host. If necessary, ask
for the jump host, port, or local key path. Verify the SSH host key.
Let me enter credentials in my own terminal.

If SSH is unavailable, ask which console or deployment project I can use.
If you have only chat access, give me one step at a time.
Put commands in fenced blocks. Label each block with the machine and shell.

Identify the running instance and its Web and FTL versions.
If several instances match, ask which one I want.
Find the directory that supplies the admin pages. Check the webroot,
webhome, and any reverse-proxy prefix.

Find where to make a lasting change:
- Device, VM, or LXC: Find the files in the OS that serves Pi-hole.
- Docker, Podman, Compose, or NAS app: Identify the service, image,
  and mounts. Package Docker changes in the Pi-hole image. Run the patch
  processes in that same container. If I selected DHCP and Query Log, use
  the example in lease-handoffs/docker/README.md. For other page choices,
  apply the selected page patches to the image. If I selected address
  history and guarded saves, include both Compose overrides. Set the exact
  admin origins and allowed LAN addresses. Record the existing FTL web
  listener before changing it. Restore it when removing the bundle.
  Preserve the existing TLS and network rules. A mount for /etc/pihole
  alone does not save web files. Propose a second container only if you
  verify a technical requirement. Explain the requirement first.
- Kubernetes, Helm, GitOps, or another managed system: Find the
  deployment definition. Identify each replica that serves the UI.

Get the selected patches

1. Read the GitHub repository record:
   https://api.github.com/repositories/1464962585
   Use its clone_url to resolve refs/heads/main to a full commit SHA.
   Use that commit throughout this run.

2. Choose the patch file for each selected page.
   Dashboard uses pihole-dashboard.patch. It changes index.lp, scripts/js/index.js, and scripts/lua/sidebar.lp.
   DHCP uses pihole-dhcp-table.patch. It changes settings-dhcp.lp,
   scripts/js/settings-dhcp.js, and scripts/js/footer.js. It adds vendor/datatables/dataTables.colReorder.min.js. Record whether that file existed before installation so undo can restore the original state.
   Query Log uses pihole-query-log-grouping.patch.
   It changes queries.lp, scripts/js/queries.js, and scripts/js/utils.js. It adds vendor/datatables/queryLog.colReorder.min.js. Record whether that file existed before installation.
   Check the paths in each patch against the web interface directory.

3. Append /contents/patches/<filename>?ref=<commit> to the record's API url.
   Fetch the file record. Decode its base64 content on the workstation.
   Run git hash-object --no-filters on the file.
   Compare the result with the file record's sha. Calculate the file's
   SHA-256 for the report. If you cannot verify the latest version,
   report it as unknown. Stop before installing an unverified update.

Identify the installed version

Copy the target files to a private staging directory on the workstation.
Record their paths, hashes, permissions, owners, and symbolic links.
Keep the original line endings when you copy files. In staging, use
git -c core.autocrlf=false apply for every Git apply command below.
This preserves the Linux files when you use Git on Windows.
Read any installation report or backup. Check each selected patch
separately. Compare patch contents. A README change alone does not
change the patch version.

Use these checks to identify each patch:

- Current. Check that the files contain the latest changes.
  Test reversal in staging with git apply --reverse --check.
  If the report disagrees, compare the files with the stock files for
  the running Web version. Stock files come from the original Pi-hole release.

- Older version. Get the installed patch from its recorded commit.
  Verify its recorded SHA-256. Test reversal on a fresh staging copy.
  If the recorded commit is unavailable or the report is missing or unreliable,
  search the patch file's commit
  history. Check older pages of results. Verify each candidate's Git blob ID.
  Test each distinct version on a separate copy. Compare the result with
  the matching stock files or a verified unpatched backup. Include files
  that only the older patch changed.

- Missing. Check the affected areas against the matching stock files or
  a verified unpatched backup. Test the latest patch with git apply --check.
  A Pi-hole update can remove a patch.

- Conflict or unknown. Stop if only part of a patch matches, several
  revisions fit, or the Web version is incompatible. Identify the files
  in question. Keep the live installation intact. Ask before adapting
  the patch or upgrading Pi-hole.

Perform the selected action

- Check only. Use reads for the entire run, including the pause service.
  Report the status and available revision for each selected patch.
  Include the installed revision if you can identify it. Stop here.

- Install/update. Skip current patches. For an update, reverse the exact
  older patch in staging. Run git apply --check for the latest patch.
  Apply it to the staged files. Verify the changes. Preserve unrelated edits.

- Undo to Stock. Skip missing patches. Reverse the exact installed revision in
  staging. Check that the staged changes remove only the selected patches.

Deploy the changes

If the action requires no changes, report the result and finish.
Otherwise, verify all selected changes together. Make a timestamped recovery
copy outside the web root and any disposable container. For a managed
deployment, record the image digest or revision and the rollback procedure.
Recheck the live file hashes or deployment revision before deployment.
If they changed during staging, check the new state before proceeding.

Update the native web files, the source of the web mount, or the existing
image build or deployment definition. For Undo to Stock, remove any step that
reapplies the selected patch. Preserve any other patch.
If only a temporary container edit is possible, explain when it will expire.
Ask me whether to use it.

For a custom selection, ask before interrupting DNS or DHCP or replacing
a running instance. The Full Monty allows a brief planned interruption
and recreation of the selected container. Get separate approval before
publishing an image outside my deployment. Deploy the verified changes
once. Preserve file permissions, ownership, and links. Give changed JavaScript files a fresh modification time. Verify the rendered script URLs change so existing browsers load the update. Check the served
files on each replica. If deployment fails partway, restore the previous
files or revision. Verify recovery.

Check the result

Open my Admin URL in a fresh browser session. For The Full Monty, use
the access available. If a check requires interactive sign-in, complete
the other checks and report which check needs sign-in. For a custom
selection, let me sign in locally.
Check only the selected pages. Use read-only checks on the running instance.
Use a disposable instance or intercept writes for edit and delete tests.
Only test pause expiry with approval. Use an empty test group and remove it
after verifying expiry.

- Dashboard install/update. Collapse and expand each heading. Check that the domain totals and both client summaries appear on the right when collapsed.

- DHCP install/update. Check Expert mode and the collapsible headings.
  Test search and sorting in the static table. Collapse the static section.
  Check that the eye opens queries for the selected client.
  In an isolated edit test, select + beside an active lease. Verify that
  the static section opens with a New row. Enter or leaving the edited row
  can save it. Escape cancels the field edit. The curved arrow cancels the
  draft. Save & Apply runs queued deletions.

- Query Log install/update. Open Query Log from the sidebar. Check Group,
  Count, and Ungroup. Cycle through All, Blocked, and Allowed.
  Check that the client filter stays active. If records are available,
  compare group counts with the API results for the same fixed time range.

- Undo to Stock. Check that each selected page works as it did before the patch.

Report the target, Web version, selected pages, and action. Include the
installed and available patch revisions and hashes. List the checks that
passed and any checks you could not complete. If live files changed,
give the recovery location and exact rollback commands. Explain what
survives an update or container replacement. Keep credentials, reservation
details, and client query histories out of the report.
```

[Patch files](../patches/README.md) · [Back to the README](../README.md)
