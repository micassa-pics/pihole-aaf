"""Check that the published history view has a matching private checkpoint."""

from pathlib import Path
import time

from checkpoint import read_committed

try:
    state = read_committed(Path("/state"), Path("/state/published/view.txt"))
    if state.get("checkpoint_format") != 1 or not 0 <= time.time() - state["last"] <= 30:
        raise ValueError("Checkpoint is stale or still starting")
except (OSError, ValueError, KeyError, TypeError):
    raise SystemExit("Pi-hole handoffs: no current committed checkpoint")
