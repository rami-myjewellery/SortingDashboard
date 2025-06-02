
import cv2
import numpy as np
from pathlib import Path

def remove_small_regions(binary_img, min_area=50, draw_on=None):
    """
    Filters small regions and optionally draws bounding boxes on a provided image.
    Returns cleaned mask, count of regions, and optionally annotated image.
    """
    contours, _ = cv2.findContours(binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask_cleaned = np.zeros_like(binary_img)
    count = 0

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > min_area:
            cv2.drawContours(mask_cleaned, [cnt], -1, 255, thickness=cv2.FILLED)
            count += 1
            if draw_on is not None:
                x, y, w, h = cv2.boundingRect(cnt)
                cv2.rectangle(draw_on, (x, y), (x + w, y + h), (0, 255, 0), 2)

    return mask_cleaned, count, draw_on


def segment_white_labels(img, threshold_value=220):
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Threshold to find bright (white-ish) regions
    _, thresh = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)

    # Morphological opening to remove small specks
    kernel = np.ones((2, 2), np.uint8)
    opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

    return opened

def process_image(image_path, output_dir):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    img = cv2.imread(image_path)

    # Step 1: Segment white label regions
    white_mask = segment_white_labels(img)
    cv2.imwrite(str(Path(output_dir) / "step1_white_mask_raw.png"), white_mask)

    # Step 2: Clean up noise and count valid labels
    annotated_img = img.copy()
    cleaned_mask, count, annotated_img = remove_small_regions(white_mask, min_area=50, draw_on=annotated_img)
    cv2.imwrite(str(Path(output_dir) / "step2_white_mask_cleaned.png"), cleaned_mask)
    cv2.imwrite(str(Path(output_dir) / "step3_labels_annotated.png"), annotated_img)

    print(f"Detected labels: {count}")
    print(f"Saved processed masks to: {output_dir}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("image_path", help="Path to the input image")
    parser.add_argument("--output_dir", default="label_mask_output", help="Directory to save the output images")
    args = parser.parse_args()
    process_image(args.image_path, args.output_dir)
