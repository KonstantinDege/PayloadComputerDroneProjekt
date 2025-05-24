from payloadcomputerdroneprojekt.image_analysis.data_item import DataItem
from payloadcomputerdroneprojekt.helper import smart_print as sp
import json
from os.path import exists, join
from os import makedirs
from scipy.cluster.hierarchy import fclusterdata
import numpy as np

FILENAME = "__data__.json"
FILENAME_FILTERED = "__data_filtered__.json"


class DataHandler:
    def __init__(self, path: str):
        if not exists(path):
            makedirs(path)
        self._path = path
        sp(f"Mission Path: {path}")
        self._fake = DataItem("")
        self.list: list[DataItem] = []

        if exists(join(self._path, FILENAME)):
            sp("loading already existing data")
            with open(join(self._path, FILENAME), "r") as f:
                content = f.read()

                if content.startswith("["):
                    self.list = json.loads(content)
                else:
                    for line in content.splitlines():
                        self.list.append(json.loads(line))

        self.saved = len(self.list)

    def _get_new_item(self) -> DataItem:
        new_item = DataItem(self._path)
        new_item._id = len(self.list)
        self.list.append(new_item)
        return new_item

    def get_items(self):
        def get_item(item):
            if isinstance(item, DataItem):
                return item.get_dict()
            return item
        return [get_item(item) for item in self.list]

    def get_filterd_items(self, dis):
        object_store = self._get_obj_tree()
        sorted_list = sort_list(object_store, dis)
        output: dict[str, dict[str, list[dict[str, any]]]
                     ] = get_mean(sorted_list)
        with open(self.get_filtered_storage(), "w") as f:
            json.dump(output, f)
        return output

    def get_filtered_storage(self):
        return join(self._path, FILENAME_FILTERED)

    def _get_obj_tree(self) -> dict[str, dict[str, list[dict]]]:
        object_store: dict[str, dict[str, list[dict]]] = {}
        for items in self.get_items():
            for obj in items["found_objs"]:
                d = object_store.setdefault(obj["color"], {})
                if obj.get("shape", False):
                    d.setdefault(obj["shape"], []).append(obj)
                else:
                    d.setdefault("all", []).append(obj)
                obj["time"] = items["time"]
        return object_store

    def _save(self) -> None:
        with open(join(self._path, FILENAME), "a") as f:
            for item in self.get_items()[self.saved:]:
                f.write(json.dumps(item) + "\n")
            self.saved = len(self.list)

    def __enter__(self) -> DataItem:
        return self._get_new_item()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._save()


def sort_list(object_store: dict[str, dict[str, list[dict]]], dis: float):
    sorted_list: dict[str, dict[str, dict[int, list]]] = {}
    for color, shapes in object_store.items():
        sorted_list[color] = {}
        array = []
        if "all" in shapes.keys():
            array = shapes["all"].copy()

        for shape, objs in shapes.items():
            if shape == "all":
                continue
            sorted_list[color][shape] = {}
            a = array.copy() + objs
            a_list = np.array([np.array(o["lat_lon"]) for o in a])

            if len(a_list) == 1:
                sorted_list[color][shape][0] = [a[0]]
                continue

            labels = fclusterdata(
                a_list, t=dis)
            for i, o in enumerate(a):
                sorted_list[color][shape].setdefault(
                    int(labels[i]), []).append(o)

    return sorted_list


def get_mean(sorted_list: dict[str, dict[str, dict[int, list]]]):
    output: dict[str, dict[str, list[dict[str, any]]]] = {}
    for color, shapes in sorted_list.items():
        output[color] = {}
        for shape, objs in shapes.items():
            output[color][shape] = []
            for _, obj in objs.items():
                n = len(obj)
                lat = 0
                lon = 0
                time = []
                id = []
                for cap in obj:
                    lat += cap["lat_lon"][0]
                    lon += cap["lat_lon"][1]
                    time.append(cap["time"])
                    id.append(cap["id"])

                output[color][shape].append({
                    "lat": lat/n,
                    "lon": lon/n,
                    "time": time,
                    "id": id,
                })
    return output
