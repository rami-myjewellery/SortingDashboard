# app/core/mask_loader.py
import cv2, numpy as np
from pathlib import Path

APP_DIR   = Path(__file__).resolve().parent.parent   # …/app/
MASK_FILE = APP_DIR / "assets" / "belt_mask.png"

mask_img = cv2.imread(str(MASK_FILE))
if mask_img is None:
    raise FileNotFoundError(
        f"Mask not found or unreadable: {MASK_FILE}. "
        "Check the assets folder is present in the image / container."
    )
# HSV ranges that match your solid paint colours
HSV_RANGES = {
    "red":     [(0,100,100), (10,255,255), (160,100,100), (180,255,255)],
    "green":   [(40,100,100), (80,255,255)],
    "yellow":  [(20,100,100), (35,255,255)],
    "magenta": [(140,100,100), (170,255,255)],
}

def load_region_masks():
    mask_img = cv2.imread(str(MASK_FILE))
    hsv      = cv2.cvtColor(mask_img, cv2.COLOR_BGR2HSV)

    full_h, full_w = mask_img.shape[:2]
    region_masks: dict[str, np.ndarray] = {}

    for colour, rngs in HSV_RANGES.items():
        m = None
        for i in range(0, len(rngs), 2):
            lower, upper = np.array(rngs[i]), np.array(rngs[i+1])
            part = cv2.inRange(hsv, lower, upper)
            m = part if m is None else cv2.bitwise_or(m, part)
        # store as boolean mask for fast use later
        region_masks[colour] = m.astype(bool)

    return region_masks, (full_w, full_h)

REGION_MASKS, FRAME_SIZE = load_region_masks()
