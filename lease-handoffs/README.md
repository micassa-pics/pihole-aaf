# Follow a device across IPv4 address changes

This optional feature needs both the DHCP and Query Log page patches. A small Python service reads the lease file and DHCP reservations every 15 seconds. It stores address intervals in a separate directory. Pi-hole keeps each DNS query under its original source IP.

- **DHCP to static.** Save the reservation. The new address shows a waiting message until Pi-hole reports a lease at that address for the same MAC. The Query Log then includes the device's observed history at both addresses.
- **Static to static.** Change a reservation's IP. The monitor associates its previous address intervals with the new reservation. The DHCP page checks the monitor's saved checkpoint before it accepts another IP change for that MAC. Other devices remain editable.
- **Same address.** Keep the IP when you create the reservation and use the existing Query Log.

The Query Log keeps the original IP on each row. Grouping still uses domain, type, and source IP. The DHCP activity chart includes complete ten-minute buckets within the recorded intervals. A partial bucket can contain another client's traffic.

Coverage starts when the monitor observes a lease or reservation. For an offline static device, the monitor uses the configured reservation. That is weaker evidence than a DHCP lease. Changes made directly through the Pi-hole API or config file bypass the page's edit check. A change and reversal between two checks can go unseen. This feature supports one MAC and one IPv4 address per reservation. Keep one monitor per Pi-hole instance.

The edit check runs in the browser. Two administrators can read the same checkpoint and submit changes at the same time. Use one editor for address changes. If a device never takes its new address, you can delete the pending reservation from the DHCP page.

If the monitor stops, the DHCP charts show standard per-IP counts with a notice. A filtered Query Log requires a current checkpoint. The ungrouped handoff view defaults to the last 24 hours. Set a start time for older queries. A pending move has no query rows until the device takes its address.

## Install and check

1. Install the two page patches. Copy the admin web files to staging. From that directory, run the following with the path to this feature's patch.

   ```sh
   git apply --check /path/to/lease-handoffs/web.patch
   git apply /path/to/lease-handoffs/web.patch
   ```

2. Find the persistent directory that contains the live `pihole.toml` and `dhcp.leases`. Check that the effective reservations match `dhcp.hosts` in that file. Create a directory named `lease-handoffs` inside it. Set its mode to 0750. Use a dedicated non-root writer and the Pi-hole web service's group. Give the monitor read access to both input files.
3. Run `worker.py` with Python 3.11 or later. Mount the config directory read-only at `/config`. Mount its `lease-handoffs` subdirectory read-write at `/state`. The web service reads the resulting `/etc/pihole/lease-handoffs/view.txt`. Start the monitor at boot.
4. On Docker or Podman, use the example below in the deployment project. Set the host paths, numeric IDs, and approved Python image for your host. On a dedicated Linux device or VM, use the included systemd service. Adjust its paths and IDs first. On an OpenWrt Docker host, the same sidecar can run alongside Pi-hole.

   ```yaml
   services:
     lease-handoffs:
       image: ${HANDOFF_PYTHON_IMAGE}
       user: "${HANDOFF_UID}:${PIHOLE_GID}"
       network_mode: none
       read_only: true
       cap_drop: [ALL]
       security_opt: ["no-new-privileges:true"]
       volumes:
         - ${PIHOLE_CONFIG}:/config:ro
         - ${PIHOLE_CONFIG}/lease-handoffs:/state:rw
         - ${HANDOFF_CODE}/worker.py:/app/worker.py:ro
       command: ["python3", "-IB", "/app/worker.py"]
       restart: unless-stopped
   ```

5. Verify that `view.txt` updates. Deploy the staged web patch using the same persistent webroot or image as the base patches. Open a filtered Query Log. Check that an ordinary address still loads. For a pending move, check the waiting message and the MAC on the next DHCP lease. The monitor keeps up to 91 days of intervals. Pi-hole controls query retention.

## Update or undo

Keep the exact feature patch and the base patch revisions with the install record. Reverse the feature patch in staging before you change either base patch. Reapply the matching feature patch after the base update. If any check fails, keep the installed files in place.

```sh
git apply --reverse --check /path/to/installed/lease-handoffs/web.patch
git apply --reverse /path/to/installed/lease-handoffs/web.patch
```

Deploy the restored web files. Remove the added `lease-handoffs.lp` endpoint. Stop and disable the monitor. The private state directory can stay in place for a later reinstall. Keep it out of source control.
