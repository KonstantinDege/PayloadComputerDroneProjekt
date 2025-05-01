import numpy as np
import math
from scipy.spatial.transform import Rotation as R


def compute_local(px, py, rot, imagesize, fov):
    return rotation_matrix(rot) @ compute_pixel_vec(px, py, imagesize, fov)


def compute_pixel_vec(px, py, imagesize, fov):
    x = px/(imagesize[0]/2) - 1
    y = py/(imagesize[1]/2) - 1

    return np.array([x * math.tan(fov[0]), y * math.tan(fov[1]), 1])


def rotation_matrix(rot):
    return R.from_euler('xyz', rot, degrees=True).as_matrix()
