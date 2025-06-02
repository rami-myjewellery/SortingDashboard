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

GROUND_TRUTH = {
    "segment_6": 2,
    "segment_4": 15,
    "segment_2": 18,
    "segment_1": 17,
    "segment_3": 8,
    "segment_5": 11
}


def calc_score(pred, target):
    error = sum(abs(pred.get(k, 0) - target.get(k, 0)) for k in target)
    max_possible = sum(target.values())
    return max(0.0, 100.0 - (error / max_possible * 100.0))



# Belt segments ordered physically from left to right
BELT_ORDER_LEFT_TO_RIGHT = ["segment_6", "segment_4", "segment_2", "segment_1", "segment_3", "segment_5"]

# ---------- debug output dir ------------------------------------------------
CROP_DIR = Path(__file__).resolve().parents[2] / "scratch" / "crops"
CROP_DIR.mkdir(parents=True, exist_ok=True)
# ---------------------------------------------------------------------------

class GPTAnswer(BaseModel):
    gpt_answer: dict[str, int]   # already parsed JSON



def segment_white_labels(img, threshold_value=210):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)
    kernel = np.ones((2, 2), np.uint8)
    opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    return opened

def remove_small_regions(binary_img, min_area=25, draw_on=None, max_aspect_ratio=4.0, min_extent=0.2, min_solidity=0.5):
    """
    Filters small, elongated, hollow, and line-like regions.
    Keeps regions that are squarish and solid (like label stickers).
    """
    contours, _ = cv2.findContours(binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask_cleaned = np.zeros_like(binary_img)
    count = 0

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue

        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = max(w / h, h / w)
        if aspect_ratio > max_aspect_ratio:
            continue

        rect_area = w * h
        extent = area / rect_area if rect_area > 0 else 0
        if extent < min_extent:
            continue

        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0
        if solidity < min_solidity:
            continue

        # All checks passed
        cv2.drawContours(mask_cleaned, [cnt], -1, 255, thickness=cv2.FILLED)
        count += 1

        if draw_on is not None:
            cv2.rectangle(draw_on, (x, y), (x + w, y + h), (0, 255, 0), 2)

    return mask_cleaned, count, draw_on

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
        # img_path.write_bytes(img_bytes)
        # print(f"Saved segment '{segment_id}' to {img_path}")
    # 2️⃣ save crops & prepare vision inputs (detail:high) one-by-one
    belt_counts: dict[str, int] = {}

    for bin in BELT_ORDER_LEFT_TO_RIGHT:
        if bin not in crops_bin:
            continue
        png_bytes = crops_bin.get(bin)

        # Decode image
        rgb = cv2.imdecode(np.frombuffer(png_bytes, np.uint8), cv2.IMREAD_COLOR)
        rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)

        # Optional upscale for clarity
        rgb = cv2.resize(rgb, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

        # Save original crop
        uid = uuid.uuid4().hex[:6]
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        crop_path = CROP_DIR / f"{ts}_{uid}_{bin}_crop.png"
        cv2.imwrite(str(crop_path), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))

        # Segment white label candidates
        label_mask = segment_white_labels(rgb)
        raw_mask_path = CROP_DIR / f"{ts}_{uid}_{bin}_label_raw.png"
        cv2.imwrite(str(raw_mask_path), label_mask)

        # Remove noise and count
        annotated = rgb.copy()
        cleaned_mask, count, annotated = remove_small_regions(label_mask, min_area=50, draw_on=annotated)
        clean_mask_path = CROP_DIR / f"{ts}_{uid}_{bin}_label_clean.png"
        annotated_path = CROP_DIR / f"{ts}_{uid}_{bin}_annotated.png"
        cv2.imwrite(str(clean_mask_path), cleaned_mask)
        cv2.imwrite(str(annotated_path), cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR))

        # Normalize hallucinated counts
        if count > 30:
            count = 0

        belt_counts[bin] = count

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
    ordered_counts = {k: belt_counts.get(k, 0) for k in BELT_ORDER_LEFT_TO_RIGHT}
    success = calc_score(belt_counts, GROUND_TRUTH)
    print(f"🎯 Label match success: {success:.2f}%")
    return {"gpt_answer": ordered_counts}
