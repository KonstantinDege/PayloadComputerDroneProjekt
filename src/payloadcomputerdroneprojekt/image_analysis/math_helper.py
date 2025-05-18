import numpy as np
import math
from scipy.spatial.transform import Rotation as R
from pyproj import CRS, Transformer


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
