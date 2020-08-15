import pandas as pd
import numpy as np
import multiprocessing
import predictor
import ftdna_tree_collector_rest
import datetime

from itertools import compress, repeat
from folium import FeatureGroup, LayerControl, Map, GeoJson
from shapely.geometry import Point


def get_positive_snps(child_snps, combined_df, json_tree_rows):
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


def get_extended_data(combined_df, str_number, json_tree_rows, child_snps):
    combined_df['Kit Number'] = combined_df['Kit Number'].astype(str)
    new_combined_df = predictor.get_extended_combined_map_file(str_number, json_tree_rows, child_snps)
    new_combined_df['Kit Number'] = new_combined_df['Kit Number'].astype(str)
    print('В наборе new_combined_df оставляем только те строки, которых нет в наборе combined_df.')
    new_combined_df = new_combined_df.loc[~new_combined_df['Kit Number'].isin(combined_df['Kit Number'])]
    print('Присоединяем к набору new_combined_df содержимое набора combined_df.')
    new_combined_df = pd.concat([combined_df, new_combined_df], sort=True)
    print('В наборе данных new_combined_df {} строк'.format(len(new_combined_df.index)))
    print("Количество представителей каждой подветви: \n{}".format(new_combined_df['Short Hand'].value_counts()))
    return new_combined_df


def get_map(combined_df, is_extended, polygon_list_list, child_snps, y_center, x_center, zoom,
            combination_to_color_dict, target_snp, h_list):
    print(datetime.datetime.now())
    print('Очищаем набор данных от строк с пустыми координатами...')
    combined_df['lng'] = combined_df['lng'].astype(float)
    combined_df = combined_df[combined_df['lng'].notna()]
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
        result = pool.starmap(get_positive_polygons, zip(polygon_list, repeat(child_snps), repeat(combined_df)))

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
    for polygon_list, current_snps_list, h, max_snps_sum in zip(polygon_list_list, current_snps_list_list, h_list,
                                                                max_snps_sum_list):
        fg = FeatureGroup(name='{} Сетка'.format(str(h)), show=is_display_enabled)
        for polygon, current_snp in zip(polygon_list, current_snps_list):
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
