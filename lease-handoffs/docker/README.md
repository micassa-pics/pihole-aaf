# Run handoffs inside Pi-hole

The monitor, reservation writer, and web proxy run beside FTL in one container. The monitor reads leases and reservations. The writer serializes edits. Each process runs with a non-root identity. The monitor and writer have separate filesystem roots. The guard uses the Pi-hole API on loopback.

1. Use the repository root as the build context. Set `PIHOLE_IMAGE` to the exact tested upstream tag or digest. The Dockerfile applies the DHCP, Query Log, handoff, and guard patches. Preserve other selected page patches in the same image. Include any site-specific overrides in a private final layer. Check that they match the expected versions.

   ```sh
   docker build -f lease-handoffs/docker/Dockerfile \
     --build-arg PIHOLE_IMAGE="$PIHOLE_IMAGE" -t local/pihole-handoffs:tested .
   ```

2. Keep your current Pi-hole network, capabilities, config and gravity volumes. Set `FTLCONF_webserver_port` to `127.0.0.1:8080`. Set `HANDOFF_ORIGINS` to a space-separated list of exact external admin origins. Give the proxy read access to its configuration. Use `error_log stderr warn;` for Docker logs. Supply your existing Nginx server configuration at `/etc/nginx/nginx.conf`. Preserve the LAN and TLS rules. Include `/etc/nginx/guard.location` in the same server block. Send ordinary requests to the loopback listener. Run Nginx in the foreground with its PID and temporary files in a directory writable by UID 64322. Check that the container permits this UID to bind the admin port.
3. Give the state directory to the dedicated helper UID (default 64321) and the Pi-hole group (default 1000). Use mode 0700. Within it, create `published` and `ipc` with the same owner and mode 0750. Mount the same state directory at both helper paths. Supply the config to the monitor read-only. Keep these mounts in the Pi-hole service.

```yaml
volumes:
  - ${HANDOFF_STATE}:/opt/guard/state
  - ${HANDOFF_STATE}:/opt/monitor/state
  - ${PIHOLE_CONFIG}:/opt/monitor/config:ro
  - ${HANDOFF_STATE}/published:/run/pihole-lease-handoffs:ro
  - ${HANDOFF_STATE}/ipc:/run/reservation-guard:ro
```

4. Test the image with private copies of the config and state. Before cutover, record the current reservations and pending moves. Stop the old writer and monitor. Back up their state and SQLite journal together. Stop the old proxy. Replace the Pi-hole service with the derived image and its entrypoint.
5. Check DNS, the admin page, LAN access rules, a guard read and the checkpoint timestamp. Compare reservations and pending moves. Restart the container and repeat the checks. Disable old startup jobs after the checks pass.
6. To roll back, stop the new container first. Restore the previous Compose file, image and services. Use the latest consistent state. Restore an older state backup only after reconciling any writes since that backup.
