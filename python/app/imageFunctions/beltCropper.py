# app/core/cropper.py
import cv2, numpy as np
from io import BytesIO

from app.imageFunctions.maskLoader import FRAME_SIZE, REGION_MASKS


def crop_belts(raw_img_bytes: bytes) -> dict[str, bytes]:
    img = cv2.imdecode(np.frombuffer(raw_img_bytes, np.uint8), cv2.IMREAD_COLOR)
    if img.shape[:2][::-1] != FRAME_SIZE:
        raise ValueError("Incoming frame size mismatch; expected "
                         f"{FRAME_SIZE}, got {img.shape[1::-1]}")

    crops: dict[str, bytes] = {}
    for colour, bool_mask in REGION_MASKS.items():
        # put the mask back into 8-bit so we can multiply
        m = bool_mask.astype(np.uint8)[:, :, None]
        masked = cv2.bitwise_and(img, img, mask=m[:,:,0])

        # find tight bounding-box for current belt
        ys, xs = np.where(bool_mask)
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        crop = masked[y0:y1+1, x0:x1+1]

        _, buf = cv2.imencode(".png", crop)
        crops[colour] = buf.tobytes()

    return crops
