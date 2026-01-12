import json

import utils

json_tree_rows = utils.get_json_tree_rows()
target_snp = "R-Z92"
list_of_descendants = utils.get_descendants_list(json_tree_rows, target_snp)
print(json.dumps(list_of_descendants))
