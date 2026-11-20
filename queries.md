# awesome-a-fyer the queries page

Open **Query Log** in Pi-hole, or select the eye beside an active DHCP lease to see requests from that client.

- **Group** combines requests with the same domain, query type, and client IP across all pages of the filtered results. **Count** replaces reply time and shows how many requests each row represents.
- The button beside **Group** cycles through **All**, **Blocked**, and **Allowed**. It works in both views and keeps the selected client filter.
- Select a grouped row to inspect its latest matching query. **Mixed** means the requests in that group had different results.
- Select **Refresh** to include newer requests, or **Ungroup** to return to individual requests and their reply times.

[Query Log patch](patches/pihole-query-log-grouping.patch) · [Install prompt for both patches](prompts/install.md) · [Back to the README](README.md)
