import json
import cv2
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches


def draw_data_on_image(data, image_folder):
    image_path = os.path.join(image_folder, data["computed_image"])
    img = cv2.imread(image_path)
    if img is None:
        print(f"Image not found: {image_path}")
        return
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.imshow(img)

    for obj in data["found_objs"]:
        color = obj["color"]
        bbox = obj["bound_box"]
        contour = obj["contour"]
        codes = obj.get("code", [])
        label = obj.get("id", "")

        # Bounding Box
        rect = patches.Rectangle(
            (bbox["x_start"], bbox["y_start"]),
            bbox["x_stop"] - bbox["x_start"],
            bbox["y_stop"] - bbox["y_start"],
            linewidth=2, edgecolor=color, facecolor='none'
        )
        ax.add_patch(rect)
        ax.text(bbox["x_start"], bbox["y_start"] - 10, label,
                color=color, fontsize=10, backgroundcolor="white")

        # Contour
        contour_pts = [(pt[0], pt[1]) for pt in contour]
        contour_pts.append(contour_pts[0])  # close contour
        xs, ys = zip(*contour_pts)
        ax.plot(xs, ys, color=color, linewidth=2, linestyle="--")

        # Codes
        for c in codes:
            code_rect = patches.Rectangle(
                (c["x"], c["y"]), c["w"], c["h"],
                linewidth=1, edgecolor='cyan', facecolor='cyan', alpha=0.4
            )
            ax.add_patch(code_rect)
            ax.text(c["x"], c["y"] - 5, str(c["d"]), color='black',
                    fontsize=8, backgroundcolor="white")

    ax.set_title(f'Time: {data["time"]} | ID: {data["id"]}')
    ax.axis('off')
    plt.tight_layout()
    plt.show()


def visualize_dataset(json_list, image_folder):
    for entry in json_list:
        draw_data_on_image(entry, image_folder)


if __name__ == "__main__":
    # Example usage:#
    path = r"C:\Users\degek\AppData\Local\Temp\image_analysisnu5mb74s"
    json_file = os.path.join(path, "__data__.json")

    with open(json_file, "r") as f:
        content = f.read()
        if content.startswith("["):
            data_entries = json.loads(content)
        else:
            data_entries = [json.loads(line) for line in content.splitlines()]

    if isinstance(data_entries, dict):
        data_entries = [data_entries]  # single entry case

    visualize_dataset(data_entries, path)
