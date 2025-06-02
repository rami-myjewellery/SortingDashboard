import cv2
import cv2
import numpy as np

from app.routers.sortingBeltAnalyser import segment_white_labels, remove_small_regions

GROUND_TRUTH = {
    "segment_6": 2,
    "segment_4": 15,
    "segment_2": 18,
    "segment_1": 17,
    "segment_3": 8,
    "segment_5": 11
}

# Initial params
params = {
    "min_area": 100,
    "max_aspect_ratio": 5.0,
    "min_extent": 0.2,
    "min_solidity": 0.5,
}

param_steps = {
    "min_area": [50, 75, 100, 125, 150],
    "max_aspect_ratio": [2.0, 3.0, 4.0, 5.0, 6.0],
    "min_extent": [0.1, 0.2, 0.3, 0.4],
    "min_solidity": [0.3, 0.4, 0.5, 0.6]
}

def score(pred, target):
    return sum(abs(pred.get(k, 0) - target.get(k, 0)) for k in target)

def test_params_on_segments(image_dict, params):
    result = {}

    for seg, img in image_dict.items():
        mask = segment_white_labels(img)  # assumed available
        _, count, _ = remove_small_regions(mask, draw_on=None, **params)
        result[seg] = count

    return result

def tune(image_dict):
    current_params = params.copy()
    current_output = test_params_on_segments(image_dict, current_params)
    best_score = score(current_output, GROUND_TRUTH)

    for param_name in param_steps:
        for val in param_steps[param_name]:
            trial_params = current_params.copy()
            trial_params[param_name] = val
            trial_output = test_params_on_segments(image_dict, trial_params)
            trial_score = score(trial_output, GROUND_TRUTH)

            if trial_score < best_score:
                best_score = trial_score
                current_params = trial_params
                print(f"✔️ Improved: {param_name} = {val}, score = {trial_score}")
                break  # move to next param
            else:
                print(f"❌ Worse: {param_name} = {val}, score = {trial_score}")

    return current_params, best_score

# Use like:
# tuned_params, final_score = tune(image_dict_with_segment_keys)

if __name__ == "__main__":
    # Load test images (your saved crops)
    image_dict = {
        "segment_6": cv2.imread("/Users/rami.shokir/SortingDashboard/python/scratch/crops/20250602-175407_segment_6.png"),
        "segment_4": cv2.imread("/Users/rami.shokir/SortingDashboard/python/scratch/crops/20250602-175407_segment_4.png"),
        "segment_2": cv2.imread("/Users/rami.shokir/SortingDashboard/python/scratch/crops/20250602-175407_segment_2.png"),
        "segment_1": cv2.imread("/Users/rami.shokir/SortingDashboard/python/scratch/crops/20250602-175407_segment_1.png"),
        "segment_3": cv2.imread("/Users/rami.shokir/SortingDashboard/python/scratch/crops/20250602-175407_segment_3.png"),
        "segment_5": cv2.imread("/Users/rami.shokir/SortingDashboard/python/scratch/crops/20250602-175407_segment_5.png"),
    }

    best_params, score_value = tune(image_dict)
    print("✅ Best Params:", best_params)
    print("🎯 Final Score:", score_value)