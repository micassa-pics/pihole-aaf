# Pi-hole awesome-a-fyer

This project provides two independent patches for the Pi-hole v6 web interface. You can install either patch or both.

| Page | What you can do |
| --- | --- |
| [Query Log](#awesome-a-fyer-the-queries-page) | Group repeated DNS queries and count requests from each client. |
| [DHCP](#awesome-a-fyer-the-dhcp-page) | Tidy the DHCP page with collapsible boxes, and added functionality |

## Get started

1. Copy the entire block from the [shared prompt](prompts/manage.md).
2. Paste it into your AI assistant.
3. Choose **DHCP**, **Query Log**, or **both**.
4. Choose an action from the table below.
5. Give the assistant your Pi-hole Admin URL and your usual SSH command or alias.

| Action | Result |
| --- | --- |
| **Check only** | Compares installed patches with GitHub. Leaves live files intact. |
| **Install/update** | Installs missing patches and updates older ones. Skips current patches. |
| **Undo** | Removes the installed patch from each selected page. |

<a name="query-log"></a>

## awesome-a-fyer the queries page


### Group repeated queries

On the queries page, at the top you can select **Group** and **Type**. Each row combines requests with the same domain, query type, and client IP. **Count** replaces reply time. It includes matching requests from all pages of the filtered results.

The **Time** column shows one bar per hour. Earlier hours appear on the left. Gaps mean zero queries. Each row uses its busiest hour as its scale. Hover over a bar for the hour in UTC and its query count.

![Grouped Recent Queries with the All filter active. The Count column shows the largest groups first.](assets/grouped-query-log.jpg)

In this example, one client sent 240 A queries and 185 AAAA queries for `calendar.example`. Each query type has its own row. The example uses fictional data.

### Filter and inspect results

- Select the button beside **Group** or **Ungroup** to cycle through **All**, **Blocked**, and **Allowed**. Your client filter stays active.
- Select a group to inspect its latest query. **Mixed** means the queries in that group had different results.
- Select **Refresh** to include newer requests.
- Select **Ungroup** to see individual requests and their reply times.

To install the Query Log patch alone, choose **Query Log** in the [shared prompt](prompts/manage.md). Then choose **Install/update**.

[Query Log patch](patches/pihole-query-log-grouping.patch) · [Standalone Query Log guide](queries.md)

<a name="dhcp"></a>

## awesome-a-fyer the dhcp page


The DHCP page opens in Expert mode. Select a section heading to expand or collapse it.

![DHCP Settings with all five sections collapsed](assets/dhcp-sections-collapsed.jpg)

Select the eye beside an active lease or static reservation to see queries from that IP address.

### Create a static reservation


1. Find the device under **Currently active DHCP leases**.
2. Select **+** to the right of the eye. A draft opens at the bottom of **Static DHCP configuration**.
3. Edit the draft. Select the checkmark to confirm it or the curved arrow to cancel it.
4. Select **Save & Apply** to save the confirmed reservation.

In this example, the top three devices already have reservations. The bottom three have a **+** button.


![Active DHCP leases. The bottom three leases can be added to the static list.](assets/active-dhcp-leases.jpg)

Search or sort static reservations by IP address, hostname, or MAC address. To edit the entries as text, open **Manual Edit Static DHCP Entries**. Pi-hole asks for confirmation when you delete a lease or reservation.

![Static DHCP configuration with IP address, hostname, MAC address, and action columns](assets/static-dhcp-reservations.jpg)



## Compatibility

The prompt covers native installations, system containers, Docker, Podman, and managed deployments. After a Pi-hole update, run **Check only** again. The update can replace the patched web files.

[Browse the patches](patches/README.md) Â· [Pi-hole web interface project](https://github.com/pi-hole/web)
