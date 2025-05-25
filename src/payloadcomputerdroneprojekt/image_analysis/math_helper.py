import numpy as np
import math
from scipy.spatial.transform import Rotation as R
from pyproj import CRS, Transformer
from itertools import permutations


def compute_local(px, py, rot, imagesize, fov):
    """
    Computes the local 3D direction vector for a given pixel in the image,
    considering camera rotation.

    :param px: Pixel x-coordinate.
    :type px: int or float
    :param py: Pixel y-coordinate.
    :type py: int or float
    :param rot: Camera rotation angles (roll, pitch, yaw) in degrees.
    :type rot: list or np.ndarray
    :param imagesize: Image size as (height, width).
    :type imagesize: tuple
    :param fov: Field of view as (horizontal_fov, vertical_fov) in degrees.
    :type fov: tuple
    :return: Local 3D direction vector.
    :rtype: np.ndarray
    """
    rot_mat = rotation_matrix(rot)
    return rot_mat @ compute_pixel_vec(px, py, imagesize, fov)


def compute_pixel_vec(px, py, imagesize, fov):
    """
    Computes the normalized direction vector from the camera center to a pixel
    in the image.

    :param px: Pixel x-coordinate.
    :type px: int or float
    :param py: Pixel y-coordinate.
    :type py: int or float
    :param imagesize: Image size as (height, width).
    :type imagesize: tuple
    :param fov: Field of view as (horizontal_fov, vertical_fov) in degrees.
    :type fov: tuple
    :return: Normalized direction vector.
    :rtype: np.ndarray
    """
    # Normalize pixel coordinates to range [-1, 1]
    x = (px/imagesize[1]-0.5) * 2
    y = (py/imagesize[0]-0.5) * 2

    # Calculate direction vector based on FOV
    return np.array([
        -y * math.tan(math.radians(fov[1]/2)),
        x * math.tan(math.radians(fov[0]/2)),
        1
    ])


def rotation_matrix(rot):
    """
    Creates a rotation matrix from Euler angles.

    :param rot: Rotation angles (roll, pitch, yaw) in degrees.
    :type rot: list or np.ndarray
    :return: 3x3 rotation matrix.
    :rtype: np.ndarray
    """
    # Note: rot[::-1] reverses the order for 'zyx' convention
    return R.from_euler('zyx', rot[::-1], degrees=True).as_matrix()


def local_to_global(initial_global_lat, initial_global_lon):
    """
    Returns a function to convert local (x, y) coordinates to global (lat, lon)
    coordinates.

    :param initial_global_lat: Latitude of the origin.
    :type initial_global_lat: float
    :param initial_global_lon: Longitude of the origin.
    :type initial_global_lon: float
    :return: Function that converts (x, y) to (lat, lon).
    :rtype: function
    """
    origin_lat = initial_global_lat
    origin_lon = initial_global_lon

    crs_global = CRS.from_epsg(4326)  # WGS84

    # Define local coordinate system centered at the GPS point
    proj_string = (
        f"+proj=tmerc +lat_0={origin_lat} +lon_0={origin_lon} "
        "+k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
    )
    crs_local = CRS.from_proj4(proj_string)

    to_global = Transformer.from_crs(crs_local, crs_global, always_xy=True)

    def loc_to_glo(x, y):
        """
        Converts local (x, y) to global (lat, lon).

        :param x: Local x-coordinate (meters).
        :type x: float
        :param y: Local y-coordinate (meters).
        :type y: float
        :return: (lat, lon) tuple.
        :rtype: tuple
        """
        return to_global.transform(y, x)
    return loc_to_glo


def find_rel_position(points: list):
    """
    Finds the relative positions of three points such that two vectors are
    orthogonal and the cross product is positive.

    :param points: List of 3D points.
    :type points: list
    :return: Tuple of points (top_left, bottom_left, top_right) if found, else
        None.
    :rtype: tuple or None
    """
    for t_l, b_l, t_r in permutations(points, 3):
        v1 = np.array(b_l) - np.array(t_l)
        v2 = np.array(t_r) - np.array(t_l)

        # Check if vectors are orthogonal
        if np.isclose(np.dot(v1, v2), 0, atol=0.01):
            # Check orientation using cross product
            if np.cross(v1, v2)[2] > 0:
                return t_l, b_l, t_r


def compute_rotation_angle(t_l, b_l):
    """
    Computes the rotation angle (in degrees) between two points.

    :param t_l: Top-left point (x, y).
    :type t_l: tuple or np.ndarray
    :param b_l: Bottom-left point (x, y).
    :type b_l: tuple or np.ndarray
    :return: Rotation angle in degrees.
    :rtype: float
    """
    v1 = np.array(b_l) - np.array(t_l)
    angle = np.arctan2(v1[1], v1[0]) * 180 / np.pi
    return float(angle)


def find_shorts_longs(points: list):
    """
    Finds the shortest and longest sides of a quadrilateral defined by four
    points.

    :param points: List of four (x, y) points.
    :type points: list
    :return: Tuple of (longest sides), (shortest sides).
    :rtype: tuple
    """
    # Sort points by y, then x to get consistent order
    points = sorted(points, key=lambda p: (p[1], p[0]))

    t_l, t_r, b_r, b_l = points

    width1 = np.linalg.norm(np.array(t_r) - np.array(t_l))
    width2 = np.linalg.norm(np.array(b_r) - np.array(b_l))
    height1 = np.linalg.norm(np.array(b_l) - np.array(t_l))
    height2 = np.linalg.norm(np.array(b_r) - np.array(t_r))

    return (max(width1, width2), max(height1, height2)), \
        (min(width1, width2), min(height1, height2))
