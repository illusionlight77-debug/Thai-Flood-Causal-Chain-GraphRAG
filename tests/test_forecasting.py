"""Roadmap B — tests for case_bank + calibration (offline, อ่านจาก ui_data/case_bank JSON)."""
from src.eval import calibration, case_bank, warning_verification


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
    assert len(r["drift_csi_by_event"]) == 4
