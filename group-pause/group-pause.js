/* Group scope for the existing Pi-hole Disable Blocking menu. */
(() => {
  const menu = document.querySelector("#pihole-disable");
  if (!menu) return;
  const prefix = "awesome-a-fyer-pause-";
  const devicePrefix = "awesome-a-fyer-device-";
  const endpoint = document.body.dataset.apiurl + "/groups";
  const box = document.createElement("li");
  box.style.padding = "5px 10px 5px 18px";
  box.innerHTML = '<fieldset><legend style="font-size:inherit;color:inherit;margin-bottom:4px">Apply to</legend>' +
    '<label><input class="no-icheck" type="checkbox" checked> All devices</label><div></div><label style="display:block" for="pause-one-device">One device</label><select id="pause-one-device" class="form-control input-sm" style="width:100%;min-width:0"><option value="">Select an IP address</option></select><button type="button" hidden>Resume this IP</button></fieldset>' +
    '<small role="status" aria-live="polite"></small>';
  menu.querySelector("ul").prepend(box);
  const all = box.querySelector("input");
  const list = box.querySelector("fieldset div");
  const device = box.querySelector("select");
  function deviceLabel(item) {
    if (!item.id) return item.text;
    const label = $("<span>").css({ display: "block", lineHeight: "1.4" });
    const lines = [item.id + ":", item.element.dataset.hostname];
    if (item.element.dataset.paused === "true") lines[1] = [lines[1], "(paused)"].filter(Boolean).join(" ");
    for (const line of lines.filter(Boolean)) {
      $("<span>").text(line).attr("title", line).css({
        display: "block", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
      }).appendTo(label);
    }
    return label;
  }
  $(device).select2({ width: "100%", minimumResultsForSearch: Infinity,
    templateResult: deviceLabel, templateSelection: deviceLabel });
  $(device).next(".select2-container").find(".select2-selection").css({ height: "auto", minHeight: "30px" });
  const resume = box.querySelector("button");
  let paused = new Set();
  const status = box.querySelector("small");
  let busy = false;
  let sequence = 0;
  const selected = new Map();
  const getGroups = async () => (await $.getJSON(endpoint)).groups;
  function address(value) {
    if (typeof value !== "string") return "";
    const host = value.trim();
    const ip = host.replace(host.includes(":") ? /\/128$/ : /\/32$/, "").replace(/^\[|\]$/g, "");
    if (/^\d{1,3}(\.\d{1,3}){3}$/.test(ip) && ip.split(".").every(o => Number(o) <= 255)) return ip.split(".").map(Number).join(".");
    if (!ip.includes(":") || !/^[a-f\d:.]+$/i.test(ip)) return "";
    try { return new URL("http://[" + ip + "]/").hostname.slice(1, -1); } catch { return ""; }
  }
  function sortKey(ip) {
    if (!ip.includes(":")) return "4" + ip.split(".").map(n => n.padStart(3, "0")).join("");
    const [left, right] = ip.split("::").map(side => side ? side.split(":") : []);
    const parts = right ? [...left, ...Array(8 - left.length - right.length).fill("0"), ...right] : left;
    return "6" + parts.map(n => n.padStart(4, "0")).join("");
  }
  async function loadDevices(seq) {
    const api = document.body.dataset.apiurl;
    const results = await Promise.allSettled([
      $.getJSON(api + "/network/devices", { max_devices: 65535, max_addresses: 256 }),
      $.getJSON(api + "/dhcp/leases"), $.getJSON(api + "/config/dhcp/hosts"), $.getJSON(api + "/clients"),
    ]);
    if (seq !== sequence) return;
    const [network, leases, config, clients] = results.map(r => r.value || {});
    const names = new Map();
    function add(raw, name) {
      const ip = address(raw);
      // Keep an existing pause reachable until the user resumes it.
      if ((ip === "::1" || ip.startsWith("127.")) && !paused.has(ip)) return;
      if (ip && !names.get(ip)) names.set(ip, name && name !== "*" ? name : "");
    }
    for (const d of network.devices || []) for (const entry of d.ips || []) add(entry.ip, entry.name);
    for (const lease of leases.leases || []) add(lease.ip, lease.name);
    for (const rule of config.config?.dhcp?.hosts || []) {
      const fields = rule.split(",").map(v => v.trim());
      const name = fields.find(v => /^[a-z_][\w.-]*$/i.test(v) && !["ignore","infinite"].includes(v));
      for (const field of fields) add(field, name);
    }
    for (const entry of clients.clients || []) add(entry.client);
    for (const ip of paused) add(ip);
    const previous = device.value;
    device.replaceChildren(new Option("Select an IP address", ""));
    for (const ip of [...names.keys()].sort((a,b) => sortKey(a).localeCompare(sortKey(b)))) {
      const hostname = names.get(ip);
      const option = new Option([ip + ":", hostname, paused.has(ip) ? "(paused)" : ""].filter(Boolean).join(" "), ip);
      option.dataset.hostname = hostname;
      option.dataset.paused = String(paused.has(ip));
      device.add(option);
    }
    $(device).val(names.has(previous) ? previous : "").trigger("change.select2");
    resume.hidden = !paused.has(device.value);
    if (results.every(r => r.status === "rejected")) status.textContent = "Could not load devices. Reopen this menu to retry.";
  }
  function clearGroups() {
    selected.clear();
    list.querySelectorAll("input").forEach(input => { input.checked = false; });
  }
  $(device).on("change", () => {
    if (device.value) { all.checked = false; clearGroups(); }
    resume.hidden = !paused.has(device.value);
  });
  resume.addEventListener("click", () => pause(0, true));
  async function refresh() {
    const seq = ++sequence;
    try {
      const groups = await getGroups();
      if (seq !== sequence) return;
      paused = new Set(groups.filter(g => g.name.startsWith(devicePrefix)).map(g => g.comment));
      void loadDevices(seq);
      list.replaceChildren();
      for (const group of groups.filter(g => !g.name.startsWith(prefix) && !g.name.startsWith(devicePrefix))) {
        const label = document.createElement("label");
        label.style.display = "block";
        const input = document.createElement("input");
        input.type = "checkbox";
        input.className = "no-icheck";
        input.disabled = !group.enabled;
        input.checked = selected.get(group.id) === group.name && group.enabled;
        label.append(input, document.createTextNode(" " + group.name + (group.enabled ? "" : " (disabled)")));
        list.append(label);
        input.addEventListener("change", () => {
          if (input.checked) {
            $(device).val("").trigger("change.select2");
            resume.hidden = true;
            all.checked = false;
            selected.set(group.id, group.name);
          } else selected.delete(group.id);
        });
      }
      for (const [id, name] of selected) {
        if (!groups.some(g => g.id === id && g.name === name && g.enabled)) selected.delete(id);
      }
    } catch {
      if (seq === sequence) status.textContent = "Could not load groups. Reopen this menu to retry.";
    }
  }
  all.addEventListener("change", () => {
    if (all.checked) {
      clearGroups();
      $(device).val("").trigger("change.select2");
      resume.hidden = true;
    }
  });
  menu.querySelector(":scope > a").addEventListener("click", refresh);
  async function pause(seconds, restore = false) {
    if (busy) return;
    const ip = device.value;
    if (ip && paused.has(ip) && !restore) { status.textContent = "This IP is already paused."; return; }
    if (!ip && !selected.size) { status.textContent = "Select an IP, a group, or All devices first."; return; }
    if (!Number.isSafeInteger(seconds) || seconds < 0 || seconds > 2147483647) {
      status.textContent = "Enter a valid duration."; return;
    }
    busy = true;
    box.querySelector("fieldset").disabled = true;
    device.disabled = true;
    const targets = Array.from(selected, ([id, name]) => ({ id, name }));
    const token = Array.from(crypto.getRandomValues(new Uint8Array(16)), n => n.toString(16).padStart(2, "0")).join("");
    const request = prefix + token;
    try {
      status.textContent = "Starting group pause…";
      const response = await $.ajax({ url: endpoint, method: "POST", contentType: "application/json",
        data: JSON.stringify({ name: [request], enabled: false, comment: JSON.stringify(ip ? { seconds, device: ip, resume: restore } : { seconds, groups: targets }) }) });
      if (response.processed?.errors?.length) throw Error("Pi-hole rejected the request.");
      for (let i = 0; i < 16; i++) {
        await new Promise(resolve => setTimeout(resolve, 500));
        const groups = await getGroups();
        if (groups.some(g => g.name === request)) continue;
        if (ip) {
          const marker = groups.find(g => g.name.startsWith(devicePrefix) && g.comment === ip);
          if (restore ? !!marker : marker?.name !== devicePrefix + token) throw Error("Could not confirm the change for " + ip + ".");
          status.textContent = ip + (restore ? " resumed." : seconds ? " paused for " + seconds + " seconds." : " paused indefinitely.");
          return;
        }
        if (!targets.every(t => groups.some(g => g.id === t.id && g.name === t.name && !g.enabled)))
          throw Error("The selection changed. Check the groups and try again.");
        status.textContent = targets.map(t => t.name).join(", ") + (seconds ? " paused for " + seconds + " seconds." : " paused indefinitely.");
        return;
      }
      status.textContent = "Pause unconfirmed. Check the group timer service and group status.";
    } catch (error) {
      status.textContent = error.message || "Could not confirm the group pause. Check group status.";
    } finally {
      busy = false;
      box.querySelector("fieldset").disabled = false;
      device.disabled = false;
      await refresh();
    }
  }
  // Stock presets and the custom-time dialog already call this one function.
  const changeBlocking = window.piholeChange;
  window.piholeChange = function (action, duration) {
    if (action !== "disable" || all.checked) return changeBlocking(action, duration);
    const seconds = duration === "" || duration == null ? NaN : Number(duration);
    return pause(seconds);
  };
})();
