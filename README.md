# Pi-hole awesome-a-fyer

Two optional patches for the Pi-hole v6 web interface. Install either page or both.

## Install, update, or undo

- Paste the [setup prompt](prompts/manage.md) into your AI assistant.
- Choose the pages and action. Enter your Pi-hole address and SSH command.
- After a Pi-hole update, run **Check only** to see if you need to reapply the patches.

<a name="query-log"></a>

## awesome-a-fyer the queries page

- Group requests by client, domain, and query type.
- Sort by count. See when requests occurred across 24 bars.
- Switch between **All**, **Blocked**, and **Allowed**. Keep the current client filter.
- **Reorderable columns.** Drag a header to move it. Your browser remembers the order.

[![Query Log before and after.](assets/queries-comparison.svg)](https://micassa-pics.github.io/pihole-awesome-a-fyer/#queries)

[Query Log guide](queries.md)

<a name="dhcp"></a>

## awesome-a-fyer the dhcp page

- Select the eye beside a device to open its Query Log.
- See active leases and static reservations in separate tables. Collapse any section.
- Select **+** beside a lease. Edit the **New** row at the top of the static table. Select the checkmark to save.
- Edit hostnames and groups in place. Use **Save & Apply** only for deletions.
- Check lease time remaining and DNS activity for the past 24 hours.
- **Reorderable columns.** Drag a header to move it. Your browser remembers the order.

[![DHCP before and after.](assets/dhcp-comparison.svg)](https://micassa-pics.github.io/pihole-awesome-a-fyer/#dhcp)

[DHCP guide](dhcp.md)
