# Guard reservation saves across browsers

The DHCP page sends reservation edits to a private writer. The writer checks the browser's Pi-hole session through the API. It compares revisions for the affected devices, keeps unrelated edits, and serializes the final list update. The manual editor uses the same route.

The writer records each request in SQLite before it sends the change. Each request has an ID. A repeated request returns its recorded result. If Pi-hole restarts during a save, the writer reads the live rules before it settles the request. An uncertain outcome requires **Review change**. The browser can check a receipt without sending another save.

- A static move stays locked until the monitor records the new reservation.
- With DHCP off, the monitor can still confirm a saved static rule. It records no lease activity during that interval. You can also correct duplicate IP rules once the monitor has read the conflicting configuration.
- A lease promotion waits for the same MAC at its reserved IP.
- A conflicting browser refreshes the rows and shows the unsaved draft below the table controls. Use **Cancel move** when the journal records the previous rule. If it records a new reservation, cancellation removes the rule. Use **Review change** when the monitor detects a pending move and the journal has no rollback record.
- Direct API clients, older open pages and direct config edits can bypass the guard. Reload open DHCP pages after deployment. The writer detects observed outside changes and marks affected entries for review. An outside change and reversal between observations can go unseen.

## Docker install

Use the [single-container installation](docker/README.md).

## Native install

Install the DHCP and Query Log patches and the address-handoff monitor first. Back up the running web files, deployment configuration and state. Stage all files before switching the web listener.

Install `checkpoint.py` beside `guard.py`. The guard must read the same published view as the web page. Set `--view` when the view is outside the default `published` directory in the guard state.

1. Use one monitor and one writer for each Pi-hole instance. Give them the same private persistent directory and dedicated non-root UID. Keep this directory outside the Pi-hole config volume. The container startup can change ownership of files in that volume. Keep `state.json` and `guard.sqlite` private. Stop both services before copying an existing checkpoint or journal. Preserve the SQLite journal files if present.
2. Create two separate directories outside the container-managed config volume. Publish `view.txt` in the first. Bind it read-only into Pi-hole at `/run/pihole-lease-handoffs`. Use the second directory for `guard.sock`. Let the monitor write the view and the writer create the socket. Give the proxy group access to the socket. Mount only the socket directory into the proxy at `/run/reservation-guard`. Use the current `worker.py`. It records actual MAC observations separately from inferred static ownership.
3. On systemd, install `guard.py` beside `worker.py` and install `guard.service`. Adjust its paths, upstream URL and service IDs. On OpenWrt, install `guard-launch.py` and `guard.py` in `/usr/lib/pihole-lease-handoffs`. Install `guard-openwrt.init` as executable `/etc/init.d/pihole-reservation-guard`. Set `GUARD_STATE`, `GUARD_IPC`, `GUARD_API`, `GUARD_IDENTITY` and `GUARD_ORIGINS` in root-owned `/etc/pihole-reservation-guard.conf`. Use a numeric API address in the isolated launcher. Set GUARD_ORIGINS to the exact external admin origins separated by spaces. For systemd, pass each origin with --web-origin. Its private filesystem exposes the program, libraries, state and socket directory. Enable and start the writer.
4. Serve the exact `/admin/reservation-guard` route through the existing admin origin. Use [the Nginx location](guard-nginx.location). Adjust the location for a custom webhome. Preserve the original Host, Cookie and X-CSRF-TOKEN headers. Keep existing TLS and LAN access rules. The writer rejects cross-origin requests and accepts only a fixed Pi-hole config API path. It opens a Unix socket and stores no Pi-hole password.
5. If FTL already owns the public web port, put the proxy on that port and bind FTL's web listener to a free loopback port. Proxy all ordinary web traffic to FTL and send only the exact guard route to the socket. Keep DNS and DHCP on the Pi-hole container. Verify the local API URL from the writer's namespace. Test the proxy config before switching the listener.
6. In staging, apply `guard-web.patch` after `web.patch` and copy `reservation-ui.js` to `scripts/js/reservation-ui.js`. Deploy the resulting files through the persistent webroot, derived image or existing override. Keep the previous deployment available for rollback.

```sh
git apply --check /path/to/lease-handoffs/guard-web.patch
git apply /path/to/lease-handoffs/guard-web.patch
cp /path/to/lease-handoffs/reservation-ui.js scripts/js/reservation-ui.js
```

## Verify

Open the DHCP page in two independent browsers. Use a disposable rule. Submit different addresses for the same device from the same starting revision. Check that one save succeeds, the other reports a conflict, and Pi-hole has only the winning address. Retry the winning request ID. Check that the revision stays the same while the lock is pending. Wait for the monitor to acknowledge the move. Remove the test rule and compare the list with the baseline. Restart the services and verify DNS, the DHCP page, the guard read and checkpoint freshness.

Run the regression suite on the workstation.

```sh
python3 -B -m unittest discover -s lease-handoffs -p 'test*.py'
```

## Undo

Reverse `guard-web.patch` in staging and remove the added UI script. Deploy the restored page before stopping the writer. Restore the prior web listener and proxy configuration together. Verify DNS and the admin URL. Keep the private journal and checkpoint with the backup. The monitor can continue serving query history without the writer.

