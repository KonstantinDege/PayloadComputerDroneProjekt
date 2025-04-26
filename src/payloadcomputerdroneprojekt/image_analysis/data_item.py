from time import time
from os.path import join
import numpy as np


class DataItem:
    def __init__(self, path: str):
        self._path = path
        self._time = int(time()*100)
        self._data = {"time": self._time, "found_objs": []}
        self._id: int

    def add_position(self, latlonalt: np.array, rot: np.array):
        self._data["latlonalt"] = latlonalt
        self._data["rot"] = rot

    def add_raw_image(self, image: np.array):
        raw_path = join(self._path, f"raw_image_{self._time}.npy")
        np.save(raw_path, image)
        self._data["raw_path"] = raw_path

    def add_computed_image(self, image: np.array):
        raw_path = join(self._path, f"computed_image_{self._time}.npy")
        np.save(raw_path, image)
        self._data["raw_path"] = raw_path

    def add_objects(self, objects: dict):
        self._data["found_objs"] = objects
        for i, obj in enumerate(objects):
            obj["id"] = f"{self._id}_{i}"

    def add_quality(self, quality: float):
        self._data["quality"] = float(quality)

    def get_dict(self):
        self._data["id"] = self._id
        return self._data
