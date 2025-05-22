from mavsdk.telemetry import PositionVelocityNed, PositionNed, VelocityNed
import math
from scipy.spatial.transform import Rotation as R
from payloadcomputerdroneprojekt.helper import smart_print as sp


def save_execute(msg):
    def wrapper(f):
        def wrap(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                sp(f"{msg}, Error: {e}")
        return wrap
    return wrapper


def reached_pos(target: list, error=0.5, error_vel=0.1):
    def func(state: PositionVelocityNed):
        return (pythagoras(get_pos_vec(state), target) < error
                ) and (abs_vel(get_vel_vec(state)) < error_vel)
    return func


def get_pos_vec(state: PositionVelocityNed):
    pos: PositionNed = state.position
    return [pos.north_m, pos.east_m, pos.down_m]


def get_vel_vec(state: PositionVelocityNed):
    pos: VelocityNed = state.velocity
    return [pos.north_m_s, pos.east_m_s, pos.down_m_s]


def abs_vel(vec):
    return math.sqrt(
        sum([v**2 for v in vec]))


def pythagoras(pos_a, pos_b):
    return math.sqrt(
        sum([(pos_a[i] - pos_b[i])**2 for i in range(len(pos_a))]))


async def get_data(func):
    async for res in func:
        return res


async def wait_for(func, b):
    async for res in func:
        if b(res):
            return res


def rotation_matrix_yaw(rot):
    return R.from_euler('z', [rot], degrees=True).as_matrix()
