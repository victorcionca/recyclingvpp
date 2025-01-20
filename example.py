file_data = ""
unique_fuel_types_dict = {}
data = None
with open("sales.csv", "r") as f:
    data = f.readlines()

for line in data:
    split_data = (str(data)).split(",")

    fuel_type = split_data[1]
    distance_travelled = int(split_data[2])
    litres_consumed = int(split_data[3])
    if (fuel_type not in unique_fuel_types_dict.keys()):
        unique_fuel_types_dict[split_data[1]] = {
            "distance": 0,
            "litres": 0
        }
    

    unique_fuel_types_dict[fuel_type]["distance"] += distance_travelled
    unique_fuel_types_dict[fuel_type]["litres"] += litres_consumed
