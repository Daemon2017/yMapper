import numpy as np
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
    df = pd.DataFrame.from_records(response)
    if 'centroids' not in df.columns or 'snp' not in df.columns:
        return []
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


def calculate_homeland(response):
    if not response:
        return []
    df = pd.DataFrame(response)
    df['diversity'] = df['sons_info'].str.len()
    df['min_dt'] = df['sons_info'].apply(lambda x: min(s['dt'] for s in x) if x else 0)
    df['vavilov_score'] = np.log1p(df['diversity'])
    df['tmrca_score'] = 1 / np.log1p(df['min_dt'] + 1)
    df['total_score'] = df['vavilov_score'] * df['tmrca_score']
    max_score = df['total_score'].max()
    if max_score == 0:
        return []
    df['level'] = ((df['total_score'] / max_score) * 100).round(2)
    df = df.groupby('level') \
        .agg({'h3_index': list, 'vavilov_score': 'mean', 'tmrca_score': 'mean'}).reset_index() \
        .rename(columns={'h3_index': 'centroids'}) \
        .sort_values(by='level', ascending=False)
    return df.head(100).to_dict(orient='records')
