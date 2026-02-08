import math

import numpy as np
from shapely import Polygon, Point


def get_hexagon(size, lng_start, lng_end, lng_target, lat_start, lat_end, lat_target):
    height = 1.5 * size
    width = math.sqrt(3) * size

    angles = np.radians(np.arange(30, 360, 60))
    v_x = np.cos(angles) * size
    v_y = np.sin(angles) * size
    vertices_template = np.stack([v_x, v_y], axis=1)

    target_point = Point(lng_target, lat_target)

    for i, lat in enumerate(np.arange(lat_start, lat_end, height)):
        current_lng_start = lng_start + (width / 2 if i % 2 == 0 else 0)
        for lng in np.arange(current_lng_start, lng_end, width):
            coords = np.array([lng, lat]) + vertices_template
            poly = Polygon(coords)
            if poly.contains(target_point):
                return poly
    return None
