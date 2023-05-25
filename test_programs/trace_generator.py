from itertools import permutations
import random
import json

options = [-1, 0, 1, 2, 3, 4]
permutations_list = list(permutations(options, 4))

random.shuffle(permutations_list)
res_file = open("trace_file.json", "w")

res_file.writelines(json.dumps(permutations_list))
res_file.close()