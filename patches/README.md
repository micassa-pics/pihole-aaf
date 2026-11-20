# Patch files

| Patch | Files changed | Download |
| --- | --- | --- |
| [Dashboard headings and counts](pihole-dashboard.patch) | `index.lp`, `scripts/js/index.js`, `scripts/lua/sidebar.lp` | [Raw Dashboard patch](pihole-dashboard.patch?raw=true) |
| [DHCP tables and headings](pihole-dhcp-table.patch) | `settings-dhcp.lp`, `scripts/js/settings-dhcp.js`, `scripts/js/footer.js`, `vendor/datatables/dataTables.colReorder.min.js` | [Raw DHCP patch](pihole-dhcp-table.patch?raw=true) |
| [Query Log grouping and filters](pihole-query-log-grouping.patch) | `queries.lp`, `scripts/js/queries.js`, `scripts/js/utils.js`, `vendor/datatables/queryLog.colReorder.min.js` | [Raw Query Log patch](pihole-query-log-grouping.patch?raw=true) |

Use the **Download** column to get a patch from this revision. Apply patches from the Pi-hole web interface directory.

The shared prompt uses one Git commit for each run. It records each patch's hash so you can identify the installed version later.

[Copyable prompt](../prompts/manage.md) · [Back to the README](../README.md)

## Stock verification

Version 1.1.0 of both patches was verified against Pi-hole Web v6.6.1 at commit `fb699c4e3fd6965d1c9a5253250d8a9b3c6f7a0e`. The checks covered each patch alone, both installation and removal orders, and upgrading from the previous published patches. Reversing the patches restored the original file contents.

For a new patch release, update its sidebar version and its published version in [the update checker](../docs/check.html) together. Dashboard registers its version in `scripts/lua/sidebar.lp`. DHCP registers its version in `scripts/js/footer.js`. Query Log registers its version in `scripts/js/utils.js`. GitHub Pages serves the checker from `main/docs`.
