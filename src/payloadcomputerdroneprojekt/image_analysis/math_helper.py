import numpy as np
import math
from scipy.spatial.transform import Rotation as R
from pyproj import CRS, Transformer
from itertools import permutations
from numpy.linalg import norm


def compute_local(pixel_x, pixel_y, rotation_angles,
                  image_size, field_of_view):
    """
    Computes the local 3D direction vector for a given pixel in the image,
    considering camera rotation.

    :param pixel_x: Pixel x-coordinate.
    :type pixel_x: int or float
    :param pixel_y: Pixel y-coordinate.
    :type pixel_y: int or float
    :param rotation_angles: Camera rotation angles (roll, pitch, yaw) in
        degrees.
    :type rotation_angles: list or np.ndarray
    :param image_size: Image size as (height, width).
    :type image_size: tuple
    :param field_of_view: Field of view as (horizontal_fov, vertical_fov) in
        degrees.
    :type field_of_view: tuple
    :return: Local 3D direction vector.
    :rtype: np.ndarray
    """
    rotation_mat = rotation_matrix(rotation_angles)
    return rotation_mat @ compute_pixel_vec(
        pixel_x, pixel_y, image_size, field_of_view)


def compute_pixel_vec(pixel_x, pixel_y, image_size, field_of_view):
    """
    Computes the normalized direction vector from the camera center to a pixel
    in the image.

    :param pixel_x: Pixel x-coordinate.
    :type pixel_x: int or float
    :param pixel_y: Pixel y-coordinate.
    :type pixel_y: int or float
    :param image_size: Image size as (height, width).
    :type image_size: tuple
    :param field_of_view: Field of view as (horizontal_fov, vertical_fov) in
        degrees.
    :type field_of_view: tuple
    :return: Normalized direction vector.
    :rtype: np.ndarray
    """
    # Normalize pixel coordinates to range [-1, 1]
    norm_x = (pixel_x / image_size[1] - 0.5) * 2
    norm_y = (pixel_y / image_size[0] - 0.5) * 2

    # Calculate direction vector based on FOV
    return np.array([
        -norm_y * math.tan(math.radians(field_of_view[1] / 2)),
        norm_x * math.tan(math.radians(field_of_view[0] / 2)),
        1
    ])


def rotation_matrix(rotation_angles):
    """
    Creates a rotation matrix from Euler angles.

    :param rotation_angles: Rotation angles (roll, pitch, yaw) in degrees.
    :type rotation_angles: list or np.ndarray
    :return: 3x3 rotation matrix.
    :rtype: np.ndarray
    """
    # Note: rotation_angles[::-1] reverses the order for 'zyx' convention
    return R.from_euler('zyx', rotation_angles[::-1], degrees=True).as_matrix()


def local_to_global(origin_latitude, origin_longitude):
    """
    Returns a function to convert local (x, y) coordinates to global (lat, lon)
    coordinates.

    :param origin_latitude: Latitude of the origin.
    :type origin_latitude: float
    :param origin_longitude: Longitude of the origin.
    :type origin_longitude: float
    :return: Function that converts (x, y) to (lat, lon).
    :rtype: function
    """
    crs_global = CRS.from_epsg(4326)  # WGS84

    # Define local coordinate system centered at the GPS point
    proj_string = (
        f"+proj=tmerc +lat_0={origin_latitude} +lon_0={origin_longitude} "
        "+k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
    )
    crs_local = CRS.from_proj4(proj_string)

    to_global_transformer = Transformer.from_crs(
        crs_local, crs_global, always_xy=True)

    def convert_local_to_global(local_x, local_y):
        """
        Converts local (x, y) to global (lat, lon).

        :param local_x: Local x-coordinate (meters).
        :type local_x: float
        :param local_y: Local y-coordinate (meters).
        :type local_y: float
        :return: (lat, lon) tuple.
        :rtype: tuple
        """
        return to_global_transformer.transform(local_y, local_x)
    return convert_local_to_global


def find_relative_position(points: list):
    """
    Finds the relative positions of three points such that two vectors are
    orthogonal and the cross product is positive.

    :param points: List of 3D points.
    :type points: list
    :return: Tuple of points (top_left, bottom_left, top_right) if found, else
        None.
    :rtype: tuple or None
    """
    outs = []
    for top_left, bottom_left, top_right in permutations(points, 3):
        vec1 = np.array(bottom_left) - np.array(top_left)
        vec2 = np.array(top_right) - np.array(top_left)

        # Check if vectors are orthogonal
        if np.cross(vec1, vec2)[2] > 0:
            outs.append((np.dot(vec1, vec2), top_left, bottom_left, top_right))
            if np.isclose(np.dot(vec1, vec2), 0, atol=0.05):
                # Check orientation using cross product
                return top_left, bottom_left, top_right

    closest = sorted(outs, key=lambda x: x[0])[0]

    return closest[1], closest[2], closest[3]


def compute_rotation_angle(top_left, bottom_left):
    """
    Computes the rotation angle (in degrees) between two points.

    :param top_left: Top-left point (x, y).
    :type top_left: tuple or np.ndarray
    :param bottom_left: Bottom-left point (x, y).
    :type bottom_left: tuple or np.ndarray
    :return: Rotation angle in degrees.
    :rtype: float
    """
    vec = np.array(bottom_left) - np.array(top_left)
    angle = np.arctan2(vec[1], vec[0]) * 180 / np.pi
    return float(angle)


def find_shortest_longest_sides(points: list):
    """
    Finds the shortest and longest sides of a quadrilateral defined by four
    points.

    :param points: List of four (x, y) points.
    :type points: list
    :return: Tuple of (longest sides), (shortest sides).
    :rtype: tuple
    """
    # Sort points by y, then x to get consistent order
    points_sorted = sorted(points, key=lambda p: (p[1], p[0]))

    top_left, top_right, bottom_right, bottom_left = points_sorted

    width_top = norm(np.array(top_right) - np.array(top_left))
    width_bottom = norm(np.array(bottom_right) - np.array(bottom_left))
    height_left = norm(np.array(bottom_left) - np.array(top_left))
    height_right = norm(np.array(bottom_right) - np.array(top_right))

    return (max(width_top, width_bottom), max(height_left, height_right)), \
        (min(width_top, width_bottom), min(height_left, height_right))
