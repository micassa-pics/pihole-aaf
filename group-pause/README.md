# Pause blocking for selected groups

Open **Disable Blocking** in the left sidebar. Check one or more groups under **Apply to**. For one address, select **One device** instead. The dropdown lists known IPv4 and IPv6 addresses in numeric order. Each address ends with a colon. Its hostname appears on the next line when available. The picker hides loopback addresses unless one has a pause you can resume. Select a time below the list. **Custom time** uses the existing seconds and minutes dialog. Select **All devices** for Pi-hole’s normal network-wide pause.

The host service restores the selected groups after the timer expires. You can close the browser. If the host restarts, the service restores overdue groups when it starts again. **Indefinitely** keeps a group disabled until you enable it on the Groups page. Rules from other enabled groups still apply to their members.

A device pause applies to the selected IP. Other addresses on the same device keep their rules. The worker temporarily assigns that exact IP to an empty group. At expiry it restores the previous memberships or removes the temporary client rule. Select a paused IP and tap **Resume this IP** to end its pause early.

If an administrator deletes a pause marker, the worker reconciles the timer. If someone adds a comment to a temporary client during a pause, the worker archives it in `client_notes` in its timer database before removing the temporary override. Explicit changes to group membership take precedence.

## Install

Use stock Pi-hole Web v6.6.1 or a version where the loader patch passes its apply check. This optional component works independently of the page patches.

1. Identify the admin webroot and the actual gravity database. For Docker, find the host mount that supplies the database. For a native install, the default path is `/etc/pihole/gravity.db`.
2. Create an empty, root-owned directory at `/usr/local/lib/pihole-group-pause/root` (mode 0755). Install `worker.py` in `/usr/local/lib/pihole-group-pause/`. Install `group-pause.service`, `group-pause-reload.socket`, and `group-pause-reload@.service` under `/etc/systemd/system/`. Set `User`, `Group`, and `SocketUser` to match the non-root database owner's UID and GID. Set the source of the writable `/gravity` bind mount to its directory. Mask unrelated files in that directory with `InaccessiblePaths` in a unit drop-in. On upgrade, transfer ownership of the timer state directory and existing state files to the worker. Keep one worker per database. The socket helper runs a single fixed command. Adjust its Docker container name or use the installed native Pi-hole reload command.
3. Start the service with the following commands on the Linux host.

```sh
sudo systemctl daemon-reload
sudo systemctl enable group-pause.service
sudo systemctl restart group-pause.service
sudo systemctl status group-pause.service
```

4. Back up `scripts/lua/footer.lp` in the webroot. Copy `group-pause.js` to `scripts/js/group-pause.js`. From the webroot, run these commands with the absolute patch path.

```sh
git apply --check /path/to/sidebar-loader.patch
git apply /path/to/sidebar-loader.patch
```

5. Reload the admin page. Test a short pause on a group with no clients or rules. Confirm it becomes enabled again with the browser closed. For containers, include the loader and script in a mount or derived image to keep them after recreation.

## How it works

The picker uses Pi-hole’s existing disable function, presets, and custom duration. For selected groups, the browser submits a short-lived, disabled request group through the authenticated Groups API. The worker consumes that request, checks each selected group, and pauses the selection in one database transaction. It records deadlines in its own SQLite file and asks the local socket helper to reload the lists. The worker has no access to the Docker socket. It retries failed reloads. The sidebar waits for a matching reload receipt before it confirms success. The worker opens no network port and needs no stored Pi-hole password.

Reserve the group-name prefixes `awesome-a-fyer-pause-`, `awesome-a-fyer-device-`, and `awesome-a-fyer-done-` for the worker. A request can appear briefly on the Groups page. A request older than 15 seconds expires without starting a pause. If the browser cannot confirm a pause, check the Groups page and the service log.

## Undo

1. Reverse the loader patch in the webroot. Check it with `git apply --reverse --check` first. Remove the added `scripts/js/group-pause.js` file.
2. Let active timers finish, or manually re-enable the paused groups. Check that the `timers`, `device_timers`, and `reload_pending` tables in the worker’s database are empty before removing the service.
3. Disable and stop `group-pause.service`, then stop `group-pause-reload.socket`. Remove the three unit files and the worker, then run `systemctl daemon-reload`. Keep the timer database with your backup.
