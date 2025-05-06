import numpy as np
import math
from scipy.spatial.transform import Rotation as R
from pyproj import CRS, Transformer

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

def local_to_global(initial_global_lat, initial_global_lon, nord_loc, ost_loc):
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

    x_local = ost_loc
    y_local = nord_loc 

    # Umwandlung in GPS
    lon, lat = to_global.transform(x_local, y_local)
    return lon, lat
