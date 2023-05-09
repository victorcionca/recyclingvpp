import os
import json
from typing import Dict, List
import ResultsFormatter
import datetime

directory = "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultParser/result_logs/"


def parse_exp_events(experiment_log_events: List) -> Dict:

    dnn_values = {}
    for event in experiment_log_events:
        message_content = event["message_content"]
        if event["event_type"] == 'HIGH_COMP_ALLOCATION_SUCCESS':
            dnn_id = message_content["dnn"]["dnnId"]
            if message_content["dnn"]["dnnId"] not in dnn_values.keys():
                dnn_values[dnn_id] = {"computation_time": datetime.timedelta(
                    seconds=0), "communication_time": datetime.timedelta(seconds=0)}
            dnn_values[dnn_id]["start_time"] = message_content["dnn"]["uploadData"]["start_fin_time"]["first"]

        if event["event_type"] == 'HIGH_COMP_FINISH':
            dnn = event["message_content"]["dnn_details"]
            dnn_id = dnn["dnnId"]
            dnn_values[dnn_id]["finish_time"] = event["time"]

            uploadData = dnn["uploadData"]["actual_start_fin_time"]
            upload_time = uploadData["second"] - uploadData["first"]
            dnn_values[dnn_id]["communication_time"] = dnn_values[dnn_id]["communication_time"] + upload_time

            for result_block in dnn["tasks"].values():
                largest_comm_window = datetime.timedelta(seconds=0)
                comp_time = datetime.timedelta(seconds=0)
                comm_time = datetime.timedelta(seconds=0)
                for task_block in result_block["partitioned_tasks"]:
                    task = task_block["task"]
                    partition_id = task_block["id"]
                    temp_comp_time = task["estimated_finish"] - \
                        task["estimated_start"]
                    temp_input_upload_start = task["input_data"]["actual_start_fin_time"]["first"]
                    temp_input_comm_window = task["input_data"]["actual_start_fin_time"]["second"] - \
                        task["input_data"]["actual_start_fin_time"]["first"]

                    for assembly_window in result_block["assembly_upload_windows"]:
                        if assembly_window["id"] == partition_id:
                            if assembly_window["window"]["actual_start_fin_time"]["second"] - temp_input_upload_start > largest_comm_window:
                                largest_comm_window = assembly_window["window"][
                                    "actual_start_fin_time"]["second"] - temp_input_upload_start
                                comp_time = temp_comp_time
                                comm_time = temp_input_comm_window + \
                                    (assembly_window["window"]["actual_start_fin_time"]["second"] -
                                     assembly_window["window"]["actual_start_fin_time"]["first"])

                dnn_values[dnn_id]["communication_time"] = dnn_values[dnn_id]["communication_time"] + comm_time
                dnn_values[dnn_id]["computation_time"] = dnn_values[dnn_id]["computation_time"] + comp_time

    end_to_end_time_list = []
    comp_time_list = []
    comm_time_list =[]

    for key, value in dnn_values.items():
        end_to_end_time_list.append(value["finish_time"] - value["start_time"])
        comp_time_list.append(value["computation_time"])
        comm_time_list.append(value["communication_time"])
    
    av_end_to_end = datetime.timedelta()
    av_comp = datetime.timedelta()
    av_comm = datetime.timedelta()

    return {
        "average_comm_time": sum(comm_time_list, datetime.timedelta(0)) / len(comm_time_list),
        "average_comp_time": sum(comp_time_list, datetime.timedelta(0)) / len(comp_time_list),
        "average_end_to_end": sum(end_to_end_time_list, datetime.timedelta(0)) / len(end_to_end_time_list)
    }


def main():
    file_names = os.listdir(directory)
    file_names = [name for name in file_names if name != ".DS_Store"]
    result_dict_list = {}

    for file_name in file_names:
        with open(f"{directory}{file_name}", "r") as f:
            result_dict_list[file_name] = ResultsFormatter.result_format(
                json_array=json.loads(f.read()), human_format=False)

    value_dict = {}
    for key, result in result_dict_list.items():
        value_dict[key] = parse_exp_events(experiment_log_events=result)

    end_to_end_time_list = []
    comp_time_list = []
    comm_time_list =[]

    for key, value in value_dict.items():
        end_to_end_time_list.append(value["average_end_to_end"])
        comp_time_list.append(value["average_comp_time"])
        comm_time_list.append(value["average_comm_time"])
    
    average = {
        "average_comm_time": sum(comm_time_list, datetime.timedelta(0)) / len(comm_time_list),
        "average_comp_time": sum(comp_time_list, datetime.timedelta(0)) / len(comp_time_list),
        "average_end_to_end": sum(end_to_end_time_list, datetime.timedelta(0)) / len(end_to_end_time_list)
    }

    final_average = average.copy()
    for key, value in average.items():
        final_average[f"{key}_hr"] = str(value)

    return


if __name__ == "__main__":
    main()
