import datetime
import pandas as pd

from multiprocessing import freeze_support
from utils import Utils

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

    utils = Utils(is_extended, target_snp, str_number, x_0, y_0, x_1, y_1, x_center, y_center, zoom, h_list)
    utils.get_json_tree_rows()
    utils.get_child_snps()
    utils.get_combination_to_color_dict()

    print("Среди всех строк ищем те, что имеют положительный SNP, восходящий к одному из дочерних SNP целевого SNP.")
    combined_df = utils.get_positive_snps(combined_df)
    print("Отбрасываем строки, содержащие 'Other' в столбце 'Short Hand'.")
    combined_df = combined_df.drop(combined_df[combined_df['Short Hand'] == 'Other'].index)
    print("Количество представителей выбранной ветви: {}".format(len(combined_df.index)))
    print("Количество представителей каждой подветви: \n{}".format(combined_df['Short Hand'].value_counts()))

    utils.get_grid()

    utils.get_map(combined_df)
    if is_extended:
        combined_df = utils.get_extended_data(combined_df)
        utils.get_map(combined_df)
    print(datetime.datetime.now())
