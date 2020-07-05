import os
import urllib.request
import urllib.parse
import json

tree_rest = 'https://www.familytreedna.com/public/y-dna-haplotree/get'


def get_json_tree_rows():
    file_name = 'ftdna_tree.txt'
    if file_name in os.listdir('./'):
        print('Файл с древом найден!')
        with open(file_name, 'r', encoding='utf-8') as file:
            json_tree_rows = json.loads(file.read())
            print('JSON разобран!')
            return json_tree_rows
    else:
        print('Файл с древом не найден! Загружаю его с сайта FTDNA...')
        with urllib.request.urlopen(tree_rest) as response:
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
