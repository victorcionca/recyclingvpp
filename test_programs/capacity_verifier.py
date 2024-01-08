import sys
import json
from datetime import datetime as dt
import copy

LOW_COMP_REQUEST = "LOW_COMP_REQUEST"
HIGH_COMP_REQUEST = "HIGH_COMP_REQUEST"
DEVICE_REGISTER = "DEVICE_REGISTER"
IPERF_RESULTS = "IPERF_RESULTS"
DAG_DISRUPTION_REQUEST = "DAG_DISRUPTION_REQUEST"
STATE_UPDATE_REQUEST = "STATE_UPDATE_REQUEST"
HIGH_COMP_FINISH = "HIGH_COMP_FINISH"
LOW_COMP_ALLOCATION_FAIL = "LOW_COMP_ALLOCATION_FAIL"
LOW_COMP_ALLOCATION_SUCCESS = "LOW_COMP_ALLOCATION_SUCCESS"
LOW_COMP_PREMPT_ALLOCATION_SUCCESS = "LOW_COMP_PREMPT_ALLOCATION_SUCCESS"
LOW_COMP_FINISH = "LOW_COMP_FINISH"
HALT_REQUEST = "HALT_REQUEST"
HIGH_COMP_ALLOCATION_CORE_FAIL = "HIGH_COMP_ALLOCATION_CORE_FAIL"
HIGH_COMP_ALLOCATION_SUCCESS = "HIGH_COMP_ALLOCATION_SUCCESS"
HIGH_COMP_ALLOCATION_FAIL = "HIGH_COMP_ALLOCATION_FAIL"
HIGH_COMP_REALLOCATION_FAIL = "HIGH_COMP_REALLOCATION_FAIL"
DAG_DISRUPTION_SUCCESS = "DAG_DISRUPTION_SUCCESS"
DAG_DISRUPTION_FAIL = "DAG_DISRUPTION_FAIL"
HALT_DNN = "HALT_DNN"
ADD_WORK_TASK = "ADD_WORK_TASK"
EXPERIMENT_INITIALISE = "EXPERIMENT_INITIALISE"
OUTBOUND_STATE_UPDATE = "OUTBOUND_STATE_UPDATE"
OUTBOUND_TASK_ALLOCATION_HIGH = "OUTBOUND_TASK_ALLOCATION_HIGH"
OUTBOUND_TASK_REALLOCATION_HIGH = "OUTBOUND_TASK_REALLOCATION_HIGH"
OUTBOUND_HALT_REQUEST = "OUTBOUND_HALT_REQUEST"
OUTBOUND_LOW_COMP_ALLOCATION = "OUTBOUND_LOW_COMP_ALLOCATION"
ADD_NETWORK_TASK = "ADD_NETWORK_TASK"
HIGH_COMP_REALLOCATION_SUCCESS = "HIGH_COMP_REALLOCATION_SUCCESS"
VIOLATED_DEADLINE = "VIOLATED_DEADLINE"
VIOLATED_DEADLINE_REQUEST = "VIOLATED_DEADLINE_REQUEST"
WORK_REQUEST = "WORK_REQUEST"



def main():

    file_path = "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/test_programs/capacity_test_result.json"
    # file_path += sys.argv[1]

    json_file = open(file_path, "r")
    text = json_file.read()

    json_loaded = json.loads(text)

    
    device_ids_list = []

    counter = 0
    while True:
        event = json_loaded[counter]
        
        if event["event_type"] != DEVICE_REGISTER:
            break
        else:
            device_ids_list.append(event["message_content"]["host"])
        counter += 1

    json_loaded = json_loaded[counter:]

    device_ids_dict = {d_id: [] for d_id in device_ids_list}
    

    violated_list = []
    existing_allocation_list = []

    for i in range(0, len(json_loaded)):
        event = json_loaded[i]

        # if event["event_type"] == VIOLATED_DEADLINE:
            # violated_list.append(event["message_content"]["dnn"]["dnn_id"])
        
    resource_list = {}

    for i in range(0, len(json_loaded)):
        event = json_loaded[i]
        if event["event_type"]  [HIGH_COMP_ALLOCATION_SUCCESS, HIGH_COMP_REALLOCATION_SUCCESS]:
            msg_content = event["message_content"]
            allocated_host = msg_content["dnn"]["allocated_host"]
            dnn = msg_content["dnn"]
            start = dt.fromtimestamp(dnn["estimated_start"] / 1000)
            usage = dnn["N"] * dnn["M"]

            resource_list[dnn["dnn_id"]] = {"type": "increase", "usage": usage, "time": start, "dnn_id": dnn["dnn_id"]}
        elif event["event_type"] in [LOW_COMP_ALLOCATION_SUCCESS, LOW_COMP_PREMPT_ALLOCATION_SUCCESS]:
            msg_content = event["message_content"]
            allocated_host = msg_content["dnn"]["source_host"]
            dnn = msg_content["dnn"]
            start = dt.fromtimestamp(dnn["estimated_start"] / 1000)
            
            resource_list[dnn["dnn_id"]] = {"type": "increase", "usage": 1, "time": start, "dnn_id": dnn["dnn_id"]}
        elif event["event_type"] in [HIGH_COMP_FINISH, VIOLATED_DEADLINE]:
            msg_content = event["message_content"]
            allocated_host = msg_content["dnn"]["allocated_host"]
            dnn = msg_content["dnn"]
            usage = dnn["N"] * dnn["M"]
            finish = dt.fromtimestamp(event["time"] / 1000)
            device_ids_dict[allocated_host].append(resource_list[dnn["dnn_id"]])
            device_ids_dict[allocated_host].append({"type": "decrease", "usage": usage, "time": finish, "dnn_id": dnn["dnn_id"]})
        elif event["event_type"] == LOW_COMP_FINISH: 
            msg_content = event["message_content"]
            allocated_host = msg_content["dnn"]["source_host"]
            dnn = msg_content["dnn"]
            finish = dt.fromtimestamp(event["time"] / 1000)
            device_ids_dict[allocated_host].append(resource_list[dnn["dnn_id"]])
            device_ids_dict[allocated_host].append({"type": "decrease", "usage": 1, "time": finish, "dnn_id": dnn["dnn_id"]})

    for id_d in device_ids_list:
        device_ids_dict[id_d] = sorted(device_ids_dict[id_d], key=lambda x: x["time"])

    device_cap_violated_dict = {d_id: {"over": 0, "under": 0} for d_id in device_ids_list}

    max_violation = 0
    largest_core_usage = 0

    for device_cap_key, device_cap_list in device_ids_dict.items():
        active_capacity = 0

        for usage_item in device_cap_list:
            if usage_item["type"] == "increase":
                active_capacity += usage_item["usage"]
            else:
                active_capacity -= usage_item["usage"]

            if active_capacity >= largest_core_usage:
                    largest_core_usage = active_capacity

            if active_capacity > 4:
                if active_capacity > max_violation:
                    max_violation = active_capacity
                # print(f"{device_cap_key}: CAPACITY EXCEEDED {active_capacity}")
                device_cap_violated_dict[device_cap_key]["over"] += 1
            elif active_capacity < 0:
                device_cap_violated_dict[device_cap_key]["under"] += 1
                # print(f"{device_cap_key}: CAPACITY VIOLATED {active_capacity}")
        
    print(device_cap_violated_dict)
    print(f"MAX VIOLATION {max_violation}")
    print(f"LARGEST CORE USAGE {largest_core_usage}")
    return


if __name__ == "__main__":
    main()