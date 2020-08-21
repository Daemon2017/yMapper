import datetime

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

    utils = Utils(is_extended, target_snp, str_number, x_0, y_0, x_1, y_1, x_center, y_center, zoom, h_list)
    combined_df = utils.get_positive_snps(utils.combined_df.copy())
    combined_df = utils.get_combined_df_without_other(combined_df)
    utils.get_map(combined_df)
    if is_extended:
        combined_df = utils.get_extended_data(combined_df)
        utils.get_map(combined_df)
    print(datetime.datetime.now())
