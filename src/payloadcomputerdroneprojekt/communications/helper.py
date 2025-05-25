from mavsdk.telemetry import PositionVelocityNed, PositionNed, VelocityNed
import math
from scipy.spatial.transform import Rotation as R
from payloadcomputerdroneprojekt.helper import smart_print as sp


def save_execute(msg):
    """
    Decorator to wrap a function and catch exceptions, printing a message if an
    error occurs.

    :param msg: Message to print if an exception is raised.
    :type msg: str
    :return: Decorator function.
    :rtype: function
    """
    def wrapper(f):
        def wrap(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                sp(f"{msg}, Error: {e}")
        return wrap
    return wrapper


def reached_pos(target: list, error=0.5, error_vel=0.1):
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
    def func(state: PositionVelocityNed):
        return (pythagoras(get_pos_vec(state), target) < error
                ) and (abs_vel(get_vel_vec(state)) < error_vel)
    return func


def get_pos_vec(state: PositionVelocityNed):
    """
    Extracts the position vector from a PositionVelocityNed object.

    :param state: MAVSDK PositionVelocityNed object.
    :type state: PositionVelocityNed
    :return: Position as [north, east, down] in meters.
    :rtype: list
    """
    pos: PositionNed = state.position
    return [pos.north_m, pos.east_m, pos.down_m]


def get_vel_vec(state: PositionVelocityNed):
    """
    Extracts the velocity vector from a PositionVelocityNed object.

    :param state: MAVSDK PositionVelocityNed object.
    :type state: PositionVelocityNed
    :return: Velocity as [north, east, down] in m/s.
    :rtype: list
    """
    pos: VelocityNed = state.velocity
    return [pos.north_m_s, pos.east_m_s, pos.down_m_s]


def abs_vel(vec):
    """
    Calculates the magnitude of a velocity vector.

    :param vec: Velocity vector [vx, vy, vz].
    :type vec: list
    :return: Magnitude of velocity.
    :rtype: float
    """
    return math.sqrt(
        sum([v**2 for v in vec]))


def pythagoras(pos_a, pos_b):
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


async def get_data(func):
    """
    Asynchronously retrieves the first result from an async generator.

    :param func: Asynchronous generator function.
    :type func: async generator
    :return: First result from the generator.
    """
    async for res in func:
        return res


async def wait_for(func, b):
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


def rotation_matrix_yaw(rot):
    """
    Creates a 3x3 rotation matrix for a yaw (Z-axis) rotation.

    :param rot: Yaw rotation in degrees.
    :type rot: float
    :return: 3x3 rotation matrix.
    :rtype: numpy.ndarray
    """
    # Using scipy's Rotation to create a rotation matrix for yaw (Z-axis)
    return R.from_euler('z', [rot], degrees=True).as_matrix()
