from time import time
from os.path import join
import numpy as np
import cv2


class DataItem:
    def __init__(self, path: str):
        self._path = path
        self._time = int(time()*100)
        self._data = {"time": self._time, "found_objs": []}
        self._id: int

    def add_image_position(self, latlonalt: np.array):
        self._data["image_pos"] = latlonalt

    def add_raw_image(self, image: np.array):
        raw_path = join(self._path, f"{self._time}_raw_image.jpg")
        cv2.imwrite(raw_path, image)
        self._data["raw_path"] = f"{self._time}_raw_image.jpg"

    def add_computed_image(self, image: np.array):
        raw_path = join(self._path, f"{self._time}_computed_image.jpg")
        cv2.imwrite(raw_path, image)
        self._data["computed_path"] = f"{self._time}_computed_image.jpg"

    def add_objects(self, objects: dict):
        self._data["found_objs"] = objects
        for i, obj in enumerate(objects):
            obj["id"] = f"{self._id}_{i}"

    def add_quality(self, quality: float):
        self._data["quality"] = float(quality)

    def add_height(self, height: float):
        self._data["height"] = float(height)

    def get_dict(self):
        self._data["id"] = self._id
        return self._data
