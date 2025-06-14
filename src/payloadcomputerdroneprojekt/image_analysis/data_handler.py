from payloadcomputerdroneprojekt.image_analysis.data_item import DataItem
from payloadcomputerdroneprojekt.helper import smart_print as sp
import json
from os.path import exists, join
from os import remove
from os import makedirs
from scipy.cluster.hierarchy import fclusterdata
import numpy as np
from typing import Any, Dict, List, Optional, TypeVar
from collections import Counter

FILENAME = "__data__.json"
FILENAME_FILTERED = "__data_filtered__.json"

T = TypeVar("T")


class DataHandler:
    """
    Handles loading, saving, and processing of DataItem objects for image
    analysis.

    :param path: Directory path where data files are stored.
    :type path: str
    """

    def __init__(self, path: str) -> None:
        """
        Initializes the DataHandler, loads existing data if present, and
        prepares the storage directory.

        :param path: Directory path for storing data.
        :type path: str
        """
        if not exists(path):
            makedirs(path)
        self._path: str = path
        sp(f"Mission Path: {path}")
        self.list: List[DataItem] = []

        if exists(join(self._path, FILENAME)):
            sp("loading already existing data")
            with open(join(self._path, FILENAME), "r") as f:
                content: str = f.read()

                # Support for both JSON array and line-delimited JSON
                if content.startswith("["):
                    self.list = json.loads(content)
                else:
                    for line in content.splitlines():
                        self.list.append(json.loads(line))

        self.saved: int = len(self.list)

    def _get_new_item(self) -> DataItem:
        """
        Creates and appends a new DataItem to the internal list.

        :return: The newly created DataItem.
        :rtype: DataItem
        """
        new_item: DataItem = DataItem(self._path)
        new_item._id = len(self.list)
        self.list.append(new_item)
        return new_item

    def get_items(self) -> List[Dict[str, Any]]:
        """
        Returns a list of all DataItems as dictionaries.

        :return: List of DataItem dictionaries.
        :rtype: list
        """
        def get_item(item: Any) -> Dict[str, Any]:
            if isinstance(item, DataItem):
                return item.get_dict()
            return item
        return [get_item(item) for item in self.list]

    def get_filterd_items(self, distance_threshold: float
                          ) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """
        Filters and clusters detected objects by color and shape, then computes
        their mean positions.

        :param distance_threshold: Distance threshold for clustering.
        :type distance_threshold: float
        :return: Filtered and clustered object data.
        :rtype: dict
        """
        object_store: Dict[
            str, Dict[str, List[Dict[str, Any]]]] = self._get_obj_tree()
        sorted_list: Dict[
            str, Dict[str, Dict[int, List[Dict[str, Any]]]]] = sort_list(
            object_store, distance_threshold)
        output: Dict[str, Dict[str, List[Dict[str, Any]]]
                     ] = get_mean(sorted_list)
        with open(self.get_filtered_storage(), "w") as f:
            json.dump(output, f)
        return output

    def get_filtered_storage(self) -> str:
        """
        Returns the path to the filtered data storage file.

        :return: Path to filtered data file.
        :rtype: str
        """
        return join(self._path, FILENAME_FILTERED)

    def _get_obj_tree(self) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """
        Builds a nested dictionary of detected objects grouped by color and
        shape.

        :return: Nested dictionary of objects.
        :rtype: dict
        """
        object_store: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        for items in self.get_items():
            for obj in items["found_objs"]:
                object_store.setdefault(
                    obj["color"], []).append(obj)

                obj["time"] = items["time"]
        return object_store

    def _save(self) -> None:
        """
        Saves new DataItems to the data file in line-delimited JSON format.
        """
        with open(join(self._path, FILENAME), "a") as f:
            for item in self.get_items()[self.saved:]:
                f.write(json.dumps(item) + "\n")
            self.saved = len(self.list)

    def __enter__(self) -> DataItem:
        """
        Context manager entry: creates a new DataItem.

        :return: The new DataItem.
        :rtype: DataItem
        """
        return self._get_new_item()

    def __exit__(self, exc_type: Optional[type],
                 exc_val: Optional[BaseException], exc_tb: Optional[Any]
                 ) -> None:
        """
        Context manager exit: saves new DataItems.
        """
        self._save()

    def reset_data(self) -> None:
        """
        Resets the data handler by clearing the internal list and deleting the
        data file.
        """
        self.list = []
        self.saved = 0
        try:
            if exists(join(self._path, FILENAME)):
                sp("Resetting data file.")
                remove(join(self._path, FILENAME))
        except FileNotFoundError:
            sp("No data file to reset.")


def sort_list(
    object_store: Dict[str, Dict[str, List[Dict[str, Any]]]],
    distance_threshold: float
) -> Dict[str, Dict[str, Dict[int, List[Dict[str, Any]]]]]:
    """
    Clusters objects by their latitude and longitude using hierarchical
    clustering.

    :param object_store: Nested dictionary of objects grouped by color and
        shape.
    :type object_store: dict
    :param distance_threshold: Distance threshold for clustering.
    :type distance_threshold: float
    :return: Nested dictionary of clustered objects.
    :rtype: dict
    """
    sorted_list: Dict[str, Dict[int, List[Dict[str, Any]]]] = {}
    for color, objs in object_store.items():
        sorted_list[color] = {}
        coords_array = np.array([np.array(o["lat_lon"])
                                for o in objs])

        # If only one object, assign it to its own cluster
        if len(coords_array) == 1:
            sorted_list[color][0] = objs
            continue

        # Cluster objects by spatial proximity
        labels = fclusterdata(
            coords_array, criterion="distance", t=distance_threshold/110000)
        for i, obj in enumerate(objs):
            sorted_list[color].setdefault(
                int(labels[i]), []).append(obj)

    return sorted_list


def get_mean(
    sorted_list: Dict[str, Dict[str, Dict[int, List[Dict[str, Any]]]]]
) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    """
    Computes the mean latitude and longitude for each cluster of objects.

    :param sorted_list: Nested dictionary of clustered objects.
    :type sorted_list: dict
    :return: Nested dictionary with mean positions and associated times/IDs.
    :rtype: dict
    """
    output: Dict[str, List[Dict[str, Any]]] = {}
    for color, clusters in sorted_list.items():
        output[color] = []
        for _, cluster_objs in clusters.items():
            n: int = len(cluster_objs)
            lat: float = 0.0
            lon: float = 0.0
            times: List[Any] = []
            ids: List[Any] = []
            shapes: List[str] = []
            for item in cluster_objs:
                lat += item["lat_lon"][0]
                lon += item["lat_lon"][1]
                times.append(item["time"])
                ids.append(item["id"])

                if item["shape"]:
                    shapes.append(item["shape"])

            if n == 0:
                continue

            if len(shapes) == 0:
                most_common_shape = "unknown"
            else:
                most_common_shape = Counter(shapes).most_common(1)[0][0]

            output[color].append({
                "lat": lat/n,
                "lon": lon/n,
                "time": times,
                "id": ids,
                "shape": most_common_shape
            })
    return output
