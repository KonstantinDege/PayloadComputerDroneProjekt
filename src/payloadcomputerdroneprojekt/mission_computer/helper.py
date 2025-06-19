import os
import json
from payloadcomputerdroneprojekt.helper import smart_print as sp


def find_shortest_path(objs: list[dict], start: list[float]
                       ) -> list[list[float]]:
    """
    Find the shortest path to all objects from a starting point.

    The function sorts the positions of the objects based on their Manhattan
    distance from the starting point and returns the sorted list of positions.

    :param objs: List of objects, each with a "pos" key containing coordinates.
    :type objs: list[dict]
    :param start: Starting position as [x, y].
    :type start: list[float]
    :return: Sorted list of positions based on distance from start.
    :rtype: list[list[float]]
    """
    if len(objs) == 0:
        return []
    path = []
    for obj in objs:
        path.append(obj["pos"])
    # Sort positions by Manhattan distance from the start
    path.sort(key=lambda x: abs(x[0] - start[0]) + abs(x[1] - start[1]))
    return path


def count_actions(actions: dict) -> int:
    """
    Recursively count the number of actions in a nested action plan.

    :param actions: Action plan dictionary.
    :type actions: dict
    :return: Total number of actions.
    :rtype: int
    """
    if actions["action"] == "list":
        c = 0
        for item in actions["commands"]:
            c += count_actions(item)
        return c
    elif actions["action"] == "mov_multiple":
        return len(actions["commands"])
    return 1


def action_with_count(plan: dict, count: int):
    """
    Find the next action in the plan and return it with the updated count.

    If the count is 0, returns the plan as is.
    If the count exceeds the number of actions, returns the remaining count.

    :param plan: The action plan.
    :type plan: dict
    :param count: Number of actions to skip.
    :type count: int
    :return: The next action or the remaining count.
    :rtype: dict or int
    """
    if plan["action"] == "list":
        for i, item in enumerate(plan["commands"]):
            ret = action_with_count(item, count)
            if not isinstance(ret, int):
                # Found the next action, return the updated plan
                return {
                    "action": "list",
                    "commands": [ret] + plan["commands"][i+1:]
                }
            count = ret
    elif plan["action"] == "mov_multiple":
        if count < len(plan["commands"]):
            # Return the remaining commands after skipping 'count' actions
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
    """
    Recursively serialize the object to load commands from a file if specified.

    If the object is a dictionary and contains a "src" key, it loads the
    commands from the specified file and updates the object. If the object is a
    list, it recursively serializes each element.

    :param obj: The object to serialize, which can be a dictionary or a list.
    :type obj: dict or list
    """
    if isinstance(obj, dict):
        if "src" in obj.keys():
            if os.path.exists(obj["src"]):
                with open(obj["src"], "r") as f:
                    subobj = json.load(f)
                    obj["action"] = subobj["action"]
                    obj["commands"] = subobj["commands"]
                    # Recursively serialize the loaded commands
                    rec_serialize(subobj["commands"])
            else:
                sp(f"File {obj['src']} not found")
    elif isinstance(obj, list):
        # Recursively serialize each element in the list
        [rec_serialize(i) for i in obj]


def diag(x: float, y: float) -> float:
    """
    Calculate the Euclidean distance from the origin to the point (x, y).

    :param x: X coordinate.
    :type x: float
    :param y: Y coordinate.
    :type y: float
    :return: Euclidean distance.
    :rtype: float
    """
    d = (x**2 + y**2)
    if d == 0:
        return 0.001
    return d


class PIDController:
    def __init__(self, Kp=1.0, Ki=0.0, Kd=0.0, output_limits=(None, None)):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.output_limits = output_limits
        self.reset()

    def reset(self):
        self.integral = 0.0
        self.prev_error = 0.0

    def __call__(self, error, dt):
        if dt <= 0:
            dt = 1e-3
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt
        output = (
            self.Kp * error +
            self.Ki * self.integral +
            self.Kd * derivative
        )
        self.prev_error = error
        min_out, max_out = self.output_limits
        if min_out is not None:
            output = max(min_out, output)
        if max_out is not None:
            output = min(max_out, output)
        return output
