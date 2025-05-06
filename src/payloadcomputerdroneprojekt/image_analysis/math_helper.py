import numpy as np
import math
from scipy.spatial.transform import Rotation as R


def compute_local(px, py, rot, offset, imagesize, fov):
    return rotation_matrix(rot) @ (
        offset + compute_pixel_vec(px, py, imagesize, fov))


def compute_pixel_vec(px, py, imagesize, fov):
    x = (px-imagesize[1]/2) / imagesize[1]
    y = (py-imagesize[0]/2) / imagesize[0]

    return np.array([-y * math.tan(math.radians(fov[0]/2)),
                     x * math.tan(math.radians(fov[1]/2)), 1])


def rotation_matrix(rot):
    return R.from_euler('xyz', rot, degrees=True).as_matrix()
