import datetime
import json
import math
import multiprocessing
import os
import urllib
from itertools import compress, repeat

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier, Pool
from shapely.geometry import Point
from shapely.geometry import Polygon
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split

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
    print(datetime.datetime.now())
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
    print(datetime.datetime.now())
    return combined_df


def get_df_extended(combined_normal_df_without_other, str_number, json_tree_rows, child_snps, combined_original_df):
    print(datetime.datetime.now())
    combined_normal_df_without_other[KIT_NUMBER] = combined_normal_df_without_other[KIT_NUMBER].astype(str)
    combined_extended_map_df = get_df_extended_map(str_number, combined_original_df, json_tree_rows, child_snps)

    if combined_extended_map_df is None:
        return None
    else:
        combined_extended_map_df[KIT_NUMBER] = combined_extended_map_df[KIT_NUMBER].astype(str)
        print('В наборе combined_extended_map_df оставляем только те строки, которых нет в наборе combined_df.')
        combined_extended_map_df = \
            combined_extended_map_df.loc[
                ~combined_extended_map_df[KIT_NUMBER].isin(combined_normal_df_without_other[KIT_NUMBER])]
        print('Присоединяем к набору combined_extended_map_df содержимое набора combined_df.')
        combined_extended_map_df = pd.concat([combined_normal_df_without_other, combined_extended_map_df], sort=True)
        print(ROWS_IN_DF_COUNT_TEXT.format('combined_extended_map_df', len(combined_extended_map_df.index)))
        print("Количество представителей каждой подветви: \n{}"
              .format(combined_extended_map_df[SHORT_HAND].value_counts()))
        print(datetime.datetime.now())
        return combined_extended_map_df


def get_map(combined_df, polygon_list_list, child_snps, target_snp, h_list, db, collection_name):
    print(datetime.datetime.now())
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


def get_df_extended_map(str_number, combined_original_df, json_tree_rows, child_snps):
    print('Выделяем данные о местоположении в отдельный набор.')
    map_df = combined_original_df.filter([KIT_NUMBER, LAT, LNG], axis=1)
    print(ROWS_IN_DF_COUNT_TEXT.format('map_df', len(map_df.index)))

    str_columns_list = get_str_columns_list(str_number)
    utils_columns_list = [SHORT_HAND, NGS, KIT_NUMBER]
    combined_original_df = get_df_without_nonutils_and_extrastr_columns(combined_original_df, str_columns_list,
                                                                        utils_columns_list)
    extra_columns_list = ['DYS385', 'DYS459', 'DYS464', 'YCAII', 'CDY', 'DYF395S1', 'DYS413']
    combined_original_df = get_df_without_palindrome_columns(combined_original_df, extra_columns_list)
    combined_original_df = get_df_without_shortstr_rows(combined_original_df, utils_columns_list)
    combined_original_df = get_df_without_palindrome_rows(combined_original_df, utils_columns_list)
    combined_original_df = get_df_with_int_datatype_of_nonutils_columns(combined_original_df, utils_columns_list)
    combined_original_df = get_df_with_str_type_of_utils_columns(combined_original_df, utils_columns_list)

    print('Создаем копию исходного набора данных, чтобы впоследствии удалить из нее строки, '
          'использовавшиеся в ходе обучения, а затем предсказать SNP для оставшихся строк.')
    unused_for_train_df = combined_original_df.copy()
    del unused_for_train_df[NGS]
    del unused_for_train_df[SHORT_HAND]

    print('Удаляем строки, для которых FTDNA, в силу каких-то причин, не указало SNP.')
    combined_original_df = combined_original_df[combined_original_df[SHORT_HAND].notna()]
    print(ROWS_IN_DF_COUNT_TEXT.format('combined_df', len(combined_original_df.index)))
    print(NUMBER_OF_REPRESENTATIVES_OF_EACH_SNP_TEXT.format(combined_original_df[SHORT_HAND].value_counts()))

    combined_df_positive_snps = get_df_positive_snps(child_snps, combined_original_df, json_tree_rows)
    print(ROWS_IN_DF_COUNT_TEXT.format('combined_df_positive_snps', len(combined_df_positive_snps.index)))
    print(NUMBER_OF_REPRESENTATIVES_OF_EACH_SNP_TEXT.format(combined_df_positive_snps[SHORT_HAND].value_counts()))

    print('Условным признаком сделанного BigY500/700 является количество положительных SNP, превышающее 200. '
          'Удаляем те строки, для которых не сделан BigY, '
          'а также те, для которых не является положительным ни один из дочерних SNP целевого SNP.')
    combined_df_positive_snps = combined_df_positive_snps.drop(
        combined_df_positive_snps[(combined_df_positive_snps[NGS] == False) &
                                  (~combined_df_positive_snps[SHORT_HAND].isin(child_snps))].index)
    del combined_df_positive_snps[NGS]
    print(ROWS_IN_DF_COUNT_TEXT.format('combined_df_positive_snps', len(combined_df_positive_snps.index)))
    print(NUMBER_OF_REPRESENTATIVES_OF_EACH_SNP_TEXT.format(combined_df_positive_snps[SHORT_HAND].value_counts()))

    print('Делим данные на 2 части: то, что предсказываем (SNP) и то, по чему предсказываем (STR).')
    y = combined_df_positive_snps[SHORT_HAND]
    del combined_df_positive_snps[SHORT_HAND]
    x = combined_df_positive_snps

    print('Расчленяем набор данных на обучающую и испытательную выборки.')
    x_train, x_test, y_train, y_test = train_test_split(x.drop(columns=[KIT_NUMBER]), y, random_state=123,
                                                        test_size=0.2)

    print('Если какого-то SNP нет в обучающей выборке, но есть в испытательной (и наоборот), '
          'то удаляем строки с ним из обеих выборок.')
    train_unique = y_train.unique()
    test_unique = y_test.unique()
    common_list = list(set(test_unique) & set(train_unique))
    train_absent_rows = y_train.index[~y_train.isin(common_list)].tolist()
    x_train = x_train.drop(train_absent_rows)
    y_train = y_train.drop(train_absent_rows)
    test_absent_rows = y_test.index[~y_test.isin(common_list)].tolist()
    x_test = x_test.drop(test_absent_rows)
    y_test = y_test.drop(test_absent_rows)

    if len(y_train.unique()) > 1 and len(y_test.unique()) > 1:
        print('Обучаем градиентный бустинг при разном количестве оценщиков, '
              'а затем выбираем и сохраняем то количество оценщиков, '
              'при котором достигается наивысшая точность предсказаний SNP.')
        n_estimators_list = [400, 500, 600]
        depth_list = [4, 5, 6, 7, 8]
        accuracy_best = 0
        n_estimators_best = 0
        depth_best = 0
        for n_estimators in n_estimators_list:
            for depth in depth_list:
                model = CatBoostClassifier(iterations=n_estimators, random_seed=123, thread_count=-1, depth=depth,
                                           nan_mode='Forbidden')
                model.fit(x_train, y_train, verbose=100, eval_set=Pool(x_test, y_test), early_stopping_rounds=10)
                predictions = model.predict(x_test)
                accuracy = f1_score(y_test, predictions, average='macro')
                if accuracy > accuracy_best:
                    accuracy_best = accuracy
                    n_estimators_best = n_estimators
                    depth_best = depth
                print('При {} оценщиков и глубине {} достигается точность {}.'.format(n_estimators, depth, accuracy))

        print('Наивысшая точность, равная {}, достигается при {} оценщиков и глубине {}.'.format(accuracy_best,
                                                                                                 n_estimators_best,
                                                                                                 depth_best))
        if accuracy_best < 0.75:
            print('Наивысшая точность предсказания ниже допустимых 0.75: пропускаем текущий SNP')
            return None
        else:
            print('Обучаем градиентный бустинг для предсказания SNP.')
            model = CatBoostClassifier(iterations=n_estimators_best, random_seed=123, thread_count=-1, verbose=100,
                                       depth=depth_best, nan_mode='Forbidden')
            model.fit(x.drop(columns=[KIT_NUMBER]), y, verbose=100)

            print('Оставляем в копии исходного набора данных только те строки, '
                  'которые не были задействованы при обучении.')
            unused_for_train_df = unused_for_train_df.loc[~unused_for_train_df[KIT_NUMBER].isin(x[KIT_NUMBER])]
            print(ROWS_IN_DF_COUNT_TEXT.format('unused_for_train_df', len(unused_for_train_df.index)))

            print('Предсказываем SNP.')
            predictions = model.predict(unused_for_train_df.drop(columns=[KIT_NUMBER]))

            print('Собираем данные воедино.')
            unused_for_train_df[SHORT_HAND] = predictions
            print(ROWS_IN_DF_COUNT_TEXT.format('unused_for_train_df', len(unused_for_train_df.index)))
            print(NUMBER_OF_REPRESENTATIVES_OF_EACH_SNP_TEXT.format(unused_for_train_df[SHORT_HAND].value_counts()))

            used_for_train_df = x
            used_for_train_df[SHORT_HAND] = y
            print(ROWS_IN_DF_COUNT_TEXT.format('used_for_train_df', len(used_for_train_df.index)))
            print(NUMBER_OF_REPRESENTATIVES_OF_EACH_SNP_TEXT.format(used_for_train_df[SHORT_HAND].value_counts()))

            combined_extended_df = pd.concat([unused_for_train_df, used_for_train_df])
            print(ROWS_IN_DF_COUNT_TEXT.format('combined_extended_df', len(combined_extended_df.index)))
            print(NUMBER_OF_REPRESENTATIVES_OF_EACH_SNP_TEXT.format(combined_extended_df[SHORT_HAND].value_counts()))

            print('Склеиваем информацию о SNP с информацией о местоположении.')
            combined_extended_map_df = pd.merge(combined_extended_df, map_df, on=KIT_NUMBER)
            print(ROWS_IN_DF_COUNT_TEXT.format('combined_extended_map_df', len(combined_extended_map_df.index)))
            print(NUMBER_OF_REPRESENTATIVES_OF_EACH_SNP_TEXT.format(
                combined_extended_map_df[SHORT_HAND].value_counts()))

            combined_extended_map_df_without_other = get_df_without_other(combined_extended_map_df)
            print(datetime.datetime.now())
            return combined_extended_map_df_without_other
    else:
        print('В обучающей/испытательной выборке нет SNP кроме Other: пропускаем текущий SNP')
        return None


def get_df_with_str_type_of_utils_columns(combined_original_df, utils_columns_list):
    print('Меняем тип данных на str для всех инструментальных столбцов.')
    for column in combined_original_df:
        if column in utils_columns_list:
            if column == NGS:
                combined_original_df[column] = combined_original_df[column].astype(bool)
            else:
                combined_original_df[column] = combined_original_df[column].astype(str)
    return combined_original_df


def get_df_with_int_datatype_of_nonutils_columns(combined_original_df, utils_columns_list):
    print('Меняем тип данных на int для всех столбцов, кроме инструментальных.')
    for column in combined_original_df:
        if column not in utils_columns_list:
            combined_original_df[column] = combined_original_df[column].astype(float)
            combined_original_df[column] = combined_original_df[column].astype(int)
    return combined_original_df


def get_df_without_palindrome_rows(combined_original_df, utils_columns_list):
    print('Удаляем строки, содержащие палиндромы в тех STR, которым не свойственна палиндромность.')
    for column in combined_original_df:
        if column not in utils_columns_list:
            try:
                combined_original_df = combined_original_df.drop(
                    combined_original_df[combined_original_df[column].astype(str).str.contains('-', na=False)].index)
            except KeyError as KE:
                print(KE)
    print(ROWS_IN_DF_COUNT_TEXT.format('combined_df', len(combined_original_df.index)))
    print(NUMBER_OF_REPRESENTATIVES_OF_EACH_SNP_TEXT.format(combined_original_df[SHORT_HAND].value_counts()))
    return combined_original_df


def get_df_without_shortstr_rows(combined_original_df, utils_columns_list):
    print('Удаляем все строки, в которых количество STR ниже порога, заданного в начале блокнота.')
    for column in combined_original_df:
        if column not in utils_columns_list:
            try:
                combined_original_df = combined_original_df[combined_original_df[column].notna()]
            except KeyError as KE:
                print(KE)
    print(ROWS_IN_DF_COUNT_TEXT.format('combined_df', len(combined_original_df.index)))
    print(NUMBER_OF_REPRESENTATIVES_OF_EACH_SNP_TEXT.format(combined_original_df[SHORT_HAND].value_counts()))
    return combined_original_df


def get_df_without_palindrome_columns(combined_original_df, extra_columns_list):
    print('Удаляем столбцы, всегда содержащие палиндромы.')
    for extra_column in extra_columns_list:
        try:
            del combined_original_df[extra_column]
        except KeyError as KE:
            print(KE)
    return combined_original_df


def get_df_without_nonutils_and_extrastr_columns(combined_original_df, str_columns_list, utils_columns_list):
    print('Удаляем столбцы, не являющиеся инструментальными и выходящие за границы выбранного числа STR.')
    for column in combined_original_df:
        if column not in utils_columns_list and column not in str_columns_list:
            try:
                del combined_original_df[column]
            except KeyError as KE:
                print(KE)
    return combined_original_df


def get_str_columns_list(str_number):
    y12_list = ['DYS393', 'DYS390', 'DYS19', 'DYS391', 'DYS385', 'DYS426', 'DYS388', 'DYS439', 'DYS389I', 'DYS392',
                'DYS389II']
    y37_list = y12_list + ['DYS458', 'DYS459', 'DYS455', 'DYS454', 'DYS447', 'DYS437', 'DYS448', 'DYS449', 'DYS464',
                           'DYS460', 'Y-GATA-H4', 'YCAII', 'DYS456', 'DYS607', 'DYS576', 'DYS570', 'CDY', 'DYS442',
                           'DYS438']
    y67_list = y37_list + ['DYS531', 'DYS578', 'DYF395S1', 'DYS590', 'DYS537', 'DYS641', 'DYS472', 'DYF406S1', 'DYS511',
                           'DYS425', 'DYS413', 'DYS557', 'DYS594', 'DYS436', 'DYS490', 'DYS534', 'DYS450', 'DYS444',
                           'DYS481', 'DYS520', 'DYS446', 'DYS617', 'DYS568', 'DYS487', 'DYS572', 'DYS640', 'DYS492',
                           'DYS565']
    y111_list = y67_list + ['DYS710', 'DYS485', 'DYS632', 'DYS495', 'DYS540', 'DYS714', 'DYS716', 'DYS717', 'DYS505',
                            'DYS556', 'DYS549', 'DYS589', 'DYS522', 'DYS494', 'DYS533', 'DYS636', 'DYS575', 'DYS638',
                            'DYS462', 'DYS452', 'DYS445', 'Y-GATA-A10', 'DYS463', 'DYS441', 'Y-GGAAT-1B07', 'DYS525',
                            'DYS712', 'DYS593', 'DYS650', 'DYS532', 'DYS715', 'DYS504', 'DYS513', 'DYS561', 'DYS552',
                            'DYS726', 'DYS635', 'DYS587', 'DYS643', 'DYS497', 'DYS510', 'DYS434', 'DYS461', 'DYS435']

    if str_number == 12:
        return y12_list
    elif str_number == 37:
        return y37_list
    elif str_number == 67:
        return y67_list
    elif str_number == 111:
        return y111_list


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
