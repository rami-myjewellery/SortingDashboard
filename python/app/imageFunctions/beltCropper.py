import cv2
import numpy as np
from typing import Dict

from app.imageFunctions.maskLoader import FRAME_SIZE, REGION_MASKS

def crop_belts(raw_img_bytes: bytes) -> Dict[str, bytes]:
    img = cv2.imdecode(np.frombuffer(raw_img_bytes, np.uint8), cv2.IMREAD_COLOR)
    if img.shape[:2][::-1] != FRAME_SIZE:
        raise ValueError(f"Incoming frame size mismatch; expected {FRAME_SIZE}, got {img.shape[1::-1]}")

    crops: Dict[str, bytes] = {}

    for belt_id, bool_mask in REGION_MASKS.items():
        # Ensure mask is uint8 for bitwise operations
        m = bool_mask.astype(np.uint8)[:, :, None]

        # Apply mask to isolate belt
        masked = cv2.bitwise_and(img, img, mask=m[:, :, 0])

        # Get bounding-box coordinates from mask
        ys, xs = np.where(bool_mask)
        if len(xs) == 0 or len(ys) == 0:
            continue  # Skip empty masks

        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()

        # Crop image to the tight bounding box
        crop = masked[y0:y1+1, x0:x1+1]

        # Encode the cropped image as PNG
        _, buf = cv2.imencode(".png", crop)
        crops[belt_id] = buf.tobytes()

    return crops
