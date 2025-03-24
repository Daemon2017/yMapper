import json
import math
import multiprocessing
import os
import time
import urllib
from itertools import compress, repeat

import numpy as np
import pandas as pd
from shapely.geometry import Point
from shapely.geometry import Polygon

ROWS_IN_DF_COUNT_TEXT = 'В наборе данных {} {} строк'
NUMBER_OF_REPRESENTATIVES_OF_EACH_SNP_TEXT = 'Количество представителей каждого SNP:\n{}'

LNG = 'lng'
LAT = 'lat'
KIT_NUMBER = 'Kit Number'
SHORT_HAND = 'Short Hand'
NGS = 'NGS'


def get_dict(snps, json_tree_rows, child_snps):
    old_to_new_dict = {}
    for snp in snps:
        parent_list = get_parent_list(json_tree_rows, snp)
        intersection_list = list(set(parent_list) & set(child_snps))
        if len(intersection_list) == 1:
            old_to_new_dict[snp] = intersection_list[0]
        else:
            old_to_new_dict[snp] = 'Other'
    return old_to_new_dict


def get_positive_snps(polygon, child_snps, combined_df):
    snps_list = [False] * len(child_snps)
    bounds = polygon.bounds
    combined_df = combined_df.loc[(combined_df[LNG] >= bounds[0]) & (combined_df[LNG] <= bounds[2]) &
                                  (combined_df[LAT] >= bounds[1]) & (combined_df[LAT] <= bounds[3])]
    for i, row in combined_df.iterrows():
        if polygon.contains(Point(combined_df.at[i, LNG], combined_df.at[i, LAT])):
            n = 0
            for snp in child_snps:
                if combined_df.at[i, SHORT_HAND] == snp:
                    snps_list[n] = True
                    break
                n = n + 1
    return snps_list


def get_combined_df():
    print('Загружаем набор данных SNP+STR+Map.')
    combined_df = pd.read_csv('combined_snp_str_map.csv', engine='python')
    print('В загруженном наборе данных {} строк'.format(len(combined_df.index)))
    print(NUMBER_OF_REPRESENTATIVES_OF_EACH_SNP_TEXT.format(combined_df[SHORT_HAND].value_counts()))
    return combined_df


def get_child_snps(json_tree_rows, target_snp):
    print("Получаем список дочерних SNP целевого SNP.")
    child_snps = get_children_list(json_tree_rows, target_snp)
    print('Дочерние SNP: {}'.format(child_snps))
    return child_snps


def get_polygon_list_list(h_list, y_0, y_1, x_0, x_1):
    print("Создаем столько сеток из шестиугольников, сколько размеров было задано на 1-м шаге.")
    polygon_list_list = []
    for h in h_list:
        print('Создаем сетку размером {}'.format(h))
        polygon_list = []
        is_even = False
        for lat in np.arange(y_0,
                             y_0 + y_1,
                             (math.sin(math.radians(30)) * h - math.sin(math.radians(270)) * h)):
            if is_even:
                is_even = False
                x_0 = x_0 + (math.cos(math.radians(30)) * h -
                             math.cos(math.radians(150)) * h) / 2
            else:
                is_even = True
                x_0 = x_0 - (math.cos(math.radians(30)) * h -
                             math.cos(math.radians(150)) * h) / 2
            for lon in np.arange(x_0,
                                 x_0 + x_1,
                                 (math.cos(math.radians(30)) * h - math.cos(math.radians(150)) * h)):
                polygon_list.append(Polygon([[lon + math.cos(math.radians(angle)) * h,
                                              lat + math.sin(math.radians(angle)) * h]
                                             for angle in range(30, 360, 60)]))
        polygon_list_list.append(polygon_list)
    return polygon_list_list


def get_df_positive_snps(child_snps, combined_df, json_tree_rows):
    print('Удаляем строки, для которых FTDNA, в силу каких-то причин, не указало SNP.')
    combined_df = combined_df[combined_df[SHORT_HAND].notna()]
    print(ROWS_IN_DF_COUNT_TEXT.format('combined_df', len(combined_df.index)))
    print(NUMBER_OF_REPRESENTATIVES_OF_EACH_SNP_TEXT.format(combined_df[SHORT_HAND].value_counts()))

    combined_df = combined_df[combined_df[SHORT_HAND].str.contains(child_snps[0][:2])]

    start_time = time.time()
    print('Среди всех строк ищем те, что имеют положительный SNP, '
          'восходящий к одному из дочерних SNP целевого SNP.')
    num_processes = multiprocessing.cpu_count()
    unique_values = combined_df[SHORT_HAND].unique()
    chunks = np.array_split(unique_values, num_processes)
    with multiprocessing.Pool(processes=num_processes) as pool:
        result = pool.starmap(get_dict,
                              zip(chunks, repeat(json_tree_rows), repeat(child_snps)))
        old_to_new_dict = {}
        for i in range(len(result)):
            old_to_new_dict.update(result[i])
        combined_df[SHORT_HAND] = combined_df[SHORT_HAND].map(old_to_new_dict)
    print("Метод get_df_positive_snps выполнен за {} с".format(time.time() - start_time))
    return combined_df


def get_map(combined_df, polygon_list_list, child_snps, target_snp, h_list, db, collection_name):
    print('Оставляем только полезные столбцы.')
    important_columns_list = [SHORT_HAND, LNG, LAT]
    for column in combined_df:
        if column not in important_columns_list:
            try:
                del combined_df[column]
            except KeyError as KE:
                print(KE)

    print('Очищаем набор данных от строк с пустыми координатами...')
    combined_df[LNG] = combined_df[LNG].astype(float)
    combined_df = combined_df[combined_df[LNG].notna()].copy()
    combined_df[LAT] = combined_df[LAT].astype(float)
    combined_df = combined_df[combined_df[LAT].notna()]
    print(ROWS_IN_DF_COUNT_TEXT.format('combined_df', len(combined_df.index)))
    print(NUMBER_OF_REPRESENTATIVES_OF_EACH_SNP_TEXT.format(combined_df[SHORT_HAND].value_counts()))

    print("Проверяем наличие каждого целевого SNP в каждом шестиугольнике каждой сетки.")
    current_snps_list_list = []
    for polygon_list, h in zip(polygon_list_list, h_list):
        print('Проверяем сетку размером {}'.format(h))
        current_snps_list = []
        with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
            result = pool.starmap(get_positive_snps,
                                  zip(polygon_list, repeat(child_snps), repeat(combined_df)))
            for r in result:
                current_snps_list.append(r)
            current_snps_list_list.append(current_snps_list)

    get_online_map(child_snps, current_snps_list_list, polygon_list_list, target_snp, db, collection_name)


def get_online_map(child_snps, current_snps_list_list, polygon_list_list, target_snp, db, collection_name):
    snp_data_list = []
    for snps_list, polygon in zip(current_snps_list_list[0], polygon_list_list[0]):
        count = sum(snps_list)
        if count > 0:
            snp_data = {'count': count, 'lat': polygon.centroid.y, 'lng': polygon.centroid.x,
                        'snpsList': list(compress(child_snps, snps_list))}
            snp_data_list.append(snp_data)

    json_string = json.dumps(snp_data_list)
    doc_ref = db.collection(collection_name).document(target_snp)
    doc_ref.set({
        u'data': json_string
    })


def get_df_without_other(combined_df):
    print('Отбрасываем строки, содержащие "Other" в столбце "Short Hand".')
    combined_df = combined_df.drop(combined_df[combined_df[SHORT_HAND] == 'Other'].index)
    print(ROWS_IN_DF_COUNT_TEXT.format('combined_df', len(combined_df.index)))
    print(NUMBER_OF_REPRESENTATIVES_OF_EACH_SNP_TEXT.format(combined_df[SHORT_HAND].value_counts()))
    return combined_df


def get_json_tree_rows():
    print("Открываем древо Y-SNP от FTDNA.")
    file_name = 'ftdna_tree.json'
    if file_name in os.listdir('./'):
        print('Файл с древом найден!')
        with open(file_name, 'r', encoding='utf-8') as file:
            json_tree_rows = json.loads(file.read())
            print('JSON разобран!')
            return json_tree_rows
    else:
        print('Файл с древом не найден! Загружаю его с сайта FTDNA...')
        with urllib.request.urlopen('https://www.familytreedna.com/public/y-dna-haplotree/get') as response:
            decoded_response = response.read().decode()
            print('Страница загружена!')
            json_tree_rows = json.loads(decoded_response)
            print('JSON разобран!')
            with open(file_name, 'w', encoding='utf-8') as text_file:
                text_file.write(decoded_response)
            return json_tree_rows


def get_parent_list(json_rows, snp):
    parent_list = []
    for haplogroup_id in json_rows['allNodes'].keys():
        if snp == json_rows['allNodes'][str(haplogroup_id)]['name']:
            while True:
                parent_list.append(json_rows['allNodes'][str(haplogroup_id)]['name'])
                if 'parentId' in json_rows['allNodes'][str(haplogroup_id)]:
                    haplogroup_id = json_rows['allNodes'][str(haplogroup_id)]['parentId']
                else:
                    break
            break
    return parent_list


def get_children_list(json_rows, snp):
    children_list = []
    for haplogroup_id in json_rows['allNodes'].keys():
        if snp == json_rows['allNodes'][str(haplogroup_id)]['name']:
            if 'children' in json_rows['allNodes'][str(haplogroup_id)]:
                for children in json_rows['allNodes'][str(haplogroup_id)]['children']:
                    children_list.append(json_rows['allNodes'][str(children)]['name'])
            break
    return children_list


def update_db_list(collection_name, db, snps_list):
    doc_ref = db.collection(collection_name).document('list')
    doc_ref.set({
        u'data': json.dumps(snps_list)
    })


def get_snps_list(collection_name, db):
    collection_ref = db.collection(collection_name)
    collection = collection_ref.get()

    snps_list = []
    for snp in collection:
        if snp.id != 'list':
            snps_list.append(snp.id)
    return snps_list
