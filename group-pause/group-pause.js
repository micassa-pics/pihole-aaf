/* Group scope for the existing Pi-hole Disable Blocking menu. */
(() => {
  const menu = document.querySelector("#pihole-disable");
  if (!menu) return;
  const prefix = "awesome-a-fyer-pause-";
  const endpoint = document.body.dataset.apiurl + "/groups";
  const box = document.createElement("li");
  box.style.padding = "5px 10px 5px 18px";
  box.innerHTML = '<fieldset><legend style="font-size:inherit;color:inherit;margin-bottom:4px">Apply to</legend>' +
    '<label><input class="no-icheck" type="checkbox" checked> All devices</label><div></div></fieldset>' +
    '<small role="status" aria-live="polite"></small>';
  menu.querySelector("ul").prepend(box);
  const all = box.querySelector("input");
  const list = box.querySelector("fieldset div");
  const status = box.querySelector("small");
  let busy = false;
  let sequence = 0;
  const selected = new Map();
  const getGroups = async () => (await $.getJSON(endpoint)).groups;
  async function refresh() {
    const seq = ++sequence;
    try {
      const groups = await getGroups();
      if (seq !== sequence) return;
      list.replaceChildren();
      for (const group of groups.filter(g => !g.name.startsWith(prefix))) {
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
      selected.clear();
      list.querySelectorAll("input").forEach(input => { input.checked = false; });
    }
  });
  menu.querySelector(":scope > a").addEventListener("click", refresh);
  async function pause(seconds) {
    if (busy) return;
    if (!selected.size) { status.textContent = "Select a group or All devices first."; return; }
    if (!Number.isSafeInteger(seconds) || seconds < 0 || seconds > 2147483647) {
      status.textContent = "Enter a valid duration."; return;
    }
    busy = true;
    box.querySelector("fieldset").disabled = true;
    const targets = Array.from(selected, ([id, name]) => ({ id, name }));
    const token = Array.from(crypto.getRandomValues(new Uint8Array(16)), n => n.toString(16).padStart(2, "0")).join("");
    const request = prefix + token;
    try {
      status.textContent = "Starting group pause…";
      const response = await $.ajax({ url: endpoint, method: "POST", contentType: "application/json",
        data: JSON.stringify({ name: [request], enabled: false, comment: JSON.stringify({ seconds, groups: targets }) }) });
      if (response.processed?.errors?.length) throw Error("Pi-hole rejected the request.");
      for (let i = 0; i < 16; i++) {
        await new Promise(resolve => setTimeout(resolve, 500));
        const groups = await getGroups();
        if (groups.some(g => g.name === request)) continue;
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
