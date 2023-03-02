import os
import json
from typing import List
import ResultsFormatter
import datetime

directory = "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultParser/result_logs/"


def parse_exp_events(experiment_log_events: List):

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

                    temp_input_comm_window_fin_str = str(task["input_data"]["actual_start_fin_time"]["second"])
                    temp_input_comm_window_strt_str = str(task["input_data"]["actual_start_fin_time"]["first"])

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
    
            copy_dict = dnn_values[dnn_id].copy()
            for key, value in dnn_values[dnn_id].items():
                copy_dict[f"{key}_hr"] = str(value)
            dnn_values[dnn_id] = copy_dict
    return


def main():
    file_names = os.listdir(directory)
    file_names = [name for name in file_names if name != ".DS_Store"]
    result_dict_list = []

    for file_name in file_names:
        with open(f"{directory}{file_name}", "r") as f:
            result_dict_list.append(ResultsFormatter.result_format(
                json_array=json.loads(f.read()), human_format=False))

    for result in result_dict_list:
        parse_exp_events(experiment_log_events=result)

    return


if __name__ == "__main__":
    main()
