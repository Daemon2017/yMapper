import datetime
import math
import multiprocessing
import sys
import numpy as np
import pandas as pd
import ftdna_tree_collector_rest
import random

from itertools import compress, repeat, product
from folium import FeatureGroup, LayerControl, Map, GeoJson
from shapely.geometry import Point
from shapely.geometry import Polygon
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier


def get_dict(snps, json_tree_rows, child_snps):
    old_to_new_dict = {}
    for snp in snps:
        parent_list = ftdna_tree_collector_rest.get_parent_list(json_tree_rows, snp)
        intersection_list = list(set(parent_list) & set(child_snps))
        if len(intersection_list) == 1:
            old_to_new_dict[snp] = intersection_list[0]
        else:
            old_to_new_dict[snp] = 'Other'
    return old_to_new_dict


def get_positive_snps(polygon, child_snps, combined_df):
    snps_list = [False] * len(child_snps)
    bounds = polygon.bounds
    combined_df = combined_df.loc[(combined_df['lng'] >= bounds[0]) & (combined_df['lng'] <= bounds[2]) &
                                  (combined_df['lat'] >= bounds[1]) & (combined_df['lat'] <= bounds[3])]
    for i, row in combined_df.iterrows():
        if polygon.contains(Point(combined_df.at[i, 'lng'], combined_df.at[i, 'lat'])):
            n = 0
            for snp in child_snps:
                if combined_df.at[i, 'Short Hand'] == snp:
                    snps_list[n] = True
                    break
                n = n + 1
    return snps_list


def get_combined_df():
    print('Загружаем набор данных SNP+STR+Map.')
    combined_df = pd.read_csv('combined_snp_str_map.csv', engine='python')
    print('В загруженном наборе данных {} строк'.format(len(combined_df.index)))
    print('Количество представителей каждого SNP:\n{}'.format(combined_df['Short Hand'].value_counts()))
    return combined_df


def get_json_tree_rows():
    print("Открываем древо Y-SNP от FTDNA.")
    json_tree_rows = ftdna_tree_collector_rest.get_json_tree_rows()
    return json_tree_rows


def get_child_snps(json_tree_rows, target_snp):
    print("Получаем список дочерних SNP целевого SNP.")
    child_snps = ftdna_tree_collector_rest.get_children_list(json_tree_rows, target_snp)
    print('Дочерние SNP: {}'.format(child_snps))
    return child_snps


def get_combination_to_color_dict(child_snps):
    print("Создаем словарь 'Набор SNP: Цвет'.")
    combination_to_color_dict = {}
    for snp in [tuple(i) for i in product([True, False], repeat=len(child_snps))]:
        combination_to_color_dict[snp] = "#%06x" % random.randint(0, 0xFFFFFF)
    return combination_to_color_dict


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
    unique_values = combined_df['Short Hand'].unique()
    chunks = np.array_split(unique_values, num_processes)
    pool = multiprocessing.Pool(processes=num_processes)
    result = pool.starmap(get_dict,
                          zip(chunks, repeat(json_tree_rows), repeat(child_snps)))
    old_to_new_dict = {}
    for i in range(len(result)):
        old_to_new_dict.update(result[i])
    combined_df['Short Hand'] = combined_df['Short Hand'].map(old_to_new_dict)
    print(datetime.datetime.now())
    return combined_df


def get_df_extended(combined_normal_df_without_other, str_number, json_tree_rows, child_snps, combined_original_df):
    print(datetime.datetime.now())
    combined_normal_df_without_other['Kit Number'] = combined_normal_df_without_other['Kit Number'].astype(str)
    combined_extended_map_df = get_df_extended_map(str_number, combined_original_df, json_tree_rows, child_snps)
    combined_extended_map_df['Kit Number'] = combined_extended_map_df['Kit Number'].astype(str)
    print('В наборе combined_extended_map_df оставляем только те строки, которых нет в наборе combined_df.')
    combined_extended_map_df = \
        combined_extended_map_df.loc[
            ~combined_extended_map_df['Kit Number'].isin(combined_normal_df_without_other['Kit Number'])]
    print('Присоединяем к набору combined_extended_map_df содержимое набора combined_df.')
    combined_extended_map_df = pd.concat([combined_normal_df_without_other, combined_extended_map_df], sort=True)
    print('В наборе данных combined_extended_map_df {} строк'.format(len(combined_extended_map_df.index)))
    print("Количество представителей каждой подветви: \n{}"
          .format(combined_extended_map_df['Short Hand'].value_counts()))
    print(datetime.datetime.now())
    return combined_extended_map_df


def get_map(combined_df, is_extended, polygon_list_list, child_snps, y_center, x_center, zoom,
            combination_to_color_dict, target_snp, h_list):
    print(datetime.datetime.now())
    print('Очищаем набор данных от строк с пустыми координатами...')
    combined_df['lng'] = combined_df['lng'].astype(float)
    combined_df = combined_df[combined_df['lng'].notna()].copy()
    combined_df['lat'] = combined_df['lat'].astype(float)
    combined_df = combined_df[combined_df['lat'].notna()]
    print('В наборе данных combined_df {} строк'.format(len(combined_df.index)))
    print('Количество представителей каждого SNP:\n{}'.format(combined_df['Short Hand'].value_counts()))

    print("Проверяем наличие каждого целевого SNP в каждом шестиугольнике каждой сетки.")
    max_snps_sum_list = []
    current_snps_list_list = []
    for polygon_list, h in zip(polygon_list_list, h_list):
        print('Проверяем сетку размером {}'.format(h))
        max_snps_sum = 0
        current_snps_list = []

        pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
        result = pool.starmap(get_positive_snps,
                              zip(polygon_list, repeat(child_snps), repeat(combined_df)))

        for r in result:
            current_snps_sum = sum(r)
            if current_snps_sum > max_snps_sum:
                max_snps_sum = current_snps_sum
            current_snps_list.append(r)

        max_snps_sum_list.append(max_snps_sum)
        current_snps_list_list.append(current_snps_list)

    print("Создаем карту и центрируем ее на Русских воротах.")
    m = Map([y_center, x_center], zoom_start=zoom, tiles='Stamen Terrain', crs='EPSG3857')

    print("Раскрашиваем шестиугольники, присоединяем их к слоям, а слои прикрепляем к карте.")
    is_display_enabled = True
    for polygon_list, current_snps_list, h, max_snps_sum in \
            zip(polygon_list_list, current_snps_list_list, h_list, max_snps_sum_list):
        fg = FeatureGroup(name='{} Сетка'.format(str(h)), show=is_display_enabled)
        for polygon, current_snp in \
                zip(polygon_list, current_snps_list):
            fillColor = combination_to_color_dict[tuple(current_snp)]
            fillOpacity = sum(current_snp) / max_snps_sum

            def style_function(feature, fillColor=fillColor, fillOpacity=fillOpacity):
                return {
                    'fillOpacity': fillOpacity,
                    'weight': 0.1,
                    'fillColor': fillColor,
                    'color': '#000000'
                }

            gj = GeoJson(polygon, style_function=style_function,
                         tooltip=list(compress(child_snps, current_snp)))
            gj.add_to(fg)
        fg.add_to(m)
        if is_display_enabled:
            is_display_enabled = False
    LayerControl().add_to(m)

    print("Сохраняем карту.")
    if is_extended:
        m.save('map_{}_extended.html'.format(target_snp))
    else:
        m.save('map_{}.html'.format(target_snp))
    print("HTML-файл с картой сохранен!")
    print(datetime.datetime.now())


def get_df_extended_map(str_number, combined_original_df, json_tree_rows, child_snps):
    print('Выделяем данные о местоположении в отдельный набор.')
    map_df = combined_original_df.filter(['Kit Number', 'lat', 'lng'], axis=1)
    print('В наборе данных map_df {} строк'.format(len(map_df.index)))

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

    str_columns_list = []
    if str_number == 12:
        str_columns_list = y12_list
    elif str_number == 37:
        str_columns_list = y37_list
    elif str_number == 67:
        str_columns_list = y67_list
    elif str_number == 111:
        str_columns_list = y111_list

    print('Удаляем столбцы, не являющиеся инструментальными и выходящие за границы выбранного числа STR.')
    utils_columns_list = ['Short Hand', 'NGS', 'Kit Number']
    for column in combined_original_df:
        if column not in utils_columns_list:
            if column not in str_columns_list:
                try:
                    del combined_original_df[column]
                except KeyError as KE:
                    print(KE)

    print('Удаляем столбцы, всегда содержащие палиндромы.')
    extra_columns_list = ['DYS385', 'DYS459', 'DYS464', 'YCAII', 'CDY', 'DYF395S1', 'DYS413']

    for extra_column in extra_columns_list:
        try:
            del combined_original_df[extra_column]
        except KeyError as KE:
            print(KE)

    print('Удаляем все строки, в которых количество STR ниже порога, заданного в начале блокнота.')
    for column in combined_original_df:
        if column not in utils_columns_list:
            try:
                combined_original_df = combined_original_df[combined_original_df[column].notna()]
            except KeyError as KE:
                print(KE)
    print('В наборе данных combined_df {} строк'.format(len(combined_original_df.index)))
    print('Количество представителей каждого SNP:\n{}'.format(combined_original_df['Short Hand'].value_counts()))

    print('Удаляем строки, содержащие палиндромы в тех STR, которым не свойственна палиндромность.')
    for column in combined_original_df:
        if column not in utils_columns_list:
            try:
                combined_original_df = combined_original_df.drop(
                    combined_original_df[combined_original_df[column].astype(str).str.contains('-', na=False)].index)
            except KeyError as KE:
                print(KE)
    print('В наборе данных combined_df {} строк'.format(len(combined_original_df.index)))
    print('Количество представителей каждого SNP:\n{}'.format(combined_original_df['Short Hand'].value_counts()))

    print('Меняем тип данных на int для всех столбцов, кроме инструментальных.')
    for column in combined_original_df:
        if column not in utils_columns_list:
            combined_original_df[column] = combined_original_df[column].astype(float)
            combined_original_df[column] = combined_original_df[column].astype(int)

    print('Меняем тип данных на str для всех инструментальных столбцов.')
    for column in combined_original_df:
        if column in utils_columns_list:
            if column == 'NGS':
                combined_original_df[column] = combined_original_df[column].astype(bool)
            else:
                combined_original_df[column] = combined_original_df[column].astype(str)

    print('Создаем копию исходного набора данных, чтобы впоследствии удалить из нее строки, '
          'использовавшиеся в ходе обучения, а затем предсказать SNP для оставшихся строк.')
    unused_for_train_df = combined_original_df.copy()
    del unused_for_train_df['NGS']
    del unused_for_train_df['Short Hand']

    print('Удаляем строки, для которых FTDNA, в силу каких-то причин, не указало SNP.')
    combined_original_df = combined_original_df[combined_original_df['Short Hand'].notna()]
    print('В наборе данных combined_df {} строк'.format(len(combined_original_df.index)))
    print('Количество представителей каждого SNP:\n{}'.format(combined_original_df['Short Hand'].value_counts()))

    combined_df_positive_snps = get_df_positive_snps(child_snps, combined_original_df, json_tree_rows)
    print('В наборе данных combined_df_positive_snps {} строк'.format(len(combined_df_positive_snps.index)))
    print('Количество представителей каждого SNP:\n{}'.format(combined_df_positive_snps['Short Hand'].value_counts()))

    print('Условным признаком сделанного BigY500/700 является количество положительных SNP, превышающее 200. '
          'Удаляем те строки, для которых не сделан BigY, '
          'а также те, для которых не является положительным ни один из дочерних SNP целевого SNP.')
    combined_df_positive_snps = combined_df_positive_snps.drop(
        combined_df_positive_snps[(combined_df_positive_snps['NGS'] == False) &
                                  (~combined_df_positive_snps['Short Hand'].isin(child_snps))].index)
    del combined_df_positive_snps['NGS']
    print('В наборе данных combined_df_positive_snps {} строк'.format(len(combined_df_positive_snps.index)))
    print('Количество представителей каждого SNP:\n{}'.format(combined_df_positive_snps['Short Hand'].value_counts()))

    print('Делим данные на 2 части: то, что предсказываем (SNP) и то, по чему предсказываем (STR).')
    Y = combined_df_positive_snps['Short Hand']
    del combined_df_positive_snps['Short Hand']

    X = combined_df_positive_snps

    print('Расчленяем набор данных на обучающую и испытательную выборки.')
    X_train, X_test, Y_train, Y_test = train_test_split(X.drop(columns=['Kit Number']), Y, random_state=123,
                                                        test_size=0.2)

    print('Обучаем градиентный бустинг при разном количестве оценщиков, '
          'а затем выбираем и сохраняем то количество оценщиков, '
          'при котором достигается наивысшая точность предсказаний SNP.')
    n_estimators_list = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    accuracy_best = 0
    n_estimators_best = 0
    for n_estimators in n_estimators_list:
        model = XGBClassifier(n_estimators=n_estimators, random_state=123, n_jobs=-1)
        model.fit(X_train, Y_train, verbose=True)
        predictions = model.predict(X_test)
        accuracy = f1_score(Y_test, predictions, average='macro')
        if accuracy > accuracy_best:
            accuracy_best = accuracy
            n_estimators_best = n_estimators
        print('При {} оценщиков достигается точность {}.'.format(n_estimators, accuracy))

    print('Наивысшая точность, равная {}, достигается при {} оценщиков.'.format(accuracy_best, n_estimators_best))
    if accuracy_best < 0.75:
        print('Наивысшая точность предсказания ниже допустимых 0.75: завершаем работу программы.')
        sys.exit(0)

    print('Обучаем градиентный бустинг для предсказания SNP.')
    model = XGBClassifier(n_estimators=n_estimators_best, random_state=123, n_jobs=-1)
    model.fit(X.drop(columns=['Kit Number']), Y, verbose=True)

    print('Оставляем в копии исходного набора данных только те строки, которые не были задействованы при обучении.')
    unused_for_train_df = unused_for_train_df.loc[~unused_for_train_df['Kit Number'].isin(X['Kit Number'])]
    print('В наборе данных unused_for_train_df {} строк'.format(len(unused_for_train_df.index)))

    print('Предсказываем SNP.')
    predictions = model.predict(unused_for_train_df.drop(columns=['Kit Number']))

    print('Собираем данные воедино.')
    unused_for_train_df['Short Hand'] = predictions
    print('В наборе данных unused_for_train_df {} строк'.format(len(unused_for_train_df.index)))
    print('Количество представителей каждого SNP:\n{}'.format(unused_for_train_df['Short Hand'].value_counts()))

    used_for_train_df = X
    used_for_train_df['Short Hand'] = Y
    print('В наборе данных used_for_train_df {} строк'.format(len(used_for_train_df.index)))
    print('Количество представителей каждого SNP:\n{}'.format(used_for_train_df['Short Hand'].value_counts()))

    combined_extended_df = pd.concat([unused_for_train_df, used_for_train_df])
    print('В наборе данных combined_extended_df {} строк'.format(len(combined_extended_df.index)))
    print('Количество представителей каждого SNP:\n{}'.format(combined_extended_df['Short Hand'].value_counts()))

    print('Оставляем только полезные столбцы.')
    important_columns_list = ['Kit Number', 'Short Hand']

    for column in combined_extended_df:
        if column not in important_columns_list:
            try:
                del combined_extended_df[column]
            except KeyError as KE:
                print(KE)

    print('Склеиваем информацию о SNP с информацией о местоположении.')
    combined_extended_map_df = pd.merge(combined_extended_df, map_df, on='Kit Number')
    print('В наборе данных combined_extended_map_df {} строк'.format(len(combined_extended_map_df.index)))
    print('Количество представителей каждого SNP:\n{}'.format(combined_extended_map_df['Short Hand'].value_counts()))

    combined_extended_map_df_without_other = get_df_without_other(combined_extended_map_df)
    print(datetime.datetime.now())
    return combined_extended_map_df_without_other


def get_df_without_other(combined_df):
    print('Отбрасываем строки, содержащие "Other" в столбце "Short Hand".')
    combined_df = combined_df.drop(combined_df[combined_df['Short Hand'] == 'Other'].index)
    print('В наборе данных combined_df {} строк'.format(len(combined_df.index)))
    print('Количество представителей каждого SNP:\n{}'.format(combined_df['Short Hand'].value_counts()))
    return combined_df
