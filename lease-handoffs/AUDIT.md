# Address handoff audit

## Reservation guard follow-up

The optional server-side writer replaces the browser-only edit check described below. Two independent browser sessions submitted competing IPs for one disposable reservation on an OpenWrt Docker deployment. One save succeeded. The other received a conflict. The winning request ID could be retried. The monitor released the static move and the original 32 reservations were restored. A separate fixture counted exactly one upstream PATCH across both saves and the retry. A browser test verified that a rejected edit preserved its draft and refreshed its baseline.

The Docker entrypoint resets ownership and modes inside its config volume. The guarded install keeps the journal, checkpoint, socket directory and publication directory outside that volume. Pi-hole receives a read-only mount of the published view. The proxy receives the socket directory. The live checks covered container recreation, DNS, and writer access. Direct API clients and pages left open from before the upgrade can still bypass the writer.

The audit started at commit `255304b`. It covered Pi-hole Web v6.6.1 on Docker with an OpenWrt host. Live checks used reads. Browser tests intercepted reservation writes. The deployment updated the monitor and web files.

| Finding | Correction and verification |
| --- | --- |
| The DHCP page resolved the monitor URL under `settings/` and received a 404. An earlier smoke test passed with an empty chart map. | Both pages use Pi-hole's web root. The live DHCP page loaded 29 client series. Twenty-four contained activity. A simulated monitor outage kept the native IP charts visible with a notice. |
| A new reservation could show an earlier occupant's queries at the same IP. Retargeting a pending move through the API could also clear its pending state. | The worker checks observed owners and conflicting leases. Regression tests cover address reuse, retargeting, and confirmation by MAC. |
| Pending reservations could block their own deletion. | A fresh checkpoint permits cancellation. A browser test used a real pending checkpoint and intercepted the writes. An address edit was blocked and cancellation succeeded. |
| The worker synced the file before rename but did not sync the directory. Two workers could write the same state. | The worker syncs file permissions, content, and the directory entry. It holds an exclusive lock. On the router, process exits immediately before and after rename left complete checkpoints. A second lock attempt failed. |
| A future checkpoint could report an age of zero. An empty response could pass as a valid map. An ungrouped read could fetch the entire retained history by default. | The reader requires a current heartbeat. The default ungrouped handoff window covers 24 hours. An explicit start time selects a longer range. |

## Other checks

- A later guard test used eight independent HTTP clients with one starting revision. One save succeeded, seven received conflicts, and retrying the winning request left the upstream write count at one. A local API fixture checked missing sessions, CSRF rejection, and the guard's origin and header checks. The passwordless LAN deployment was verified separately.
- Regression coverage includes DHCP disabled, duplicate IP repair, denied writes and a monitor outage during deletion. The guard uses the monitor's copy of the configured rules to distinguish a recorded rule from an observed DHCP lease.

- Eight worker tests passed. They cover expiry, address reuse, ambiguous leases, the on-disk lease format, retention, clock rollback, a saved-state reload, and successive static moves.
- The web patch applied, reversed, and reapplied against the stock Web v6.6.1 files with the published DHCP and Query Log patches. Both modified scripts passed the JavaScript syntax check.
- A simulated completed handoff used live DNS data. The raw API count, grouped chart bins, and unique individual rows all returned 76 queries for the same ten-minute window.
- The live worker resumed from its checkpoint. The old indexer was inactive. The persistent override archive and the running web files matched at inspection.

## Limits

- The browser's read and write are separate requests. Two tabs can race. The API and direct config edits can bypass the guard.
- A reservation is weaker evidence than a lease. A device with a manually assigned address can use someone else's reserved IP. Sampling every 15 seconds can miss brief changes. The monitor cannot reconstruct ownership before its first observation.
- DHCP charts omit ten-minute buckets that cross an ownership boundary. Their totals can differ from the timestamp-based Query Log.
- The monitor replaces two files every 15 seconds. This creates 11,520 file replacements per day. Filesystem journaling adds storage writes. A corrupt checkpoint requires recovery from backup. Keep a persistent state directory.
- A fresh Query Log page with no eligible address interval can leave the advanced date picker uninitialized. Large explicit date ranges collect matching rows in the browser and can take time.
- The test covered a process exit on Linux. It did not include physical power loss, a router reboot, or a new systemd installation. The two live devices selected for the renewal check still held their old leases. Their completed renewals were simulated.
