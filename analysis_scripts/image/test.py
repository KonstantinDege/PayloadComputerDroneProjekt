import json
import cv2
import os
import numpy as np
import argparse

parser = argparse.ArgumentParser(description="Image annotation viewer")
parser.add_argument(
    "path", type=str,
    help="Path to the folder containing the images and __data__.json")

image_base_path = parser.parse_args().path
json_path = os.path.join(image_base_path, "__data__.json")
filtered_path = os.path.join(image_base_path, "__data_filtered__.json")


# === Config ===
display_keys = ["raw_image", "computed_image",
                "blue", "red", "yellow", "orange", "shape"]
# individual image height (each sub-image will be resized to this)
canvas_height = 300

# === Load JSON Data ===
with open(json_path, "r") as f:
    content = f.read()
    if content.startswith("["):
        all_frames = json.loads(content)
    else:
        all_frames = [json.loads(line) for line in content.splitlines()]

with open(filtered_path, "r") as f:
    filtered_data = json.load(f)

# === Build filtered ID set ===
filtered_ids = {
    obj_id: {"color": color, "shape": obj["shape"]}
    for color, objs in filtered_data.items()
    for obj in objs
    for obj_id in obj["id"]
}

# === Helper: Add label above image ===


def pad_to_width(img, target_width):
    h, w = img.shape[:2]
    if w >= target_width:
        return img
    pad_width = target_width - w
    return cv2.copyMakeBorder(img, 0, 0, 0, pad_width,
                              cv2.BORDER_CONSTANT, value=(0, 0, 0))


def draw_annotations(img, frame, filtered_ids):
    debug_img = img.copy()
    for obj in frame.get("found_objs", []):
        obj_id = obj["id"]
        bb = obj["bound_box"]
        contour = obj.get("contour")

        # Color + Label
        if obj_id in filtered_ids:
            color_map = {
                "yellow": (0, 0, 0),
                "red": (0, 0, 255),
                "blue": (255, 0, 0),
            }
            color = color_map.get(
                filtered_ids[obj_id]["color"], (255, 255, 255))
            h = obj.get("h", -1)
            shape = filtered_ids[obj_id].get("shape", "")
            c = filtered_ids[obj_id]['color']
            label = f"{obj_id} {h:.2f} [{c}] {shape}".strip()
        else:
            color = (200, 200, 200)
            label = obj_id

        # Draw box + contour
        cv2.rectangle(debug_img, (bb['x_start'], bb['y_start']),
                      (bb['x_stop'], bb['y_stop']), color, 2)

        cv2.putText(debug_img, label, (bb['x_start'], bb['y_start'] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 2)

        if contour is not None:
            contour_np = cv2.convexHull(np.array(contour, dtype=np.int32))
            cv2.polylines(debug_img, [contour_np], True, color, 2)

    return debug_img


def label_image(img, text):
    labeled = img.copy()
    cv2.rectangle(labeled, (0, 0), (img.shape[1], 30), (0, 0, 0), -1)
    cv2.putText(labeled, text, (10, 20), cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (255, 255, 255), 1)
    return labeled


# === Main Loop ===
cv2.namedWindow("Fullscreen Window", cv2.WINDOW_FULLSCREEN)
i = 0
while i < len(all_frames):
    frame = all_frames[i]
    variants = []

    # First, draw on the computed image (or raw if fallback)
    base_file = frame.get("computed_image", frame.get("raw_image"))
    base_path = os.path.join(image_base_path, base_file)
    base_img = cv2.imread(base_path)
    if base_img is None:
        print(f"⚠️ Could not read: {base_path}")
        continue

    # Annotate before resizing
    annotated_img = draw_annotations(base_img, frame, filtered_ids)
    variants.append(("annotated", annotated_img))

    # Load additional image types if available
    for key in ["raw_image", "red", "blue", "yellow", "shape"]:
        file = frame.get(key)
        if file:
            img_path = os.path.join(image_base_path, file)
            img = cv2.imread(img_path)
            if img is not None:
                variants.append((key, img))

    # Resize all to same height (e.g., 400px), keeping aspect ratio
    fixed_height = 400
    resized_labeled = []
    for name, img in variants:
        if len(img.shape) == 2 or img.shape[2] == 1:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        aspect = img.shape[1] / img.shape[0]
        new_size = (int(fixed_height * aspect), fixed_height)
        img_resized = cv2.resize(img, new_size)
        labeled = label_image(img_resized, name)
        resized_labeled.append(labeled)

    # Split into two rows
    mid = (len(resized_labeled) + 1) // 2
    top_row = cv2.hconcat(resized_labeled[:mid])
    bottom_row = cv2.hconcat(resized_labeled[mid:])

    # Equalize row width
    max_width = max(top_row.shape[1], bottom_row.shape[1])
    top_row_padded = pad_to_width(top_row, max_width)
    bottom_row_padded = pad_to_width(bottom_row, max_width)

    # Combine into canvas
    canvas = cv2.vconcat([top_row_padded, bottom_row_padded])
    cv2.imshow("Fullscreen Window", canvas)

    key = cv2.waitKey(0)
    if key == ord('q'):
        break
    elif key == ord('w'):
        i += 1
    elif key == ord('s'):
        i = max(0, i - 1)

cv2.destroyAllWindows()
