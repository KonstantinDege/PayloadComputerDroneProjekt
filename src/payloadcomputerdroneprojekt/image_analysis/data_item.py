from time import time
from os.path import join
from typing import Any, Dict, List, Optional
import numpy as np
import cv2


class DataItem:
    """
    Represents a data item for image analysis, storing image paths, metadata,
    and detected objects.

    :param path: Directory path where images will be saved.
    :type path: str
    """

    def __init__(self, path: str):
        """
        Initialize a DataItem instance.

        :param path: Directory path for saving images.
        :type path: str
        """
        self._path: str = path
        self._time: int = int(time() * 100)
        self._data: Dict[str, Any] = {"time": self._time, "found_objs": []}
        self._id: Optional[int] = None

    def add_image_position(self, latlonalt: np.ndarray) -> None:
        """
        Add the image's GPS position (latitude, longitude, altitude).

        :param latlonalt: Array containing latitude, longitude, and altitude.
        :type latlonalt: np.ndarray
        """
        self._data["image_pos"] = latlonalt

    def add_raw_image(self, image: np.ndarray) -> None:
        """
        Save and register the raw image.

        :param image: Raw image as a numpy array.
        :type image: np.ndarray
        """
        self.add_image(image, "raw_image")

    def add_image(self, image, name: str) -> None:
        """
        Save and register an image with a specific name.

        :param image: Image as a numpy array.
        :type image: np.ndarray
        :param name: Name for the saved image.
        :type name: str
        """
        image_path: str = join(self._path, f"{self._time}_{name}.jpg")
        cv2.imwrite(image_path, image)
        self._data[name] = f"{self._time}_{name}.jpg"

    def add_computed_image(self, image: np.ndarray) -> None:
        """
        Save and register the computed (processed) image.

        :param image: Computed image as a numpy array.
        :type image: np.ndarray
        """
        self.add_image(image, "computed_image")

    def add_objects(self, objects: List[Dict[str, Any]]) -> None:
        """
        Add detected objects to the data item and assign unique IDs to each.

        :param objects: List of detected object dictionaries.
        :type objects: List[Dict[str, Any]]
        """
        self._data["found_objs"] = objects
        # Assign a unique ID to each object based on the DataItem's ID and
        # object index
        for i, obj in enumerate(objects):
            obj["id"] = f"{self._id}_{i}"

    def add_quality(self, quality: float) -> None:
        """
        Add a quality metric to the data item.

        :param quality: Quality value (e.g., confidence score).
        :type quality: float
        """
        self._data["quality"] = float(quality)

    def add_height(self, height: float) -> None:
        """
        Add the height at which the image was taken.

        :param height: Height value.
        :type height: float
        """
        self._data["height"] = float(height)

    def get_dict(self) -> Dict[str, Any]:
        """
        Get the data item as a dictionary, including its ID.

        :return: Dictionary representation of the data item.
        :rtype: Dict[str, Any]
        """
        self._data["id"] = self._id
        return self._data
