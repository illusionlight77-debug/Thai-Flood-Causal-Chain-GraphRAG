"""Roadmap B — tests for case_bank + calibration (offline, อ่านจาก ui_data/case_bank JSON)."""
from src.eval import calibration, case_bank, warning_verification
from src.ingest import rid_bulletin


def test_rid_bulletin_parser():
    """lever-1 tool: RID bulletin prose → per-sub-basin over-bank (independent of gold)."""
    txt = ("แม่น้ำปิง สถานี P.7A ปริมาณน้ำไหลผ่าน 900 ลบ.ม./วินาที ระดับน้ำ สูงกว่าตลิ่ง 1.20 เมตร "
           "แม่น้ำเจ้าพระยา สถานี C.2 ปริมาณน้ำไหลผ่าน 766 ลบ.ม./วินาที ระดับน้ำ ต่ำกว่าตลิ่ง 6.73 เมตร")
    st = {s["station"]: s for s in rid_bulletin.parse_stations(txt)}
    assert st["P.7A"]["subbasin"] == "Ping" and st["P.7A"]["over_bank"] is True
    assert st["C.2"]["subbasin"] == "ChaoPhraya" and st["C.2"]["over_bank"] is False
    res = rid_bulletin.to_overbank_json(list(st.values()), "unit", "test")
    assert res["overflow"]["Ping"] is True and res["overflow"]["ChaoPhraya"] is False


def test_outcome_labels():
    assert case_bank._label(True, True) == "TP"
    assert case_bank._label(True, False) == "FP"
    assert case_bank._label(False, True) == "FN"
    assert case_bank._label(False, False) == "TN"


def test_case_bank_builds():
    bank = case_bank.build()
    assert bank["n_cases_scored"] > 0
    c = bank["cumulative_scored"]
    for k in ("pod", "far", "csi"):
        assert 0.0 <= c[k] <= 1.0
    # confusion นับครบ = จำนวนเคส scored
    assert c["tp"] + c["fp"] + c["fn"] + c["tn"] == bank["n_cases_scored"]
    assert all(x["outcome"] in ("TP", "FP", "FN", "TN") for x in bank["cases"])


def test_calibration_prequential():
    r = calibration.run()
    assert r["n_warned"] > 0
    for m in r["models"].values():
        assert 0.0 <= m["brier"] <= 1.0
    # baseline คงที่ → sharpness = 0; LOEO ต้อง sharp กว่า (>0)
    assert r["models"]["baseline_const"]["sharpness_sd"] == 0.0
    assert r["models"]["loeo_by_hop"]["sharpness_sd"] > 0.0


def test_verification_bss_and_decomp():
    r = warning_verification.run()
    assert r["n_warned"] > 0
    m = r["models"]
    # Murphy identity: BS ~= reliability - resolution + uncertainty
    for v in m.values():
        approx = v["reliability"] - v["resolution"] + v["uncertainty"]
        assert abs(approx - v["brier"]) < 1e-2
    # calibrate-by-hop ควรมี skill (BSS) เหนือค่าคงที่ (รายงานตรง แม้ CI จะกว้าง)
    assert m["by_hop"]["bss_vs_climatology"] > m["const"]["bss_vs_climatology"]
    n_events = len({c["event"] for c in case_bank.build()["cases"] if c["scored"]})
    assert len(r["drift_csi_by_event"]) == n_events
    # event-level (cluster) bootstrap + per-event consistency reported
    assert "bss_ci95" in r["best_ci_event_level"]
    assert len(r["per_event_loeo"]) == n_events
