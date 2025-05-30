import cv2
import numpy as np
from pathlib import Path
from skimage.measure import label

APP_DIR = Path(__file__).resolve().parent.parent
MASK_FILE = APP_DIR / "assets" / "belt_mask.png"

EXPECTED_SEGMENTS = 6

def load_region_masks():
    mask_img = cv2.imread(str(MASK_FILE))
    if mask_img is None:
        raise FileNotFoundError(
            f"Mask not found or unreadable: {MASK_FILE}. "
            "Check the assets folder is present in the image/container."
        )

    hsv = cv2.cvtColor(mask_img, cv2.COLOR_BGR2HSV)
    full_h, full_w = mask_img.shape[:2]

    # Initial HSV range parameters for green
    base_lower = np.array([40, 50, 50])
    base_upper = np.array([80, 255, 255])

    # Iteratively adjust saturation/value lower bound
    for threshold in range(50, 200, 10):
        adjusted_lower = np.array([40, threshold, threshold])
        green_mask = cv2.inRange(hsv, adjusted_lower, base_upper)

        labeled_segments, num_segments = label(green_mask, return_num=True, connectivity=2)

        if num_segments == EXPECTED_SEGMENTS:
            region_masks = {
                f"segment_{label_id}": (labeled_segments == label_id)
                for label_id in range(1, num_segments + 1)
            }
            return region_masks, (full_w, full_h)

    raise ValueError(
        f"Could not find exactly {EXPECTED_SEGMENTS} segments after iterative adjustments. "
        "Please verify the mask image manually."
    )

REGION_MASKS, FRAME_SIZE = load_region_masks()
