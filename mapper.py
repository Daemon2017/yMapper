import datetime
from multiprocessing import freeze_support

import firebase_admin
from firebase_admin import credentials, firestore

import utils

# Выбираем стратегию работы с данными:
# * False - если хотим работать только с теми данными, что 100% подтверждены BigY500/BigY700/SNP;
# * True - если хотим работать с наибольшим возможным количеством данных, полученным в результате предсказания SNP по
#  STR с некоторой точностью.
is_extended = False
# Задаем целевой SNP, чьи дочерние SNP будут наноситься на карту.
target_snps = ['R-CTS1211', 'R-Z92']
# Задаем количество STR (12/37/67/111), которое будет использоваться на шаге предсказания SNP.
str_number = 111
# Задаем возможность перезаписи БД, если SNP уже присутствует в ней.
is_overwrite_allowed = False

if __name__ == '__main__':
    freeze_support()

    collection_name = ''
    if is_extended:
        collection_name = 'new_snps_extended'
    else:
        collection_name = 'new_snps'

    combined_df = utils.get_combined_df()
    json_tree_rows = utils.get_json_tree_rows()

    if not firebase_admin._apps:
        cred = credentials.Certificate('serviceAccount.json')
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    snps_list = utils.get_snps_list(collection_name, db)

    for target_snp in target_snps:
        if target_snp in snps_list and not is_overwrite_allowed:
            print("\nSNP {} уже присутствует в БД!".format(target_snp))
        else:
            print("\nОбрабатывается SNP {}...".format(target_snp))
            print(datetime.datetime.now())
            combined_original_df = combined_df.copy()
            new_json_tree_rows = json_tree_rows.copy()
            child_snps = utils.get_child_snps(new_json_tree_rows, target_snp)
            if len(child_snps) > 0:
                x_0 = -180
                y_0 = -90
                x_1 = 360
                y_1 = 180
                h_list = [1.0]
                polygon_list_list = utils.get_polygon_list_list(h_list, y_0, y_1, x_0, x_1)

                combined_normal_df_positive_snps = utils.get_df_positive_snps(child_snps, combined_original_df,
                                                                              new_json_tree_rows)
                combined_normal_df_without_other = utils.get_df_without_other(combined_normal_df_positive_snps)
                if len(combined_normal_df_without_other.index) > 0:
                    final_df = combined_normal_df_without_other.copy()
                    if is_extended:
                        final_df = utils.get_df_extended(combined_normal_df_without_other, str_number,
                                                         new_json_tree_rows,
                                                         child_snps, combined_original_df)
                        if final_df is None:
                            continue
                    utils.get_map(final_df, polygon_list_list, child_snps, target_snp, h_list, db, collection_name)
                    snps_list.append(target_snp)
                    utils.update_db_list(collection_name, db, snps_list)
                else:
                    print("В наборе данных combined_normal_df_without_other 0 строк!")
            else:
                print("У выбранного SNP нет дочерних SNP!")
            print("Завершена обработка SNP {}".format(target_snp))
            print(datetime.datetime.now())
