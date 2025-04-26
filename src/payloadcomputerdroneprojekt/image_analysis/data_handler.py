from payloadcomputerdroneprojekt.image_analysis.data_item import DataItem
import json
from os.path import exists, join
from os import makedirs


class DataHandler:
    def __init__(self, path: str):
        if not exists(path):
            makedirs(path)

        self._path = path
        
        print(f"Mission Path: {path}")
        self._list: list[DataItem] = []

    def _get_new_item(self) -> DataItem:
        new_item = DataItem(self._path)
        self._list.append(new_item)
        return new_item

    def _save(self) -> None:
        data = [item.get_dict() for item in self._list]
        with open(join(self._path, "data.json"), "w") as f:
            json.dump(data, f)

    def __enter__(self) -> DataItem:
        return self._get_new_item()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._save()
