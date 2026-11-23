# Follow a device across IPv4 address changes

This optional feature needs both the DHCP and Query Log page patches. A small Python service reads the lease file and DHCP reservations every 15 seconds. It stores address intervals in a separate directory. Pi-hole keeps each DNS query under its original source IP.

- **DHCP to static.** Save the reservation. The new address shows a waiting message until Pi-hole reports a lease at that address for the same MAC. The Query Log then includes the device's observed history at both addresses.
- **Static to static.** Change a reservation's IP. The monitor associates its previous address intervals with the new reservation. The DHCP page checks the monitor's saved checkpoint before it accepts another IP change for that MAC. Other devices remain editable.
- **Same address.** Keep the IP when you create the reservation and use the existing Query Log.

The Query Log keeps the original IP on each row. Grouping still uses domain, type, and source IP. The DHCP activity chart includes complete ten-minute buckets within the recorded intervals. A partial bucket can contain another client's traffic.

Coverage starts when the monitor observes a lease. Static rules can confirm that a reservation changed. Only observed leases establish automatic history windows. Earlier checkpoints mixed both types of evidence. The update keeps those windows for detecting address reuse. Changes made directly through the Pi-hole API or config file bypass the page's edit check. A change and reversal between two checks can go unseen. This feature supports one MAC and one IPv4 address per reservation. Keep one monitor per Pi-hole instance.

The reservation guard checks each device revision and serializes the Pi-hole writes. Two editors can work on different devices. If they change the same device, the second save receives a conflict. The page keeps a copy of the unsaved changes. Use **Cancel move** to restore the previous reservation. Use **Review change** to acknowledge an edit made outside the guard. [Guard setup and recovery](GUARD.md)

If the monitor stops, the DHCP charts show standard per-IP counts with a notice. A filtered Query Log requires a current checkpoint. The ungrouped handoff view defaults to the last 24 hours. Set a start time for older queries. A pending move has no query rows until the device takes its address.

## Docker install

Install address history and guarded saves together. The monitor, guard, and Nginx run in the same Pi-hole container. [Single-container installation](docker/README.md)

## Native install and check

1. Install the two page patches. Copy the admin web files to staging. From that directory, run the following with the path to this feature's patch.

   ```sh
   git apply --check /path/to/lease-handoffs/web.patch
   git apply /path/to/lease-handoffs/web.patch
   ```

2. Locate the live `pihole.toml` and `dhcp.leases`. Confirm that the effective reservations match `dhcp.hosts`. Create a private state directory outside the Pi-hole config volume. Give the service user ownership and mode 0700. For upgrades, stop both services and copy their state there before restarting.
3. Install `checkpoint.py` beside `worker.py`. Run the monitor with Python 3.11 or later. Mount the config directory read-only at `/config`. Create a separate publication directory outside the config volume. Give the monitor write access and the Pi-hole web service read access. Make the publication directory available to the Pi-hole web service at `/run/pihole-lease-handoffs`. Start the monitor at boot.
4. On a dedicated Linux device or VM, use the included systemd service. Adjust its paths and IDs first.

5. Finish the [writer and proxy setup](GUARD.md) before deploying the page. Set `HANDOFF_PUBLISH` to the publication path inside the monitor. Verify that `view.txt` updates after restarting the services. Open a filtered Query Log. For a pending move, check the waiting message and the MAC on the next DHCP lease. The monitor keeps up to 91 days of intervals. Pi-hole controls query retention.

## Update or undo

Keep both overlay revisions and the base patch revisions in the install record. Review interrupted saves and pending moves first. In staging, reverse the guard overlay and then the history overlay. For an update, reapply both after the base update. If any check fails, keep the installed files in place.

```sh
git apply --reverse --check /path/to/installed/lease-handoffs/guard-web.patch
git apply --reverse /path/to/installed/lease-handoffs/guard-web.patch
git apply --reverse --check /path/to/installed/lease-handoffs/web.patch
git apply --reverse /path/to/installed/lease-handoffs/web.patch
```

Deploy the restored web files and remove the added `scripts/js/reservation-ui.js` script. Restore the previous web listener and proxy settings as part of the same change. Stop and disable the writer and monitor. Keep the private state directory for a later reinstall. Keep it out of source control.
