import json

import firebase_admin
from firebase_admin import credentials, firestore

import utils

json_tree_rows = utils.get_json_tree_rows()

for i in range(ord('A'), ord('T') + 1):
    haplogroup = chr(i)
    print("Обрабатывается ГГ {}...".format(haplogroup))

    new_all_nodes = {}
    for node in json_tree_rows['allNodes']:
        if json_tree_rows['allNodes'][node]['name'].startswith('{}-'.format(haplogroup)):
            new_all_nodes[node] = {
                'name': json_tree_rows['allNodes'][node]['name']
            }
            if 'children' in json_tree_rows['allNodes'][node]:
                new_all_nodes[node]['children'] = json_tree_rows['allNodes'][node]['children']
            if 'parentId' in json_tree_rows['allNodes'][node]:
                new_all_nodes[node]['parentId'] = json_tree_rows['allNodes'][node]['parentId']

    new_json_tree_rows = {'allNodes': new_all_nodes}

    if not firebase_admin._apps:
        cred = credentials.Certificate('serviceAccount.json')
        firebase_admin.initialize_app(cred)
    db = firestore.client()

    doc_ref = db.collection("haplotrees").document(haplogroup)
    doc_ref.set({
        u'data': json.dumps(new_json_tree_rows)
    })
