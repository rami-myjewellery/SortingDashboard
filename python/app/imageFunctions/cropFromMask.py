# app/imageFunctions/crop_from_mask.py
import cv2, numpy as np
from typing import Tuple

def crop_visible_region(mask_png_bytes: bytes) -> Tuple[bytes, Tuple[int,int,int,int]]:
    """
    Given a PNG mask where the wanted pixels are anything ≠ black,
    return a tightly-cropped PNG of just that area plus its (x,y,w,h).
    """
    mask_img = cv2.imdecode(np.frombuffer(mask_png_bytes, np.uint8), cv2.IMREAD_UNCHANGED)
    if mask_img is None:
        raise ValueError("Mask image unreadable")

    # If the PNG has an alpha channel, composite on black first
    if mask_img.shape[2] == 4:
        alpha = mask_img[:, :, 3] / 255.0
        rgb   = mask_img[:, :, :3]
        mask_img = cv2.convertScaleAbs(rgb * alpha[..., None])

    # ❶ threshold: non-black = foreground
    gray  = cv2.cvtColor(mask_img, cv2.COLOR_BGR2GRAY)
    _, bw = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)   # 10 catches faint yellows too

    # ❷ morphological opening to clean dots (optional)
    kernel = np.ones((5,5), np.uint8)
    bw = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel)

    # ❸ bounding box of all white pixels
    ys, xs = np.where(bw > 0)
    if xs.size == 0 or ys.size == 0:
        raise ValueError("Mask is empty (all black)")

    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    crop = mask_img[y0:y1+1, x0:x1+1]

    _, buf = cv2.imencode(".png", crop)
    return buf.tobytes(), (x0, y0, x1 - x0 + 1, y1 - y0 + 1)
