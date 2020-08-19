import pandas as pd
import numpy as np
import multiprocessing
import ftdna_tree_collector_rest
import datetime
import sys

from xgboost import XGBClassifier
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from itertools import compress, repeat
from folium import FeatureGroup, LayerControl, Map, GeoJson
from shapely.geometry import Point


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


def get_positive_polygons(polygon, child_snps, combined_df):
    snps_list = [False] * len(child_snps)
    for i, row in combined_df.iterrows():
        if polygon.contains(Point(combined_df.at[i, 'lng'], combined_df.at[i, 'lat'])):
            n = 0
            for snp in child_snps:
                if combined_df.at[i, 'Short Hand'] == snp:
                    snps_list[n] = True
                    break
                n = n + 1
    return snps_list


class Utils(object):
    def get_positive_snps(self, child_snps, combined_df, json_tree_rows):
        print(datetime.datetime.now())
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

    def get_extended_data(self, combined_df, str_number, json_tree_rows, child_snps):
        print(datetime.datetime.now())
        combined_df['Kit Number'] = combined_df['Kit Number'].astype(str)
        new_combined_df = self.get_extended_combined_map_file(str_number, json_tree_rows, child_snps)
        new_combined_df['Kit Number'] = new_combined_df['Kit Number'].astype(str)
        print('В наборе new_combined_df оставляем только те строки, которых нет в наборе combined_df.')
        new_combined_df = new_combined_df.loc[~new_combined_df['Kit Number'].isin(combined_df['Kit Number'])]
        print('Присоединяем к набору new_combined_df содержимое набора combined_df.')
        new_combined_df = pd.concat([combined_df, new_combined_df], sort=True)
        print('В наборе данных new_combined_df {} строк'.format(len(new_combined_df.index)))
        print("Количество представителей каждой подветви: \n{}".format(new_combined_df['Short Hand'].value_counts()))
        print(datetime.datetime.now())
        return new_combined_df

    def get_map(self, combined_df, is_extended, polygon_list_list, child_snps, y_center, x_center, zoom,
                combination_to_color_dict, target_snp, h_list):
        print(datetime.datetime.now())
        print('Очищаем набор данных от строк с пустыми координатами...')
        combined_df['lng'] = combined_df['lng'].astype(float)
        combined_df = combined_df[combined_df['lng'].notna()].copy()
        combined_df['lat'] = combined_df['lat'].astype(float)
        combined_df = combined_df[combined_df['lat'].notna()]
        print('В наборе данных combined_df {} строк'.format(len(combined_df.index)))
        print('Количество представителей каждого SNP:\n{}'.format(combined_df['Short Hand'].value_counts()))

        print("Проверяем наличие каждого целевого SNP в каждом шестиугольнике.")
        max_snps_sum_list = []
        current_snps_list_list = []
        for polygon_list in polygon_list_list:
            max_snps_sum = 0
            current_snps_list = []

            pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
            result = pool.starmap(get_positive_polygons,
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

                gj = GeoJson(polygon, style_function=style_function, tooltip=list(compress(child_snps, current_snp)))
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
        print("HTML-файл с картой сохранен!\n")
        print(datetime.datetime.now())

    def get_extended_combined_map_file(self, str_number, json_tree_rows, child_snps):
        print(datetime.datetime.now())
        print('Загружаем набор данных SNP+STR+Map.')
        combined_df = pd.read_csv('combined_snp_str_map.csv', engine='python')
        print('В загруженном наборе данных {} строк'.format(len(combined_df.index)))
        print('Количество представителей каждого SNP:\n{}'.format(combined_df['Short Hand'].value_counts()))

        print('Выделяем данные о местоположении в отдельный набор.')
        combined_map_df = combined_df.filter(['Kit Number', 'lat', 'lng'], axis=1)
        print('В наборе данных combined_map_df {} строк'.format(len(combined_map_df.index)))

        y12_list = ['DYS393', 'DYS390', 'DYS19', 'DYS391', 'DYS385',
                    'DYS426', 'DYS388', 'DYS439', 'DYS389I', 'DYS392', 'DYS389II']
        y37_list = y12_list + ['DYS458', 'DYS459', 'DYS455', 'DYS454', 'DYS447', 'DYS437', 'DYS448', 'DYS449',
                               'DYS464', 'DYS460', 'Y-GATA-H4', 'YCAII', 'DYS456', 'DYS607', 'DYS576', 'DYS570', 'CDY',
                               'DYS442', 'DYS438']
        y67_list = y37_list + ['DYS531', 'DYS578', 'DYF395S1', 'DYS590', 'DYS537', 'DYS641', 'DYS472', 'DYF406S1',
                               'DYS511',
                               'DYS425', 'DYS413', 'DYS557', 'DYS594',
                               'DYS436', 'DYS490', 'DYS534', 'DYS450', 'DYS444', 'DYS481', 'DYS520', 'DYS446', 'DYS617',
                               'DYS568', 'DYS487', 'DYS572', 'DYS640', 'DYS492', 'DYS565']
        y111_list = y67_list + ['DYS710', 'DYS485', 'DYS632', 'DYS495', 'DYS540', 'DYS714', 'DYS716', 'DYS717',
                                'DYS505',
                                'DYS556', 'DYS549', 'DYS589', 'DYS522', 'DYS494', 'DYS533', 'DYS636', 'DYS575',
                                'DYS638',
                                'DYS462', 'DYS452', 'DYS445',
                                'Y-GATA-A10', 'DYS463', 'DYS441', 'Y-GGAAT-1B07', 'DYS525', 'DYS712', 'DYS593',
                                'DYS650',
                                'DYS532', 'DYS715', 'DYS504', 'DYS513', 'DYS561', 'DYS552', 'DYS726', 'DYS635',
                                'DYS587',
                                'DYS643', 'DYS497', 'DYS510', 'DYS434', 'DYS461', 'DYS435']

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
        for column in combined_df:
            if column not in utils_columns_list:
                if column not in str_columns_list:
                    try:
                        del combined_df[column]
                    except KeyError as KE:
                        print(KE)

        print('Удаляем столбцы, всегда содержащие палиндромы.')
        extra_columns_list = ['DYS385', 'DYS459', 'DYS464', 'YCAII', 'CDY', 'DYF395S1', 'DYS413']

        for extra_column in extra_columns_list:
            try:
                del combined_df[extra_column]
            except KeyError as KE:
                print(KE)

        print('Удаляем все строки, в которых количество STR ниже порога, заданного в начале блокнота.')
        for column in combined_df:
            if column not in utils_columns_list:
                try:
                    combined_df = combined_df[combined_df[column].notna()]
                except KeyError as KE:
                    print(KE)
        print('В наборе данных combined_df {} строк'.format(len(combined_df.index)))
        print('Количество представителей каждого SNP:\n{}'.format(combined_df['Short Hand'].value_counts()))

        print('Удаляем строки, содержащие палиндромы в тех STR, которым не свойственна палиндромность.')
        for column in combined_df:
            if column not in utils_columns_list:
                try:
                    combined_df = combined_df.drop(
                        combined_df[combined_df[column].astype(str).str.contains('-', na=False)].index)
                except KeyError as KE:
                    print(KE)
        print('В наборе данных combined_df {} строк'.format(len(combined_df.index)))
        print('Количество представителей каждого SNP:\n{}'.format(combined_df['Short Hand'].value_counts()))

        print('Меняем тип данных на int для всех столбцов, кроме инструментальных.')
        for column in combined_df:
            if column not in utils_columns_list:
                combined_df[column] = combined_df[column].astype(float)
                combined_df[column] = combined_df[column].astype(int)

        print('Меняем тип данных на str для всех инструментальных столбцов.')
        for column in combined_df:
            if column in utils_columns_list:
                if column == 'NGS':
                    combined_df[column] = combined_df[column].astype(bool)
                else:
                    combined_df[column] = combined_df[column].astype(str)

        print('Создаем копию исходного набора данных, чтобы впоследствии удалить из нее строки, '
              'использовавшиеся в ходе обучения, а затем предсказать SNP для оставшихся строк.')
        unused_for_train_df = combined_df.copy()
        del unused_for_train_df['NGS']
        del unused_for_train_df['Short Hand']

        print('Удаляем строки, для которых FTDNA, в силу каких-то причин, не указало SNP.')
        combined_df = combined_df[combined_df['Short Hand'].notna()]
        print('В наборе данных combined_df {} строк'.format(len(combined_df.index)))
        print('Количество представителей каждого SNP:\n{}'.format(combined_df['Short Hand'].value_counts()))

        print(
            'Среди всех строк ищем те, что имеют положительный SNP, восходящий к одному из дочерних SNP целевого SNP.')
        combined_df = self.get_positive_snps(child_snps, combined_df, json_tree_rows)
        print('В наборе данных combined_df {} строк'.format(len(combined_df.index)))
        print('Количество представителей каждого SNP:\n{}'.format(combined_df['Short Hand'].value_counts()))

        print('Условным признаком сделанного BigY500/700 является количество положительных SNP, превышающее 200. '
              'Удаляем те строки, для которых не сделан BigY, '
              'а также те, для которых не является положительным ни один из дочерних SNP целевого SNP.')
        combined_df = combined_df.drop(combined_df[(combined_df['NGS'] == False) &
                                                   (~combined_df['Short Hand'].isin(child_snps))].index)
        del combined_df['NGS']
        print('В наборе данных combined_df {} строк'.format(len(combined_df.index)))
        print('Количество представителей каждого SNP:\n{}'.format(combined_df['Short Hand'].value_counts()))

        print('Делим данные на 2 части: то, что предсказываем (SNP) и то, по чему предсказываем (STR).')
        Y = combined_df['Short Hand']
        del combined_df['Short Hand']

        X = combined_df.copy()

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

        used_for_train_df = X.copy()
        used_for_train_df['Short Hand'] = Y
        print('В наборе данных used_for_train_df {} строк'.format(len(used_for_train_df.index)))
        print('Количество представителей каждого SNP:\n{}'.format(used_for_train_df['Short Hand'].value_counts()))

        new_combined_df = pd.concat([unused_for_train_df, used_for_train_df])

        print('В наборе данных new_combined_df {} строк'.format(len(new_combined_df.index)))
        print('Количество представителей каждого SNP:\n{}'.format(new_combined_df['Short Hand'].value_counts()))

        print('Оставляем только полезные столбцы.')
        important_columns_list = ['Kit Number', 'Short Hand']

        for column in new_combined_df:
            if column not in important_columns_list:
                try:
                    del new_combined_df[column]
                except KeyError as KE:
                    print(KE)

        print('Склеиваем информацию о SNP с информацией о местоположении.')
        new_combined_df = pd.merge(new_combined_df, combined_map_df, on='Kit Number')
        print('В наборе данных new_combined_df {} строк'.format(len(new_combined_df.index)))
        print('Количество представителей каждого SNP:\n{}'.format(new_combined_df['Short Hand'].value_counts()))

        print('Отбрасываем строки, содержащие "Other" в столбце "Short Hand".')
        new_combined_df = new_combined_df.drop(new_combined_df[new_combined_df['Short Hand'] == 'Other'].index)
        print('В наборе данных new_combined_df {} строк'.format(len(new_combined_df.index)))
        print('Количество представителей каждого SNP:\n{}'.format(new_combined_df['Short Hand'].value_counts()))
        print(datetime.datetime.now())

        return new_combined_df
