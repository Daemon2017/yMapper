import json
from itertools import islice

import firebase_admin
from firebase_admin import credentials, firestore

import utils


def chunks(data, size):
    it = iter(data)
    for i in range(0, len(data), size):
        yield {k: data[k] for k in islice(it, size)}


json_tree_rows = utils.get_json_tree_rows()

new_all_nodes = {}
for node in json_tree_rows['allNodes']:
    new_all_nodes[node] = {
        'name': json_tree_rows['allNodes'][node]['name']
    }
    if 'children' in json_tree_rows['allNodes'][node]:
        new_all_nodes[node]['children'] = json_tree_rows['allNodes'][node]['children']
    if 'parentId' in json_tree_rows['allNodes'][node]:
        new_all_nodes[node]['parentId'] = json_tree_rows['allNodes'][node]['parentId']

if not firebase_admin._apps:
    cred = credentials.Certificate('serviceAccount.json')
    firebase_admin.initialize_app(cred)
db = firestore.client()

i = 0
for item in chunks(new_all_nodes, 10000):
    doc_ref = db.collection("haplotree").document("part" + str(i))
    doc_ref.set({
        u'data': json.dumps(item)
    })
    i = i + 1
