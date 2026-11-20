# Pi-hole Awesome-a-fyer

Unofficial web interface patches for Pi-hole v6. Manage DHCP reservations from the leases table and group repeated requests in the Query Log.

**[Install with the copyable prompt](prompts/install.md)** · **[Undo with the copyable prompt](prompts/undo.md)** · **[Browse the patches](patches/README.md)**

Open the install page, copy the full prompt, and paste it into your LLM. It asks for your Pi-hole address and SSH details, fetches the two patch files, and checks them against your installed web interface. The undo page works the same way.

## DHCP

- Open the page in Expert mode. Toggle each settings or lease section by its heading.
- Search, sort, and page through static reservations by IP address, hostname, or MAC address.
- Use **+** beside an eligible active lease to open an editable reservation draft. **Confirm** stages it for **Save & Apply**. The eye opens queries for that client.
- Confirm lease deletions and expand **Manual Edit Static DHCP Entries** for advanced configurations.

![Example active DHCP leases table showing IP addresses, hostnames, expiration times, and per-client actions](assets/active-dhcp-leases.png)

*Illustrative view with fictional device names, addresses, and lease data.*

## Query Log

Choose **Group** to combine requests with the same domain, query type, and client IP across result pages. **Count** replaces reply time. The button beside **Group** cycles through **All**, **Blocked**, and **Allowed**.

## Compatibility

The installer checks the actual web files before applying either patch. Run that check again after a Pi-hole update. The install prompt covers native systems, system containers, Docker or Podman, and managed deployments.

Pi-hole and its web interface are maintained by the [Pi-hole project](https://github.com/pi-hole/web).
