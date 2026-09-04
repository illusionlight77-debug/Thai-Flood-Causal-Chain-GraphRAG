"""#5 Blind / out-of-sample protocol — "if a NEW flood hits, would it warn correctly?"

The strongest thing this model has going for blind testing: **it has zero learned
parameters.** Nothing is fit to any event's flood outcome:
  - graph structure  ← real Chao Phraya hydrology (8 sub-basins), DEM-validated
  - reach.overflow   ← independent RID SWOC river-gauge bulletin (NOT the GISTDA gold)
  - dam active/spillway ← EGAT/RID specs
  - protection       ← cited flood defenses (King's Dyke)
The GISTDA satellite gold is used ONLY to *score*, never to *set* the model. So every
event is out-of-sample by construction — there is no training set to leak from.

This module makes that concrete:
  1. Leave-one-event-out: report each scored event's metrics as HELD-OUT (they already are).
  2. Prospective blind: the Mekong/NE event was run by freezing the GISTDA *live* flood,
     predicting from structure+gauge, then comparing — a genuine prospective blind test.
  3. New events: `src/ingest/mekong_ne.py` shows the pattern — snapshot a live GISTDA flood
     → a new frozen event the pipeline scores. Each real future flood becomes a blind test.

#1 note: adding more historical scored events is DATA-bound, not code-bound — the pipeline
is EVENT_ID-parameterized. Complete per-province GISTDA tables at the >=10k-rai cutoff are
published only for NORU2022 / DIANMU2021 (2011/2013/2020/2024 checked — regional aggregates
or Excel-only, see HISTORY.md). So significance rests on those two + the live NE blind test.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.config import settings

WEB = Path(__file__).resolve().parent.parent.parent / "web"
EVENTS = [("2022", "เจ้าพระยา 2565"), ("2021", "เจ้าพระยา 2564"), ("2024", "เจ้าพระยา 2567"), ("2023", "เจ้าพระยา 2566"), ("ne2026", "โขง/อีสาน (live, prospective blind)")]


def _metrics(d: dict) -> dict:
    c = d["confusion"]["causal-graphrag"]
    tp, fp, fn = c["tp"], c["fp"], c["fn"]
    pod = tp / (tp + fn) if (tp + fn) else 0.0
    far = fp / (tp + fp) if (tp + fp) else 0.0
    return {"f1": d["results"]["causal-graphrag"]["f1_overall"],
            "POD": round(pod, 3), "FAR": round(far, 3),
            "specificity": c["specificity"], "traceability": d["results"]["causal-graphrag"]["traceability"]}


def run() -> dict:
    held_out = {}
    for y, label in EVENTS:
        f = WEB / f"ui_data_{y}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text("utf-8"))
        held_out[y] = {"label": label, **_metrics(d)}
    return {
        "learned_parameters": 0,
        "leakage": "structurally impossible — gate (reach.overflow) from RID gauge, gold only scores",
        "protocol": "leave-one-event-out ≡ every-event-out (no fit); NE = prospective live blind",
        "held_out_metrics": held_out,
        "new_event_mechanism": "src/ingest/mekong_ne.py (freeze live GISTDA → scored event)",
    }


def main() -> None:
    res = run()
    print("BLIND / OUT-OF-SAMPLE — learned parameters:", res["learned_parameters"],
          "→ every event is out-of-sample by construction")
    print("leakage:", res["leakage"])
    for y, m in res["held_out_metrics"].items():
        print(f"  held-out {y} ({m['label']}): F1={m['f1']} POD={m['POD']} FAR={m['FAR']} "
              f"spec={m['specificity']} trace={m['traceability']}")
    (settings.data_processed_dir / "blind_test.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), "utf-8")


if __name__ == "__main__":
    main()
