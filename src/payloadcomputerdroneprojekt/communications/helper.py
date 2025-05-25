from mavsdk.telemetry import PositionVelocityNed, PositionNed, VelocityNed
import math
from scipy.spatial.transform import Rotation as R
from payloadcomputerdroneprojekt.helper import smart_print as sp
from typing import Callable, AsyncGenerator, List, TypeVar, Optional
import numpy as np
import asyncio

T = TypeVar('T')


def save_execute(msg: str):
    """
    Decorator to wrap a function and catch exceptions, printing a message if an
    error occurs. Works for both sync and async functions.
    """
    def wrapper(f):
        if asyncio.iscoroutinefunction(f):
            async def wrap(*args, **kwargs):
                try:
                    return await f(*args, **kwargs)
                except Exception as e:
                    sp(f"{msg}, Error: {e}")
            return wrap
        else:
            def wrap(*args, **kwargs):
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    sp(f"{msg}, Error: {e}")
            return wrap
    return wrapper


def reached_pos(
    target: List[float], error: float = 0.5, error_vel: float = 0.1
) -> Callable[[PositionVelocityNed], bool]:
    """
    Returns a function that checks if a drone has reached a target position and
    is below a velocity threshold.

    :param target: Target position as [north, east, down] in meters.
    :type target: list
    :param error: Allowed position error in meters.
    :type error: float, optional
    :param error_vel: Allowed velocity error in m/s.
    :type error_vel: float, optional
    :return: Function that takes PositionVelocityNed and returns True if target
        is reached.
    :rtype: function
    """
    def func(state: PositionVelocityNed) -> bool:
        return (pythagoras(get_pos_vec(state), target) < error
                ) and (abs_vel(get_vel_vec(state)) < error_vel)
    return func


def get_pos_vec(state: PositionVelocityNed) -> List[float]:
    """
    Extracts the position vector from a PositionVelocityNed object.

    :param state: MAVSDK PositionVelocityNed object.
    :type state: PositionVelocityNed
    :return: Position as [north, east, down] in meters.
    :rtype: list
    """
    pos: PositionNed = state.position
    return [pos.north_m, pos.east_m, pos.down_m]


def get_vel_vec(state: PositionVelocityNed) -> List[float]:
    """
    Extracts the velocity vector from a PositionVelocityNed object.

    :param state: MAVSDK PositionVelocityNed object.
    :type state: PositionVelocityNed
    :return: Velocity as [north, east, down] in m/s.
    :rtype: list
    """
    vel: VelocityNed = state.velocity
    return [vel.north_m_s, vel.east_m_s, vel.down_m_s]


def abs_vel(vec: List[float]) -> float:
    """
    Calculates the magnitude of a velocity vector.

    :param vec: Velocity vector [vx, vy, vz].
    :type vec: list
    :return: Magnitude of velocity.
    :rtype: float
    """
    return math.sqrt(sum([v**2 for v in vec]))


def pythagoras(pos_a: List[float], pos_b: List[float]) -> float:
    """
    Calculates the Euclidean distance between two position vectors.

    :param pos_a: First position vector [x, y, z].
    :type pos_a: list
    :param pos_b: Second position vector [x, y, z].
    :type pos_b: list
    :return: Euclidean distance.
    :rtype: float
    """
    return math.sqrt(
        sum([(pos_a[i] - pos_b[i])**2 for i in range(len(pos_a))]))


async def get_data(func: AsyncGenerator[T, None]) -> Optional[T]:
    """
    Asynchronously retrieves the first result from an async generator.

    :param func: Asynchronous generator function.
    :type func: async generator
    :return: First result from the generator.
    """
    async for res in func:
        return res


async def wait_for(func: AsyncGenerator[T, None],
                   b: Callable[[T], bool]) -> Optional[T]:
    """
    Asynchronously waits for a condition to be met in an async generator.

    :param func: Asynchronous generator function.
    :type func: async generator
    :param b: Condition function that takes a result and returns True if
        condition is met.
    :type b: function
    :return: First result for which the condition is True.
    """
    async for res in func:
        if b(res):
            return res


def rotation_matrix_yaw(rot: float) -> np.ndarray:
    """
    Creates a 3x3 rotation matrix for a yaw (Z-axis) rotation.

    :param rot: Yaw rotation in degrees.
    :type rot: float
    :return: 3x3 rotation matrix.
    :rtype: numpy.ndarray
    """
    # Using scipy's Rotation to create a rotation matrix for yaw (Z-axis)
    return R.from_euler('z', [rot], degrees=True).as_matrix()
