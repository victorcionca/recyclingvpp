import json
from datetime import datetime as dt

log_name = "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultParser/result_log.json"


def time_to_string(time_int):
    return dt.fromtimestamp(time_int / 1000).strftime("%Y-%m-%d %H:%M:%S.%f")


def link_parse(link):
    link["actual_start_fin_time"]["first"] = time_to_string(
        link["actual_start_fin_time"]["first"])
    link["actual_start_fin_time"]["second"] = time_to_string(
        link["actual_start_fin_time"]["second"])
    link["start_fin_time"]["first"] = time_to_string(
        link["start_fin_time"]["first"])
    link["start_fin_time"]["second"] = time_to_string(
        link["start_fin_time"]["second"])
    return link


def task_parse(task):
    task["estimated_start"] = time_to_string(task["estimated_start"])
    task["estimated_finish"] = time_to_string(task["estimated_finish"])
    task["actual_finish"] = time_to_string(task["actual_finish"])
    task["input_data"] = link_parse(task["input_data"])
    return task


def low_comp_allocation_parse(dnn_dict):
    dnn_dict["deadline"] = time_to_string(dnn_dict["deadline"])
    dnn_dict["estimatedStart"] = time_to_string(dnn_dict["estimatedStart"])
    dnn_dict["estimatedFinish"] = time_to_string(dnn_dict["estimatedFinish"])
    dnn_dict["task"] = task_parse(dnn_dict["task"])
    return dnn_dict


def result_block_parse(res_block):
    res_block["assembly_fin_time"] = time_to_string(
        res_block["assembly_fin_time"])
    res_block["assembly_start_time"] = time_to_string(
        res_block["assembly_start_time"])
    res_block["state_update_fin_time"] = time_to_string(
        res_block["state_update_fin_time"])
    res_block["state_update"] = link_parse(res_block["state_update"])

    for i in range(0, len(res_block["assembly_upload_windows"])):
        res_block["assembly_upload_windows"][i]["window"] = link_parse(
            res_block["assembly_upload_windows"][i]["window"])

    for i in range(0, len(res_block["partitioned_tasks"])):
        res_block["partitioned_tasks"][i]["task"] = task_parse(
            res_block["partitioned_tasks"][i]["task"])
    return res_block


def high_comp_parse(dnn):
    dnn["deadline"] = time_to_string(dnn["deadline"])
    dnn["estimatedFinish"] = time_to_string(dnn["estimatedFinish"])
    dnn["estimatedStart"] = time_to_string(dnn["estimatedStart"])
    dnn["uploadData"] = link_parse(dnn["uploadData"])

    for task_key in dnn["tasks"].keys():
        dnn["tasks"][task_key] = result_block_parse(dnn["tasks"][task_key])

    return dnn


def main():
    file = open(log_name, "r")
    json_array = json.loads(file.read())
    file.close()

    for event in json_array:
        event["time"] = time_to_string(event["time"])

        if event["event_type"] == "LOW_COMP_REQUEST":
            event["message_content"]["deadline"] = time_to_string(
                event["message_content"]["deadline"])
        elif event["event_type"] == "LOW_COMP_ALLOCATION_SUCCESS":
            event["message_content"]["dnn_details"] = low_comp_allocation_parse(
                event["message_content"]["dnn_details"])
        elif event["event_type"] == 'OUTBOUND_LOW_COMP_ALLOCATION':
            event["message_content"]["comm_time"] = time_to_string(
                event["message_content"]["comm_time"] / 1000)
            event["message_content"]["dnn"] = low_comp_allocation_parse(
                event["message_content"]["dnn"])
        elif event["event_type"] == 'HIGH_COMP_REQUEST':
            event["message_content"]["deadline"] = time_to_string(
                event["message_content"]["deadline"])
        elif event["event_type"] == "HIGH_COMP_ALLOCATION_SUCCESS":
            event["message_content"]["dnn"] = high_comp_parse(
                event["message_content"]["dnn"])
        elif event["event_type"] == 'OUTBOUND_TASK_ALLOCATION_HIGH':
            event["message_content"]["comm_time"] = time_to_string(
                event["message_content"]["comm_time"] / 1000)
            event["message_content"]["dnn"] = high_comp_parse(
                event["message_content"]["dnn"])
        elif event["event_type"] == 'STATE_UPDATE_REQUEST':
            for finish_time_key in event["message_content"]["finish_times"].keys():
                event["message_content"]["finish_times"][finish_time_key]["finish_time"] = time_to_string(event["message_content"]["finish_times"][finish_time_key]["finish_time"])
                event["message_content"]["finish_times"][finish_time_key]["assembly_upload_start"] = time_to_string(event["message_content"]["finish_times"][finish_time_key]["assembly_upload_start"])
                event["message_content"]["finish_times"][finish_time_key]["assembly_upload_finish"] = time_to_string(event["message_content"]["finish_times"][finish_time_key]["assembly_upload_finish"])

        elif event["event_type"] == 'DAG_DISRUPTION_REQUEST':
            event["message_content"]["finish_time"] = time_to_string(event["message_content"]["finish_time"])

        elif event["event_type"] == 'OUTBOUND_STATE_UPDATE':
            event["message_content"]["comm_time"] = time_to_string(
                event["message_content"]["comm_time"] / 1000)

            event["message_content"]["dnn"] = high_comp_parse(event["message_content"]["dnn"])

        elif event["event_type"] == 'HIGH_COMP_FINISH':
            event["message_content"]["dnn_details"] = high_comp_parse(event["message_content"]["dnn_details"])

        elif event["event_type"] == 'OUTBOUND_PRUNE':
            event["message_content"]["comm_time"] = time_to_string(
                event["message_content"]["comm_time"] / 1000)

    with open('./result_parsed.json', 'w') as f:
        json.dump(json_array, f, indent=4)

    return


if __name__ == "__main__":
    main()
