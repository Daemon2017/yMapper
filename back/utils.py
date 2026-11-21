import math
import re

import numpy as np
import pandas as pd


def get_input(args, body):
    a_points = body.get('a_points')
    b_points = body.get('b_points')
    size = args.get('size')
    start = args.get('start')
    end = args.get('end')
    group_mode = args.get('group', 'combined').lower()
    snp = args.get('snp')
    raw_exclude = args.get('exclude_snps', '')
    exclude_snps = [s.strip() for s in re.split(r'[,\s]+', raw_exclude) if s.strip()]
    return a_points, b_points, start, end, group_mode, size, snp, exclude_snps


def process_centroids(response, group_mode):
    df = pd.DataFrame.from_records(response)
    if 'centroids' not in df.columns or 'snp' not in df.columns:
        return []
    df = df.explode('centroids').rename(columns={'centroids': 'centroid'})
    if group_mode == 'grouped':
        df = df.groupby('centroid')['snp'].nunique().reset_index() \
            .groupby('snp')['centroid'].agg(list).reset_index() \
            .rename(columns={'snp': 'level', 'centroid': 'centroids'}) \
            .sort_values(by='level', ascending=False)
    elif group_mode == 'combined':
        df = df.groupby('centroid')['snp'].apply(lambda x: tuple(sorted(set(x)))).reset_index() \
            .groupby('snp')['centroid'].agg(list).reset_index() \
            .rename(columns={'snp': 'snps', 'centroid': 'centroids'})
        df = df.assign(snps_len=df['snps'].str.len()) \
            .sort_values(by='snps_len', ascending=False) \
            .drop(columns=['snps_len'])
        df['snps'] = df['snps'].apply(lambda x: ", ".join(x))
    else:
        df = df.groupby('snp')['centroid'].agg(list).reset_index() \
            .rename(columns={'snp': 'snps', 'centroid': 'centroids'})
        df['count'] = df['centroids'].str.len()
        df = df.sort_values(by='count', ascending=False).drop(columns=['count'])
    records = df.to_dict(orient='records')
    if group_mode == 'grouped':
        return _collapse_overflow_to_others(records, label_key='level')
    return records[:100]


def process_max_centroids(response, group):
    if not response:
        return []
    df = pd.DataFrame.from_records(response)
    if group:
        winners = df.sort_values(by=['sons_count'], ascending=False) \
            .groupby('h3_index').head(1)
        final_groups = winners.groupby('sons_count')['h3_index'].agg(list).reset_index()
        result = []
        for _, row in final_groups.iterrows():
            lvl = int(row['sons_count'])
            result.append({
                'level': lvl,
                'centroids': row['h3_index'],
                'snps': f"Max Sons: {lvl}"
            })
        sorted_res = sorted(result, key=lambda x: x['level'], reverse=True)
        return _collapse_overflow_to_others(sorted_res, label_key='level')
    else:
        df = df.sample(frac=1).reset_index(drop=True)
        idx_winners = df.sort_values(by='sons_count', ascending=False) \
            .groupby('h3_index').head(1)
        result_df = idx_winners.groupby('snp')['h3_index'] \
            .agg(list).reset_index() \
            .rename(columns={'snp': 'snps', 'h3_index': 'centroids'})
        result_df['count'] = result_df['centroids'].str.len()
        return result_df.sort_values(by='count', ascending=False) \
            .drop(columns=['count']) \
            .head(100).to_dict(orient='records')


def _rarefied_richness(counts, n_sub):
    N = sum(counts)
    if N < n_sub:
        return None
    if n_sub <= 1:
        return 1.0
    log_denom = math.lgamma(N + 1) - math.lgamma(N - n_sub + 1)
    expected_s = 0.0
    for n_i in counts:
        if N - n_i < n_sub:
            prob_absent = 0.0
        else:
            log_num = math.lgamma(N - n_i + 1) - math.lgamma(N - n_i - n_sub + 1)
            prob_absent = math.exp(log_num - log_denom)
        expected_s += (1.0 - prob_absent)
    return expected_s


def calculate_homeland(response, use_stats=False):
    if not response:
        return []
    df = pd.DataFrame(response)
    df['actual_branches'] = df['sons_info'].str.len()
    df['min_dt'] = df['sons_info'].apply(lambda x: min(s['dt'] for s in x) if x else 0)
    df['tmrca_score'] = 1 / np.log1p(df['min_dt'] + 1)

    if use_stats:
        df['counts_list'] = df['sons_info'].apply(lambda x: [s.get('count', 1) for s in x])
        df['total_n'] = df['counts_list'].apply(sum)

        multi_n = df['total_n'][df['total_n'] >= 2]
        if len(multi_n) > 0:
            n_sub = max(2, int(np.floor(np.percentile(multi_n, 34))))
        else:
            n_sub = 1

        df = df[df['total_n'] >= n_sub].copy()
        if df.empty:
            return []

        df['expected_s'] = df['counts_list'].apply(lambda c: _rarefied_richness(c, n_sub))
        df['vavilov_score'] = np.log1p(df['expected_s'])
        df['rarefaction_n'] = n_sub
    else:
        df['vavilov_score'] = np.log1p(df['actual_branches'])
        df['rarefaction_n'] = None

    df['total_score'] = df['vavilov_score'] * df['tmrca_score']

    max_score = df['total_score'].max()
    if max_score == 0:
        return []
    df['level'] = ((df['total_score'] / max_score) * 100).round(2)

    agg_dict = {
        'h3_index': list,
        'vavilov_score': 'mean',
        'tmrca_score': 'mean',
        'actual_branches': 'mean'
    }
    if use_stats:
        agg_dict['rarefaction_n'] = 'first'
        agg_dict['expected_s'] = 'mean'

    df = df.groupby('level') \
        .agg(agg_dict).reset_index() \
        .rename(columns={'h3_index': 'centroids'}) \
        .sort_values(by='level', ascending=False)
    records = df.to_dict(orient='records')
    return _collapse_overflow_to_others(records, label_key='level')


def process_correlation_centroids(response, group_mode):
    if not response:
        return []
    df = pd.DataFrame(response)
    df['intersection'] = df['jaccard_metrics'].apply(lambda x: x['intersection_count'])
    df['union'] = df['jaccard_metrics'].apply(lambda x: x['union_count'])
    df['correlation'] = (df['intersection'] / df['union']).round(4)
    df = df[df['correlation'] >= 0.25]
    if df.empty:
        return []
    df_top_100 = df.sort_values(by='correlation', ascending=False).head(100)
    if group_mode == 'grouped':
        df_exploded = df_top_100.explode('centroids')
        counts = df_exploded.groupby('centroids').size().reset_index(name='frequency')
        max_freq = counts['frequency'].max()
        counts['level'] = ((counts['frequency'] / max_freq) * 100).round(2) if max_freq > 0 else 0.0
        final_groups = counts.groupby('level')['centroids'].agg(list).reset_index()
        result = []
        for _, row in final_groups.iterrows():
            lvl = float(row['level'])
            result.append({
                'level': lvl,
                'centroids': row['centroids'],
                'snps': f"Correlation Intensity: {lvl}%"
            })
        sorted_res = sorted(result, key=lambda x: x['level'], reverse=True)
        return _collapse_overflow_to_others(sorted_res, label_key='level')
    elif group_mode == 'combined':
        records = []
        for _, row in df_top_100.iterrows():
            for c in row['centroids']:
                records.append({'snp': f"{row['snp']} (r={row['correlation']})", 'centroid': c})
        if not records: return []
        comb_df = pd.DataFrame(records)
        comb_df = comb_df.groupby('centroid')['snp'].apply(lambda x: ", ".join(sorted(set(x)))).reset_index()
        comb_df = comb_df.groupby('snp')['centroid'].agg(list).reset_index() \
            .rename(columns={'snp': 'snps', 'centroid': 'centroids'})
        return comb_df.to_dict(orient='records')
    else:
        result = []
        for _, row in df_top_100.iterrows():
            result.append({
                'snps': f"{row['snp']} (r={row['correlation']})",
                'centroids': row['centroids']
            })
        return result


def _collapse_overflow_to_others(records, label_key='level', other_label='Others'):
    if len(records) <= 100:
        return records
    top_99 = records[:99]
    overflow = records[99:]
    other_centroids = []
    seen = set()
    for item in overflow:
        for c in item.get('centroids', []):
            if c not in seen:
                seen.add(c)
                other_centroids.append(c)
    other_entry = {
        label_key: other_label,
        'centroids': other_centroids
    }
    if 'vavilov_score' in overflow[0]:
        other_entry['vavilov_score'] = float(np.mean([x['vavilov_score'] for x in overflow]))
        other_entry['tmrca_score'] = float(np.mean([x['tmrca_score'] for x in overflow]))
    if 'actual_branches' in overflow and overflow['actual_branches'] is not None:
        other_entry['actual_branches'] = float(np.mean([x['actual_branches'] for x in overflow]))
    if 'rarefaction_n' in overflow and overflow['rarefaction_n'] is not None:
        other_entry['rarefaction_n'] = overflow['rarefaction_n']
    if 'expected_s' in overflow and overflow['expected_s'] is not None:
        other_entry['expected_s'] = float(np.mean([x['expected_s'] for x in overflow]))
    return top_99 + [other_entry]
