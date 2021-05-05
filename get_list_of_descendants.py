import json

import utils


def get_list_of_descendants(start):
    stack = [start]
    snps = []
    while stack:
        current_snp = stack.pop()
        snps.append(current_snp)
        stack.extend(snp for snp in utils.get_children_list(json_tree_rows, current_snp))
    return snps


json_tree_rows = utils.get_json_tree_rows()
target_snp = "R-Z92"
list_of_descendants = get_list_of_descendants(target_snp)
print(json.dumps(list_of_descendants))
