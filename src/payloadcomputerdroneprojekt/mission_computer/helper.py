import os
import json
from payloadcomputerdroneprojekt.helper import smart_print as sp


def find_shortest_path(objs: list[dict], start: list[float]):
    """
    find the shortest path to all objects
    """
    if len(objs) == 0:
        return []
    path = []
    for obj in objs:
        path.append(obj["pos"])
    path.sort(key=lambda x: abs(x[0] - start[0]) + abs(x[1] - start[1]))
    return path


def count_actions(actions):
    if actions["action"] == "list":
        c = 0
        for item in actions["commands"]:
            c += count_actions(item)
        return c
    elif actions["action"] == "mov_multiple":
        return len(actions["commands"])
    return 1


def action_with_count(plan, count: int):
    if plan["action"] == "list":
        for i, item in enumerate(plan["commands"]):
            ret = action_with_count(item, count)
            if not isinstance(ret, int):
                return {
                    "action": "list",
                    "commands": [ret] + plan["commands"][i+1:]
                }
            count = ret
    elif plan["action"] == "mov_multiple":
        if count < len(plan["commands"]):
            return {
                "action": "mov_multiple",
                "commands": plan["commands"][count:]
            }
        else:
            return count - len(plan["commands"])

    if count == 0:
        return plan
    return count - 1


def rec_serialize(obj):
    if isinstance(obj, dict):
        if "src" in obj.keys():
            if os.path.exists(obj["src"]):
                with open(obj["src"], "r") as f:
                    subobj = json.load(f)
                    obj["action"] = subobj["action"]
                    obj["commands"] = subobj["commands"]
                    rec_serialize(subobj["commands"])
            else:
                sp(f"File {obj['src']} not found")
    elif isinstance(obj, list):
        [rec_serialize(i) for i in obj]


def diag(x: float, y: float) -> float:
    return (x**2 + y**2)**0.5
