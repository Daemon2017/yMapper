import pandas as pd
import numpy as np
import math
import random
import ftdna_tree_collector_rest
import datetime

from utils import Utils
from itertools import product
from shapely.geometry import Polygon
from multiprocessing import freeze_support

# Выбираем стратегию работы с данными:
# * False - если хотим работать только с теми данными, что 100% подтверждены BigY500/BigY700/SNP;
# * True - если хотим работать с наибольшим возможным количеством данных, полученным в результате предсказания SNP по
#  STR с некоторой точностью.
is_extended = True
# Задаем целевой SNP, чьи дочерние SNP будут наноситься на карту.
target_snp = 'R-CTS1211'
# Задаем количество STR (12/37/67/111), которое будет использоваться на шаге предсказания SNP.
str_number = 111
# Задаем координаты левого нижнего угла сетки из шестиугольников.
x_0 = 0
y_0 = 37
# Задаем ширину/длину сетки из шестиугольников. Координаты правого верхнего угла сетки из прямоугольников это
# x_0+x_1:y_0+y_1.
x_1 = 42
y_1 = 27
# Задаем координаты центра карты и степень приближения.
x_center = 23.169720
y_center = 48.814170
zoom = 5
# Задаем размеры шестиугольников для каждого из слоев. По умолчанию будет отображаться только первый. 
h_list = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]

if __name__ == '__main__':
    freeze_support()
    print(datetime.datetime.now())
    combined_df = pd.read_csv('combined_snp_str_map.csv', engine='python')
    print("Количество строк в файле: {}".format(len(combined_df.index)))

    print("Открываем древо Y-SNP от FTDNA.")
    json_tree_rows = ftdna_tree_collector_rest.get_json_tree_rows()

    print("Получаем список дочерних SNP целевого SNP.")
    child_snps = ftdna_tree_collector_rest.get_children_list(json_tree_rows, target_snp)
    print(child_snps)

    print("Создаем словарь 'Набор SNP: Цвет'.")
    combination_to_color_dict = {}
    for snp in [tuple(i) for i in product([True, False], repeat=len(child_snps))]:
        combination_to_color_dict[snp] = "#%06x" % random.randint(0, 0xFFFFFF)

    utils = Utils()

    print("Среди всех строк ищем те, что имеют положительный SNP, восходящий к одному из дочерних SNP целевого SNP.")
    combined_df = utils.get_positive_snps(child_snps, combined_df, json_tree_rows)
    print("Отбрасываем строки, содержащие 'Other' в столбце 'Short Hand'.")
    combined_df = combined_df.drop(combined_df[combined_df['Short Hand'] == 'Other'].index)
    print("Количество представителей выбранной ветви: {}".format(len(combined_df.index)))
    print("Количество представителей каждой подветви: \n{}".format(combined_df['Short Hand'].value_counts()))

    print("Создаем столько сеток из шестиугольников, сколько размеров было задано на 1-м шаге.")
    polygon_list_list = []
    for h in h_list:
        polygon_list = []
        is_even = False
        for lat in np.arange(y_0, y_0 + y_1, (math.sin(math.radians(30)) * h - math.sin(math.radians(270)) * h)):
            if is_even:
                is_even = False
                x_0 = x_0 + (math.cos(math.radians(30)) * h -
                             math.cos(math.radians(150)) * h) / 2
            else:
                is_even = True
                x_0 = x_0 - (math.cos(math.radians(30)) * h -
                             math.cos(math.radians(150)) * h) / 2
            for lon in np.arange(x_0, x_0 + x_1, (math.cos(math.radians(30)) * h - math.cos(math.radians(150)) * h)):
                polygon_list.append(Polygon([[lon + math.cos(math.radians(angle)) * h,
                                              lat + math.sin(math.radians(angle)) * h]
                                             for angle in range(30, 360, 60)]))

        polygon_list_list.append(polygon_list)

    utils.get_map(combined_df, False, polygon_list_list, child_snps, y_center, x_center, zoom,
                  combination_to_color_dict, target_snp, h_list)
    if is_extended:
        combined_df = utils.get_extended_data(combined_df, str_number, json_tree_rows, child_snps)
        utils.get_map(combined_df, True, polygon_list_list, child_snps, y_center, x_center, zoom,
                      combination_to_color_dict, target_snp, h_list)
    print(datetime.datetime.now())
