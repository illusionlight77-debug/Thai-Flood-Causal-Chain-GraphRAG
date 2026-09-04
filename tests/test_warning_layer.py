"""#4 risk layer + #5 blind protocol — offline (pure functions / cached ui_data)."""
import pytest

from src.config import settings


def test_risk_annotation_shape():
    from src.eval.risk_warning import annotate
    w = [{"province": "Nakhon Sawan", "province_th": "นครสวรรค์", "lead_hours": 72,
          "chain": ["a", "b", "c", "d", "Nakhon Sawan"]}]
    out = annotate(w)
    r = out[0]
    assert 0 < r["probability"] <= 1
    assert r["lead_window_h"][0] <= r["lead_window_h"][1]      # fast-wave <= slow-fill
    assert r["risk_level"] in ("สูงมาก", "สูง", "ปานกลาง", "ต่ำ")
    assert r["exposure_pop_k"] and r["risk_score"] >= 0


def test_risk_sorted_desc():
    from src.eval.risk_warning import annotate
    w = [{"province": "Sing Buri", "province_th": "สิงห์บุรี", "lead_hours": 42, "chain": ["x", "Sing Buri"]},
         {"province": "Nakhon Sawan", "province_th": "นครสวรรค์", "lead_hours": 72, "chain": ["x", "Nakhon Sawan"]}]
    out = annotate(w)
    assert out[0]["risk_score"] >= out[1]["risk_score"]        # เรียงตาม risk มาก→น้อย


@pytest.mark.skipif(not (settings.data_processed_dir.parent.parent / "web" / "ui_data_2022.json").exists()
                    if False else False, reason="")
def test_blind_zero_learned_params():
    from src.eval.blind_test import run
    res = run()
    assert res["learned_parameters"] == 0        # out-of-sample by construction
    assert "held_out_metrics" in res
