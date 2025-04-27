from payloadcomputerdroneprojekt.image_analysis.data_item import DataItem
import json
from os.path import exists, join
from os import makedirs

FILENAME = "__data__.json"


class DataHandler:
    def __init__(self, path: str):
        if not exists(path):
            makedirs(path)
        self._path = path
        print(f"Mission Path: {path}")
        self._list: list[DataItem] = []

        if exists(join(self._path, FILENAME)):
            print("loading already existing data")
            with open(join(self._path, FILENAME), "r") as f:
                self._list = json.load(f)

    def _get_new_item(self) -> DataItem:
        new_item = DataItem(self._path)
        new_item._id = len(self._list)
        self._list.append(new_item)
        return new_item

    def get_items(self):
        return [item.get_dict() for item in self._list]

    def _save(self) -> None:
        with open(join(self._path, FILENAME), "w") as f:
            json.dump(self.get_items(), f)

    def __enter__(self) -> DataItem:
        return self._get_new_item()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._save()
