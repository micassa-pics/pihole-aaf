# DNS service blocklists

Choose the individual services you want to block in Pi-hole or display in Logstalgia.

## Pi-hole

1. Open **Lists** in your Pi-hole v6 admin page.
2. Copy the **Pi-hole list** link for a service. Add the URL as a blocklist.
3. Assign the list to the intended groups. Update Gravity to load it.

The lists include exact hostnames and rules that match the named domain and its subdomains.
To use the optional regex rules, add each non-comment line in **Domains** as a regex deny rule.
Assign the rule to the intended groups. Gravity does not import these patterns from subscription URLs.

## Logstalgia

Select the services you want to see under **DNS service filters**. Clear the selection to show all calls.
Custom wildcard and regex rules work in Logstalgia. The filters affect the display only.

The [JSON catalog](service-domains.json) includes the full rules.
Plain domains include subdomains. Prefix a hostname with `=` for an exact match.
Use `*` and `?` as wildcards. Use `/pattern/` for a regular expression.

To refresh the catalog, run this on the Logstalgia host.

```sh
python3 -B /opt/docker/stacks/dns-visualizer/service_filters.py --refresh
```

Shared domains can match traffic from several services. The Google list includes YouTube and Google Cloud.

## Social & web

| Service | Subscription | Optional regex rules |
| --- | --- | --- |
| Facebook | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/facebook.txt) |  |
| Instagram | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/instagram.txt) |  |
| X / Twitter | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/twitter.txt) |  |
| TikTok | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/tiktok.txt) |  |
| Snapchat | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/snapchat.txt) |  |
| Threads | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/threads.txt) |  |
| Reddit | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/reddit.txt) |  |
| Pinterest | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/pinterest.txt) |  |
| LinkedIn | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/linkedin.txt) |  |
| Tumblr | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/tumblr.txt) |  |
| Bluesky | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/bluesky.txt) |  |
| Discord | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/discord.txt) |  |
| Mastodon | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/mastodon.txt) |  |
| VK | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/vk.txt) |  |
| Weibo | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/weibo.txt) |  |
| WhatsApp | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/whatsapp.txt) |  |
| Google | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/google.txt) |  |

## Gaming

| Service | Subscription | Optional regex rules |
| --- | --- | --- |
| Roblox | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/roblox.txt) |  |
| PlayStation | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/playstation.txt) |  |
| Nintendo | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/nintendo.txt) |  |
| Xbox | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/xbox.txt) |  |
| Steam | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/steam.txt) |  |
| Epic Games / Fortnite | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/epicgames.txt) | [Regex rules](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/regex/epicgames.txt) |
| Minecraft | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/minecraft.txt) |  |
| Riot Games | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/riot.txt) |  |
| Activision Blizzard / Battle.net | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/blizzard.txt) |  |
| EA | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/ea.txt) |  |
| Ubisoft | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/ubisoft.txt) | [Regex rules](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/regex/ubisoft.txt) |
| Rockstar Games | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/rockstar.txt) |  |

## Video streaming

| Service | Subscription | Optional regex rules |
| --- | --- | --- |
| YouTube | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/youtube.txt) |  |
| Vimeo | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/vimeo.txt) | [Regex rules](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/regex/vimeo.txt) |
| Netflix | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/netflix.txt) | [Regex rules](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/regex/netflix.txt) |
| Prime Video | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/primevideo.txt) |  |
| Disney+ | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/disneyplus.txt) |  |
| Hulu | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/hulu.txt) |  |
| HBO Max | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/hbomax.txt) |  |
| Apple TV | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/appletv.txt) |  |
| Twitch | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/twitch.txt) |  |
| Peacock | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/peacock.txt) |  |
| Paramount+ | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/paramountplus.txt) |  |
| Crunchyroll | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/crunchyroll.txt) |  |
| Dailymotion | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/dailymotion.txt) |  |
| Pluto TV | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/plutotv.txt) |  |
| Tubi | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/tubi.txt) |  |
| Crave | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/crave.txt) |  |
| CBC Gem | [Pi-hole list](https://raw.githubusercontent.com/micassa-apps/pihole-aaf/main/blocklists/lists/cbcgem.txt) |  |

## Sources and maintenance

The presets use the MIT-licensed [V2Fly domain lists](https://github.com/v2fly/domain-list-community/tree/99b3169c537639873b56499d3412232b52b6b59b/data), DNS aliases, and published service documentation. See the [upstream license](service-domains-LICENSE.txt).

After editing the catalog, run `python3 blocklists/generate.py` from the repository root.
Run `python3 blocklists/generate.py --check` to check the generated files.
