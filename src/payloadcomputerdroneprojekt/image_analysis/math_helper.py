import numpy as np
import math


def add_latlonalt(obj, pos, rot, imagesize, fov):
    return
    px, py = obj["x_center"], obj["y_center"]
    local_vec = compute_local(px, py, rot, imagesize, fov)
    obj["latlonalt"] = []


def compute_local(px, py, rot, imagesize, fov):
    return rotation_matrix(rot) * compute_pixel_vec(px, py, imagesize, fov)


def compute_pixel_vec(px, py, imagesize, fov):
    x = px/(imagesize[0]/2) - 0.5
    y = py/(imagesize[1]/2) - 0.5

    return np.array([x * math.sin(fov[0]), y * math.sin(fov[1]), 1])


def rotation_matrix(rot):
    return np.array()
