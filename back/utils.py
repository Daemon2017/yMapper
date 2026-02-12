import math
import re

import numpy as np
import pandas as pd
from shapely import Polygon, Point


def get_input(args, body):
    a_points = body.get('a_points')
    b_points = body.get('b_points')
    size = args.get('size')
    start = args.get('start')
    end = args.get('end')
    group = args.get('group', 'false').lower() == 'true'
    return a_points, b_points, start, end, group, size


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


def process_centroids(response, group):
    if not response:
        return {}
    df = pd.DataFrame.from_records(response)
    df = df.explode('centroids').rename(columns={'centroids': 'centroid'})
    df['centroid'] = df['centroid'].map(tuple)
    if group:
        df = df.groupby('centroid')['snp'].nunique().reset_index() \
            .groupby('snp')['centroid'].agg(list).reset_index() \
            .rename(columns={'snp': 'level', 'centroid': 'centroids'}) \
            .sort_values(by='level', ascending=False)
    else:
        df = df.groupby('centroid')['snp'].apply(lambda x: tuple(sorted(set(x)))).reset_index() \
            .groupby('snp')['centroid'].agg(list).reset_index() \
            .rename(columns={'snp': 'snps', 'centroid': 'centroids'})
        df = df.assign(snps_len=df['snps'].str.len()) \
            .sort_values(by='snps_len', ascending=False) \
            .drop(columns=['snps_len'])
    return df.head(100).to_dict(orient='records')


def transform_row(row):
    row = dict(row._mapping)
    centroids = row.get('centroids')
    if isinstance(centroids, str):
        row['centroids'] = parse_pg_point_array(centroids)
    return row


def parse_pg_point_array(pg_string):
    if not pg_string:
        return []
    points = re.findall(r"\(([-+]?\d*\.?\d+),([-+]?\d*\.?\d+)\)", pg_string)
    return [[float(p[0]), float(p[1])] for p in points]
