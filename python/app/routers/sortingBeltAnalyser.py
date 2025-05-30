# app/routers/sortingBeltAnalyser.py
import base64, uuid, datetime, json
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import cv2, numpy as np

from app.imageFunctions.beltCropper import crop_belts
from app.config.environment_variables_provider import environment_variables_provider
from app.data.store import get_db
router = APIRouter()
client = OpenAI(api_key=environment_variables_provider.openai_api_key().strip())

# ---------- debug output dir ------------------------------------------------
CROP_DIR = Path(__file__).resolve().parents[2] / "scratch" / "crops"
CROP_DIR.mkdir(parents=True, exist_ok=True)
# ---------------------------------------------------------------------------

class GPTAnswer(BaseModel):
    gpt_answer: dict[str, int]   # already parsed JSON

# -- helper -----------------------------------------------------------------
def mark_candidate_labels(rgb: np.ndarray) -> np.ndarray:
    """
    Finds bright-ish rectangles (label stickers) and puts a tiny red dot
    at each centroid.  Very lightweight; improves GPT counting accuracy.
    """
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    # threshold on bright areas (labels are white-ish)
    _, bw = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)
    kernel = np.ones((5, 5), np.uint8)
    bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    out = rgb.copy()
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w * h < 400:                      # ignore tiny specks
            continue
        cx, cy = x + w//2, y + h//2
        cv2.circle(out, (cx, cy), 4, (255, 0, 0), -1)  # red dot
    return out
# ---------------------------------------------------------------------------

@router.post("/analyze-image", response_model=GPTAnswer)
async def analyze_image(
    file: UploadFile =  (...),
):
    # 1️⃣ crop the 4 belts
    try:
        full_frame = await file.read()
        crops_bin = crop_belts(full_frame)              # {'red': b'...', ...}
    except Exception as e:
        raise HTTPException(400, str(e))
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    for segment_id, img_bytes in crops_bin.items():
        img_path = CROP_DIR / f"{ts}_{segment_id}.png"
        "img_path.write_bytes(img_bytes)"
        print(f"Saved segment '{segment_id}' to {img_path}")
    # 2️⃣ save crops & prepare vision inputs (detail:high) one-by-one
    belt_counts: dict[str, int] = {}

    prompt_single = (
        "This image shows ONE conveyor-belt segment with parcels.\n"
        "Count **every individual label sticker** you can see on the parcels. the camera quality is not too good so check for white squares"
        "only respond in the integer of the amount of labels you see"
    )

    for bin in crops_bin:
        png_bytes = crops_bin.get(bin)

        # -- optional upscale for more pixels (2×) --------------------------
        rgb = cv2.imdecode(np.frombuffer(png_bytes, np.uint8), cv2.IMREAD_COLOR)
        rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        rgb = cv2.resize(rgb, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        rgb = cv2.resize(rgb, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

        # -- optional marker dots ------------------------------------------
        rgb = mark_candidate_labels(rgb)

        # -- encode back to PNG --------------------------------------------
        _, buf = cv2.imencode(".png", cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        png_bytes = buf.tobytes()

        # -- debug-save to scratch -----------------------------------------
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        uid = uuid.uuid4().hex[:6]
        Path(CROP_DIR, f"{ts}_{uid}_{bin}.png").write_bytes(png_bytes)

        # -- build vision message ------------------------------------------
        data_url = "data:image/png;base64," + base64.b64encode(png_bytes).decode()

        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_single},
                {"type": "image_url",
                 "image_url": {"url": data_url, "detail": "high"}}
            ],
        }]

        # 3️⃣ ask GPT-4o-mini-vision for this single belt
        reply_text = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.2,
        ).choices[0].message.content.strip()

        # 4️⃣ extract the integer (allow plain number or JSON literal)
        try:
            belt_counts[bin] = int(json.loads(reply_text)) or 0
        except Exception:
            # fallback: digits in the string
            digits = "".join(ch for ch in reply_text if ch.isdigit())
            belt_counts[bin] = int(digits) if digits else 1
        # ----------- 3️⃣  UPDATE DASHBOARD KPI VALUES -------------------------
    db = get_db()["default"]  # single profile for now

    total_labels = sum(belt_counts.values())  # multi-belt = accumulated
    highest_belt = max(v for k, v in belt_counts.items())  # ignore red
    error_labels = belt_counts.get("segment_6")

    for kpi in db.kpis:
        if kpi.label.startswith("Multi"):
            kpi.value = total_labels
            kpi.unit = " boxes"
        elif kpi.label.startswith("Single"):
            kpi.value = highest_belt
            kpi.unit = " boxes"
        elif kpi.label.startswith("Error"):
            kpi.value = error_labels
            kpi.unit = " boxes"

    # optional: flip dashboard status
    db.status = "risk" if error_labels > 4 else "good"
    print(db)
    return {"gpt_answer": belt_counts}
