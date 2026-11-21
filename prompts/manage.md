# Manage Pi-hole awesome-a-fyer

Copy the entire block into your AI assistant. Choose **Check only** to compare versions without changing Pi-hole.

```text
First ask me which Pi-hole pages I want: Dashboard, DHCP, Query Log, or any combination.
Also ask if I want the optional sidebar group picker. If selected, follow group-pause/README.md from the same verified commit. Verify the worker and loader separately. Use a new group with no clients or rules to test expiry.
Then ask which action I want: Check only, Install/update, or Undo.
Use any choice I already gave you. Wait for both choices before you
download a patch or connect to a device. Work only on the selected pages.

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
  and mounts. A mount for /etc/pihole alone does not save web files.
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

- Check only. Report the status and available revision for each selected
  patch. Include the installed revision if you can identify it. Stop here.

- Install/update. Skip current patches. For an update, reverse the exact
  older patch in staging. Run git apply --check for the latest patch.
  Apply it to the staged files. Verify the changes. Preserve unrelated edits.

- Undo. Skip missing patches. Reverse the exact installed revision in
  staging. Check that the staged changes remove only the selected patches.

Deploy the changes

If the action requires no changes, report the result and finish.
Otherwise, verify all selected changes together. Make a timestamped recovery
copy outside the web root and any disposable container. For a managed
deployment, record the image digest or revision and the rollback procedure.
Recheck the live file hashes or deployment revision before deployment.
If they changed during staging, check the new state before proceeding.

Update the native web files, the source of the web mount, or the existing
image build or deployment definition. For Undo, remove any step that
reapplies the selected patch. Preserve any other patch.
If only a temporary container edit is possible, explain when it will expire.
Ask me whether to use it.

Ask before interrupting DNS or DHCP, replacing a running instance, or
publishing an image outside my deployment. Deploy the verified changes
once. Preserve file permissions, ownership, and links. Give changed JavaScript files a fresh modification time. Verify the rendered script URLs change so existing browsers load the update. Check the served
files on each replica. If deployment fails partway, restore the previous
files or revision. Verify recovery.

Check the result

Open my Admin URL in a fresh browser session. Let me sign in locally.
Check only the selected pages. Use read-only checks. Cancel any test
drafts or delete prompts.

- Dashboard install/update. Collapse and expand each heading. Check that the domain totals and both client summaries appear on the right when collapsed.

- DHCP install/update. Check Expert mode and the collapsible headings.
  Test search and sorting in the static table. Collapse the static section.
  If an active lease has a + button, select it. The static section should
  open with an editable draft. The checkmark confirms it for Save & Apply.
  The curved arrow cancels it. A lease with a reservation has no + button.
  Check that the eye opens queries for the selected client.

- Query Log install/update. Open Query Log from the sidebar. Check Group,
  Count, and Ungroup. Cycle through All, Blocked, and Allowed.
  Check that the client filter stays active. If records are available,
  compare group counts with the API results for the same fixed time range.

- Undo. Check that each selected page works as it did before the patch.

Report the target, Web version, selected pages, and action. Include the
installed and available patch revisions and hashes. List the checks that
passed and any checks you could not complete. If live files changed,
give the recovery location and exact rollback commands. Explain what
survives an update or container replacement. Keep credentials, reservation
details, and client query histories out of the report.
```

[Patch files](../patches/README.md) · [Back to the README](../README.md)
