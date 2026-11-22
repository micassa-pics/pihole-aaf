# awesome-a-fyer the queries page

Open **Query Log** from the Pi-hole sidebar. If you also use the DHCP patch, select the eye beside a lease to see that client's queries.

## Group repeated queries

Drag a Query Log header to move its column. Your browser remembers the layout for both individual and grouped queries.

When you filter by one IP, **Recent Queries** shows the hostname or the IP in bold. Edit the field to filter by another hostname or IP. Select **Apply** or press **Enter**. Select **Cancel** or press **Esc** to discard the edit.

The Query Log opens in grouped view by default. Select **Ungroup** to see individual requests. Reload the page to return to grouped view. In grouped view, each row combines requests with the same domain, query type, and client IP. **Count** replaces reply time. It includes matching requests from all pages of the filtered results.

By default, **Group** shows the last 24 hours, with one bar per hour. Select a time range to chart that range in 24 equal intervals. The oldest interval is on the left. For a six-hour range, each bar covers 15 minutes. An empty slot means zero queries. Select the chart to read the count for each UTC interval. Start with a short range for large logs. The status shows how many queries Pi-hole has loaded.

![Grouped Recent Queries sorted by Count. The Time chart for calendar.example shows steady activity. The chart for maps.example shows two short bursts.](assets/grouped-query-log.jpg)

In this fictional example, `maple-tablet.test` sent 240 A queries for `calendar.example` across the selected range. The 24 interval counts add up to 240. The next row shows the same client's 185 AAAA queries. Each chart scales to its own busiest interval. Use **Count** to compare totals across rows.

## Filter and inspect results

- Select the button beside **Group** or **Ungroup** to cycle through **All**, **Blocked**, and **Allowed**. Your client filter stays active.
- **Mixed** means the queries had different statuses or CNAME targets. These rows have no **Allow** or **Deny** button. Select **Ungroup** to see the action for each request.
- Select **Refresh** to include newer requests.
- Select **Ungroup** to see individual requests and their reply times.

To install the Query Log patch alone, choose **Query Log** in the [shared prompt](prompts/manage.md). Then choose **Install/update**.

[Query Log patch](patches/pihole-query-log-grouping.patch) · [Back to the README](README.md)
