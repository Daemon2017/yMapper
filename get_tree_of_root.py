import json

import utils

letter = 'A'
json_tree_rows = utils.get_json_tree_rows()

new_all_nodes = {}
for node in json_tree_rows['allNodes']:
    if json_tree_rows['allNodes'][node]['name'].startswith('{}-'.format(letter)):
        new_all_nodes[node] = {
            'name': json_tree_rows['allNodes'][node]['name']
        }
        if 'children' in json_tree_rows['allNodes'][node]:
            new_all_nodes[node]['children'] = json_tree_rows['allNodes'][node]['children']
        if 'parentId' in json_tree_rows['allNodes'][node]:
            new_all_nodes[node]['parentId'] = json_tree_rows['allNodes'][node]['parentId']

new_json_tree_rows = {'allNodes': new_all_nodes}
with open('trees/{}.json'.format(letter), 'w') as fp:
    json.dump(new_json_tree_rows, fp)
