import time
from multiprocessing import freeze_support

import firebase_admin
from firebase_admin import credentials, firestore

import utils

# Задаем целевой SNP, чьи дочерние SNP будут наноситься на карту.
target_snps = ['R-CTS1211', 'R-Z92']
# Задаем количество STR (12/37/67/111), которое будет использоваться на шаге предсказания SNP.
str_number = 111
# Задаем возможность перезаписи БД, если SNP уже присутствует в ней.
is_overwrite_allowed = False

if __name__ == '__main__':
    freeze_support()

    collection_name = 'new_snps'

    combined_df = utils.get_combined_df()
    json_tree_rows = utils.get_json_tree_rows()

    if not firebase_admin._apps:
        cred = credentials.Certificate('serviceAccount.json')
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    snps_list = utils.get_snps_list(collection_name, db)

    x_0 = -180
    y_0 = -90
    x_1 = 360
    y_1 = 180
    h_list = [1.0]
    polygon_list_list = utils.get_polygon_list_list(h_list, y_0, y_1, x_0, x_1)

    for target_snp in target_snps:
        if target_snp in snps_list and not is_overwrite_allowed:
            print("\nSNP {} уже присутствует в БД!".format(target_snp))
        else:
            print("\nОбрабатывается SNP {}...".format(target_snp))
            start_time = time.time()
            combined_original_df = combined_df.copy()
            new_json_tree_rows = json_tree_rows.copy()
            child_snps = utils.get_children_list(new_json_tree_rows, target_snp)
            if len(child_snps) > 0:
                print('Дочерние SNP: {}'.format(child_snps))
                combined_normal_df_positive_snps = utils.get_df_positive_snps(child_snps, combined_original_df,
                                                                              new_json_tree_rows)
                combined_normal_df_without_other = utils.get_df_without_other(combined_normal_df_positive_snps)
                if len(combined_normal_df_without_other.index) > 0:
                    print("В наборе данных combined_normal_df_without_other {} строк!"
                          .format(len(combined_normal_df_without_other.index)))
                    final_df = combined_normal_df_without_other.copy()
                    utils.get_map(final_df, polygon_list_list, child_snps, target_snp, h_list, db, collection_name)
                    snps_list.append(target_snp)
                    utils.update_db_list(collection_name, db, snps_list)
                else:
                    print("В наборе данных combined_normal_df_without_other 0 строк!")
            else:
                print("У выбранного SNP нет дочерних SNP!")
            print("Обработка SNP {} завершена за {} с".format(target_snp, time.time() - start_time))
