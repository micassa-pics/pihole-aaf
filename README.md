# Pi-hole Awesome-a-fyer

Unofficial web interface patches for Pi-hole v6. Manage DHCP reservations from the leases table and group repeated requests in the Query Log.

<a name="query-log"></a>

[awesome-a-fyer the dhcp page](#awesome-a-fyer-the-dhcp-page) · [awesome-a-fyer the queries page](queries.md)

**[Install with the copyable prompt](prompts/install.md)** · **[Undo with the copyable prompt](prompts/undo.md)** · **[Browse the patches](patches/README.md)**

Open the install page, copy the full prompt, and paste it into your LLM. It asks for your Pi-hole address and SSH details, fetches the two patch files, and checks them against your installed web interface. The undo page works the same way.

<a name="dhcp"></a>

## awesome-a-fyer the dhcp page

![DHCP Settings in Expert mode with all five sections collapsed](assets/dhcp-sections-collapsed.png)

- Open the page in Expert mode. Toggle each settings or lease section by its heading.
- Search, sort, and page through static reservations by IP address, hostname, or MAC address.
- Use **+** beside an eligible active lease to open an editable reservation draft. Select the checkmark to stage it for **Save & Apply**, or the curved arrow to cancel. The eye opens queries for that client.
- Confirm lease deletions and expand **Manual Edit Static DHCP Entries** for advanced configurations.

![Six active DHCP leases. The bottom three have a plus button between the trash and eye icons.](assets/active-dhcp-leases.png)

The top three devices already have static reservations. For any of the bottom three, select **+** to review and edit a new reservation.

![Static DHCP reservations with IP address, hostname, MAC address, and controls for adding or deleting a reservation](assets/static-dhcp-reservations.png)

*Both tables use fictional device names and network addresses.*

## Compatibility

The installer checks the actual web files before applying either patch. Run that check again after a Pi-hole update. The install prompt covers native systems, system containers, Docker or Podman, and managed deployments.

Pi-hole and its web interface are maintained by the [Pi-hole project](https://github.com/pi-hole/web).
