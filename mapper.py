import datetime
from multiprocessing import freeze_support

import utils

# Выбираем стратегию работы с данными:
# * False - если хотим работать только с теми данными, что 100% подтверждены BigY500/BigY700/SNP;
# * True - если хотим работать с наибольшим возможным количеством данных, полученным в результате предсказания SNP по
#  STR с некоторой точностью.
is_extended = False
# Задаем целевой SNP, чьи дочерние SNP будут наноситься на карту.
target_snps = ['R-CTS1211']
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
is_web = True

if __name__ == '__main__':
    freeze_support()

    for target_snp in target_snps:
        print("Обрабатывается SNP {}...".format(target_snp))
        print(datetime.datetime.now())
        combined_original_df = utils.get_combined_df()
        json_tree_rows = utils.get_json_tree_rows()
        child_snps = utils.get_child_snps(json_tree_rows, target_snp)
        if len(child_snps) > 0:
            combination_to_color_dict = utils.get_combination_to_color_dict(child_snps)

            if is_web:
                x_0 = -180
                y_0 = -90
                x_1 = 360
                y_1 = 180
                h_list = [1.0]
            polygon_list_list = utils.get_polygon_list_list(h_list, y_0, y_1, x_0, x_1)

            combined_normal_df_positive_snps = utils.get_df_positive_snps(child_snps, combined_original_df,
                                                                          json_tree_rows)
            combined_normal_df_without_other = utils.get_df_without_other(combined_normal_df_positive_snps)
            if is_extended:
                combined_extended_df = utils.get_df_extended(combined_normal_df_without_other, str_number,
                                                             json_tree_rows, child_snps, combined_original_df)

                if combined_extended_df is None:
                    continue
                else:
                    utils.get_map(combined_extended_df, True, polygon_list_list, child_snps, y_center, x_center, zoom,
                                  combination_to_color_dict, target_snp, h_list, is_web)
            else:
                utils.get_map(combined_normal_df_without_other.copy(), False, polygon_list_list, child_snps, y_center,
                              x_center, zoom, combination_to_color_dict, target_snp, h_list, is_web)
            print(datetime.datetime.now())
        else:
            print("У выбранного SNP нет дочерних SNP!")
