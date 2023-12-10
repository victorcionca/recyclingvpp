import random
import json
from itertools import permutations

number_of_values = 1296
values = [-1, 0, 1, 2, 3, 4]
weights = [0.05, 0.05, 0.4, 0.2, 0.2, 0.1]
device_count = 4
file_name = "../trace_files/weighted_trace_file_1.json"

def main():

    # options = [0.4, 0.2, 0.2, 0.1]

    # weighted_1 = [0.4, 0.2, 0.2, 0.1]
    # weighted_2 = [0.2, 0.4, 0.2, 0.1]
    # weighted_3 = [0.1, 0.2, 0.4, 0.2]
    # weighted_4 = [0.1, 0.2, 0.2, 0.4]

    # permutations_list = list(permutations(options, 4))

    results_arr = [random.choices(values, weights, k=device_count) for i in range(0, 1296)]

    res_file = open(file_name, "w")

    res_file.writelines(json.dumps(results_arr))
    res_file.close()
    return


if __name__ == "__main__":
    main()