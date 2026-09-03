"""#1 LLM generation — provider-agnostic (groq | ollama | anthropic | none).

ใช้สร้าง "คำอธิบายเหตุน้ำท่วมรายจังหวัดแบบ user-friendly" จาก causal chain + evidence จริง
(grounded: ห้ามแต่งข้อมูลนอกเหนือจาก chain/evidence ที่ให้). ถ้า provider=none หรือเรียกไม่ได้
→ คืน "" ให้ผู้เรียกใช้ template แทน (ระบบไม่พังถ้าไม่มี LLM).
"""
from __future__ import annotations

import requests

from src.config import settings

TIMEOUT = 45

SYSTEM = (
    "คุณเป็นผู้ช่วยอธิบายสาเหตุน้ำท่วมให้ประชาชนเข้าใจง่าย ตอบเป็นภาษาไทยล้วน "
    "ใช้ *เฉพาะ* ข้อมูลสายเหตุ-ผล (causal chain) และหลักฐาน (evidence) ที่ให้มาเท่านั้น "
    "ห้ามแต่งชื่อแม่น้ำ/เขื่อน/จังหวัดที่ไม่ได้อยู่ในข้อมูล ตอบกระชับ 2–4 ประโยค อบอุ่นเป็นมิตร"
)


def available() -> bool:
    p = settings.llm_provider
    if p == "groq":
        return bool(settings.groq_api_key)
    if p == "ollama":
        return True
    if p == "anthropic":
        return bool(settings.anthropic_api_key)
    return False


def _chat(user: str) -> str:
    p = settings.llm_provider
    if p == "groq":
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                          headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                          json={"model": settings.groq_model, "temperature": 0.3, "max_tokens": 300,
                                "messages": [{"role": "system", "content": SYSTEM},
                                             {"role": "user", "content": user}]}, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    if p == "ollama":
        r = requests.post(f"{settings.ollama_base}/api/chat",
                          json={"model": settings.ollama_model, "stream": False,
                                "messages": [{"role": "system", "content": SYSTEM},
                                             {"role": "user", "content": user}]}, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()["message"]["content"].strip()
    if p == "anthropic":
        r = requests.post("https://api.anthropic.com/v1/messages",
                          headers={"x-api-key": settings.anthropic_api_key,
                                   "anthropic-version": "2023-06-01"},
                          json={"model": settings.anthropic_model, "max_tokens": 300,
                                "system": SYSTEM, "messages": [{"role": "user", "content": user}]},
                          timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()["content"][0]["text"].strip()
    return ""


def explain_flood(province: str, chain: list[str], evidence: list[dict],
                  hops: int, flooded: bool, lead_time_h: int | None = None) -> str:
    """คำอธิบายเหตุน้ำท่วมของจังหวัด (grounded บน chain+evidence). คืน "" ถ้า LLM ไม่พร้อม/ล้มเหลว."""
    if not available():
        return ""
    if not flooded or not chain:
        user = (f"ระบบสรุปว่า 'จังหวัด{province}' ไม่พบสายเหตุ-ผลน้ำท่วมจากกราฟ (ลำน้ำหลักไม่ล้น). "
                f"อธิบายสั้นๆ ว่าทำไมระบบจึงไม่ทำนายว่าท่วม (อาจท่วมจากฝนท้องถิ่นที่กราฟไม่ครอบคลุม).")
    else:
        ev = "; ".join(f"{e.get('dataset','')} ({e.get('station_id','')})" for e in evidence)
        lead = f" คาดถึงจังหวัดนี้ในอีกราว {lead_time_h} ชั่วโมงหลังต้นเหตุ." if lead_time_h else ""
        user = (f"จังหวัด: {province} (สายเหตุ-ผลยาว {hops}-hop)\n"
                f"สายเหตุ-ผล (ต้นน้ำ→ปลายน้ำ): {' → '.join(chain)}\n"
                f"หลักฐานประกอบแต่ละช่วง: {ev}\n"
                f"lead time: {lead_time_h if lead_time_h else '-'} ชั่วโมง\n"
                f"อธิบายให้ชาวบ้านเข้าใจว่าทำไมจังหวัดนี้ถึงน้ำท่วม ตามสายเหตุ-ผลนี้.{lead}")
    try:
        return _chat(user)
    except Exception:  # noqa: BLE001
        return ""


def main() -> None:
    print("provider:", settings.llm_provider, "| available:", available())
    if available():
        print(explain_flood("Nakhon Sawan",
              ["สถานีฝนปิงตอนบน", "ปิงท้ายเขื่อนภูมิพล", "ปากน้ำโพ", "เจ้าพระยาตอนบน", "Nakhon Sawan"],
              [{"dataset": "D1 rain→runoff", "station_id": "RS-PING"},
               {"dataset": "D1 river gauge", "station_id": "CONF-PAKNAMPHO"}], 4, True, 84))


if __name__ == "__main__":
    main()
