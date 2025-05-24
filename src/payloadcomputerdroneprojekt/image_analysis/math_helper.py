import numpy as np
import math
from scipy.spatial.transform import Rotation as R
from pyproj import CRS, Transformer
from itertools import permutations


def compute_local(px, py, rot, imagesize, fov):
    rot_mat = rotation_matrix(rot)
    return rot_mat @ compute_pixel_vec(px, py, imagesize, fov)


def compute_pixel_vec(px, py, imagesize, fov):
    x = (px/imagesize[1]-0.5) * 2
    y = (py/imagesize[0]-0.5) * 2

    return np.array([-y * math.tan(math.radians(fov[1]/2)),
                     x * math.tan(math.radians(fov[0]/2)), 1])


def rotation_matrix(rot):
    return R.from_euler('zyx', rot[::-1], degrees=True).as_matrix()


def local_to_global(initial_global_lat, initial_global_lon):
    origin_lat = initial_global_lat
    origin_lon = initial_global_lon

    crs_global = CRS.from_epsg(4326)  # WGS84

    # Lokales System mit Ursprung am GPS-Punkt
    proj_string = (
        f"+proj=tmerc +lat_0={origin_lat} +lon_0={origin_lon} "
        "+k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
    )
    crs_local = CRS.from_proj4(proj_string)

    to_global = Transformer.from_crs(crs_local, crs_global, always_xy=True)

    def loc_to_glo(x, y):
        return to_global.transform(y, x)
    return loc_to_glo


def find_rel_position(points: list):
    for t_l, b_l, t_r in permutations(points, 3):
        v1 = np.array(b_l) - np.array(t_l)
        v2 = np.array(t_r) - np.array(t_l)

        if np.isclose(np.dot(v1, v2), 0, atol=0.01):
            if np.cross(v1, v2)[2] > 0:
                return t_l, b_l, t_r


def compute_rotation_angle(t_l, b_l):
    v1 = np.array(b_l) - np.array(t_l)

    angle = np.arctan2(v1[1], v1[0]) * 180 / np.pi

    return float(angle)


def find_shorts_longs(points: list):
    points = sorted(points, key=lambda p: (p[1], p[0]))

    t_l, t_r, b_r, b_l = points

    width1 = np.linalg.norm(np.array(t_r) - np.array(t_l))
    width2 = np.linalg.norm(np.array(b_r) - np.array(b_l))
    height1 = np.linalg.norm(np.array(b_l) - np.array(t_l))
    height2 = np.linalg.norm(np.array(b_r) - np.array(t_r))

    return (max(width1, width2), max(height1, height2)), \
        (min(width1, width2), min(height1, height2))
