import math

import h3
import pandas as pd


def get_input(args, body):
    a_points = body.get('a_points')
    b_points = body.get('b_points')
    size = args.get('size')
    start = args.get('start')
    end = args.get('end')
    group = args.get('group', 'false').lower() == 'true'
    return a_points, b_points, start, end, group, size


def process_centroids(response, group):
    if not response:
        return {}
    df = pd.DataFrame.from_records(response)
    if 'centroids' not in df.columns or 'snp' not in df.columns:
        return {}
    df = df.explode('centroids').rename(columns={'centroids': 'centroid'})
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


def get_weighted_median(values, weights):
    combined = sorted(zip(values, weights))
    total_weight = sum(weights)
    cumulative_weight = 0
    for val, weight in combined:
        cumulative_weight += weight
        if cumulative_weight >= total_weight / 2:
            return val
    return values[0] if values else 0


def calculate_homeland(response, mode):
    if not response:
        return None
    lats = []
    lngs = []
    weights = []
    max_diversity = 0
    for row in response:
        lat, lng = h3.cell_to_latlng(row['h3_index'])
        if not (-30 <= lng <= 170):
            continue
        current_diversity = len(row['sons_info'])
        if current_diversity > max_diversity:
            max_diversity = current_diversity
        vavilov = current_diversity ** 2
        if mode == 'geometric':
            weight = 1
        elif mode == 'vavilov':
            weight = vavilov
        elif mode == 'time_weighted':
            weight = sum(1 / (math.log(s['dt'] + 2)) for s in row['sons_info']) * vavilov
        else:
            weight = 1
        lats.append(lat)
        lngs.append(lng)
        weights.append(weight)
    if not weights or sum(weights) == 0:
        return None
    center_lat = get_weighted_median(lats, weights)
    center_lng = get_weighted_median(lngs, weights)
    total_weight = sum(weights)
    sum_sq_dist = 0
    for i in range(len(lats)):
        dist_sq = (lats[i] - center_lat) ** 2 + (lngs[i] - center_lng) ** 2
        sum_sq_dist += dist_sq * weights[i]
    std_dev = math.sqrt(sum_sq_dist / total_weight) if total_weight > 0 else 0
    uncertainty_km = std_dev * 111
    return {
        "lat": center_lat,
        "lng": center_lng,
        "uncertainty_km": uncertainty_km,
        "diversity_max": max_diversity,
        "hex_count": len(response)
    }
