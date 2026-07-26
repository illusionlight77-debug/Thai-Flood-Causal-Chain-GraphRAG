"""Test metric หลัก: f1 + f1_by_hop + traceability."""
from src.eval.f1_by_hop import f1, f1_by_hop, traceability


def test_f1_perfect():
    assert f1({"Ayutthaya", "Ang Thong"}, {"Ayutthaya", "Ang Thong"}) == 1.0


def test_f1_empty_is_zero():
    assert f1(set(), {"Ayutthaya"}) == 0.0
    assert f1({"Ayutthaya"}, set()) == 0.0


def test_f1_partial():
    # pred={A,B}, gold={A,C} → p=0.5, r=0.5 → F1=0.5
    assert f1({"A", "B"}, {"A", "C"}) == 0.5


def test_f1_by_hop_buckets():
    preds = [
        (2, {"A"}, {"A"}),        # perfect 2-hop
        (4, {"A"}, {"B"}),        # miss 4-hop
        (4, {"B"}, {"B"}),        # perfect 4-hop
    ]
    res = f1_by_hop(preds)
    assert res[2] == 1.0
    assert res[4] == 0.5          # mean(0.0, 1.0)


def test_traceability():
    assert traceability([True, True, False, True]) == 0.75
    assert traceability([]) == 0.0
