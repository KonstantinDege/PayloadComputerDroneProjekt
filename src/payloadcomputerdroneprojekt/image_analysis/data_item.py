from datetime import time
from os.path import join
import numpy as np


class DataItem:
    def __init__(self, path: str):
        self._path = path
        self._time = int(time*100)
        self._data = {"time": self._time, "found_obj": []}

    def add_position(self, latlonalt: np.array, rot: np.array):
        self._data["latlonalt"] = latlonalt
        self._data["rot"] = rot

    def add_raw_image(self, image: np.array):
        raw_path = join(self._path, f"raw_image_{self._time}")
        with open(raw_path, "w") as f:
            f.write(image)
        self._data["raw_path"] = raw_path

    def add_computed_image(self, image: np.array):
        raw_path = join(self._path, f"computed_image_{self._time}")
        with open(raw_path, "w") as f:
            f.write(image)
        self._data["raw_path"] = raw_path

    def add_objects(self, objects: dict):
        self._data["obj"] = objects

    def get_dict(self):
        return self._data
