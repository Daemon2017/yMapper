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
