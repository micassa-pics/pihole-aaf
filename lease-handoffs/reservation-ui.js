/* Loaded into the DHCP page by the reservation guard patch. */
let reservationVersions = {};
let reservationLocks = {};
let reservationAttempt;
let guardPoll;

async function guardCall(body) {
  try {
    return await $.ajax({
      url: document.body.dataset.webhome + "reservation-guard",
      method: "POST", contentType: "application/json", dataType: "json",
      headers: { "X-Reservation-Guard": "1" }, data: JSON.stringify(body),
    });
  } catch (error) {
    throw new Error(error.responseJSON?.error || "Reservation service unavailable. Refresh to check the save.");
  }
}

function guardId() {
  return Array.from(crypto.getRandomValues(new Uint8Array(16)), b => b.toString(16).padStart(2, "0")).join("");
}

function moveLabel(move) {
  if (move.kind === "review") return "Reservation changed outside this editor. Review required.";
  if (move.kind === "lease") return "Waiting for this device to lease " + move.ip + ".";
  return "Recording address history for " + move.ip + ".";
}

function guardStatus(view) {
  reservationLocks = view.locks;
  let panel = $("#reservation-moves");
  if (!panel.length) panel = $('<div id="reservation-moves" aria-live="polite">').insertBefore("#StaticDHCPTable");
  panel.empty();
  if (view.checkpointReady === false) {
    $("<p>").text("Lease history checkpoint is unavailable. Reservation moves are paused.").appendTo(panel);
  }
  for (const [key, move] of Object.entries(view.locks)) {
    const label = key === "order" ? "Reservation order" : move.ip || key;
    const row = $("<p>").text(label + " · " + moveLabel(move) + " ").appendTo(panel);
    if (move.recovery) {
      const details = $("<details>").appendTo(panel);
      $("<summary>").text("Show previous and requested rules").appendTo(details);
      $("<pre>").text("Previous rules\n" + move.recovery.before.join("\n") +
        "\n\nRequested rules\n" + move.recovery.requested.join("\n")).appendTo(details);
    }
    if (move.waitOnly) continue;
    const review = move.kind === "review";
    $('<button type="button" class="btn btn-default btn-xs">').text(review ? "Review change" : "Cancel move")
      .appendTo(row).on("click", async () => {
        const lines = view.hosts.filter(line => line.toLowerCase().split(",").map(x => x.trim()).includes(key));
        const prompt = review ? "Keep the current rules and clear this review?" : "Cancel this move and restore the previous reservation?";
        if (!confirm(prompt + "\n" + (lines.join("\n") || key))) return;
        await withDHCPSave(async () => {
          const response = await guardCall({action: review ? "review" : "cancel", key, versions:view.versions, id:guardId()});
          adoptReservations(response);
        });
      });
  }
  $("#StaticDHCPTable tr[data-original-line]").each(function () {
    const key = this.dataset.originalLine.toLowerCase().split(",").map(x => x.trim()).find(x => x in view.locks);
    $(this).find(".reservation-status").remove();
    if (key) $("<span class='reservation-status fa fa-lock'>").attr({"title":moveLabel(view.locks[key]),"aria-label":moveLabel(view.locks[key])}).prependTo($(this).find(".actions"));
  });
}

function adoptReservations(view) {
  reservationVersions = view.versions;
  const field = document.getElementById("dhcp-hosts");
  savedDHCPValues?.set(field, view.hosts.join("\n"));
  displayHosts(visibleHosts(view.hosts, pendingHostDeletes));
  guardStatus(view);
}

function preserveReservationDraft(before, after) {
  const draft = [...visibleHosts(before, after).map(line => "Remove: " + line),
    ...visibleHosts(after, before).map(line => "Add: " + line)].join("\n");
  if (!draft) return;
  let field = $("#reservation-conflict-draft");
  if (!field.length) {
    const label = $('<label for="reservation-conflict-draft">Your unsaved reservation changes</label>');
    field = $('<textarea id="reservation-conflict-draft" class="form-control" rows="3" readonly>');
    $("#StaticDHCPTable").before(label, field);
  }
  field.val(draft);
}

async function guardedSave(before, after) {
  const request = {action:"save", before, after, versions:reservationVersions};
  const signature = JSON.stringify(request);
  if (reservationAttempt?.signature !== signature)
    reservationAttempt = {signature, id:guardId()};
  try {
    const view = await guardCall({...request,id:reservationAttempt.id});
    reservationAttempt = undefined;
    reservationVersions = view.versions;
    after.splice(0, after.length, ...view.hosts);
    guardStatus(view);
  } catch (error) {
    let latest;
    try { latest = await guardCall({action:"status", id:reservationAttempt.id}); } catch { /* Service unavailable. */ }
    if (latest?.outcome === "saved") {
      reservationAttempt = undefined;
      reservationVersions = latest.versions;
      after.splice(0, after.length, ...latest.hosts);
      guardStatus(latest);
      return;
    }
    preserveReservationDraft(before, after);
    if (latest) adoptReservations(latest);
    throw error;
  }
}

function pollReservationMoves() {
  clearTimeout(guardPoll);
  guardPoll = setTimeout(async () => {
    try {
      if (!document.hidden && !savingDHCP && !document.querySelector("#reservation-moves details[open]")) {
        guardStatus(await guardCall({action:"read"}));
      }
    } catch { /* The next save always checks the server again. */ }
    pollReservationMoves();
  }, 15000);
}

