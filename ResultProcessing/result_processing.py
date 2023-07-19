import sys
import json
import datetime
import statistics

valid_event_items = [
    "LOW_COMP_ALLOCATION_SUCCESS",
    "LOW_COMP_REQUEST",
    "HIGH_COMP_FINISH",
    "LOW_COMP_FINISH",
    "LOW_COMP_ALLOCATION_FAIL",
    "LOW_COMP_ALLOCATION_SUCCESS",
    "LOW_COMP_PREMPT_ALLOCATION_SUCCESS",
    "HIGH_COMP_ALLOCATION_SUCCESS",
    "HIGH_COMP_ALLOCATION_FAIL",
    "HIGH_COMP_REALLOCATION_FAIL",
    "HALT_DNN",
    "HIGH_COMP_REALLOCATION_SUCCESS",
    "VIOLATED_DEADLINE",
    "OUTBOUND_LOW_COMP_ALLOCATION",
    "HIGH_COMP_REQUEST",
    "OUTBOUND_TASK_ALLOCATION_HIGH",
]


def generate_event_array(file_name):
    result_file = open(file_name, "r")
    result_text = result_file.read()
    result_file.close()
    result_event_array = json.loads(result_text)
    low_comp_last_state_dict = {}
    high_comp_last_state_dict = {}
    for i in range(0, len(result_event_array)):
        event = result_event_array[i]
        if event["event_type"] in valid_event_items:
            dnn_id = ""
            event_content = event["message_content"]
            if "dnn_details" in event_content.keys():
                dnn_id = event_content["dnn_details"]["dnn_id"]
            elif "dnn" in event_content.keys():
                dnn_id = event_content["dnn"]["dnn_id"]
            elif "dnn_id" in event_content.keys():
                dnn_id = event_content["dnn_id"]

            if "LOW_COMP" in event["event_type"]:
                if dnn_id not in low_comp_last_state_dict:
                    low_comp_last_state_dict[dnn_id] = {}
                low_comp_last_state_dict[dnn_id][event["event_type"]] = event["time"]
            else:
                if event["event_type"] == "HIGH_COMP_REQUEST":
                    dnn_base_id = event["message_content"]["dnn_id"]
                    task_count = event["message_content"]["task_count"]

                    for i in range(0, task_count):
                        dnn_id = f"{dnn_base_id}_{i}"

                        if dnn_id not in high_comp_last_state_dict:
                            high_comp_last_state_dict[dnn_id] = []
                        high_comp_last_state_dict[dnn_id].append(
                            (event["event_type"], event["time"])
                        )
                else:
                    if dnn_id not in high_comp_last_state_dict:
                        high_comp_last_state_dict[dnn_id] = []
                    high_comp_last_state_dict[dnn_id].append(
                        (event["event_type"], event["time"])
                    )
    return low_comp_last_state_dict, high_comp_last_state_dict, result_event_array


def low_high_summary_processing(
    low_comp_last_state_dict, high_comp_last_state_dict, event_list
):
    total_low_comp_count = len(low_comp_last_state_dict.keys())
    low_comp_success_count = 0
    low_comp_preempt_success_count = 0
    low_comp_fail_count = 0
    low_comp_allocation_times_preemp = []
    low_comp_allocation_times_no_preemp = []

    for dnn_result_map in low_comp_last_state_dict.values():
        dnn_result = list(dnn_result_map.keys())
        if "LOW_COMP_FINISH" in dnn_result:
            low_comp_success_count = low_comp_success_count + 1
            if "LOW_COMP_PREMPT_ALLOCATION_SUCCESS" in dnn_result:
                low_comp_preempt_success_count = low_comp_preempt_success_count + 1

        if (
            "LOW_COMP_ALLOCATION_FAIL" in dnn_result
            and "LOW_COMP_FINISH" not in dnn_result
        ):
            low_comp_fail_count = low_comp_fail_count + 1

        if "OUTBOUND_LOW_COMP_ALLOCATION" in dnn_result:
            allo_time = (
                dnn_result_map["OUTBOUND_LOW_COMP_ALLOCATION"]
                - dnn_result_map["LOW_COMP_REQUEST"]
            )
            if "LOW_COMP_PREMPT_ALLOCATION_SUCCESS" in dnn_result:
                low_comp_allocation_times_preemp.append(allo_time)
            else:
                low_comp_allocation_times_no_preemp.append(allo_time)

    if len(low_comp_allocation_times_preemp) == 0:
        low_comp_allocation_times_preemp = [0, 0]
    if len(low_comp_allocation_times_no_preemp) == 0:
        low_comp_allocation_times_no_preemp = [0, 0]

    avg_low_comp_allocation_times_preemp = statistics.mean(
        low_comp_allocation_times_preemp
    )
    avg_low_comp_allocation_times_no_preemp = statistics.mean(
        low_comp_allocation_times_no_preemp
    )

    stdev_low_comp_allocation_times_no_preemp = statistics.stdev(
        low_comp_allocation_times_no_preemp
    )

    stdev_low_comp_allocation_times_preemp = statistics.stdev(
        low_comp_allocation_times_preemp
    )

    total_high_comp_count = len(high_comp_last_state_dict.keys())
    high_comp_success_count = 0
    high_comp_fail = 0
    high_comp_prempt_fail = 0
    high_comp_prempt_success = 0
    high_comp_finish = 0
    high_comp_violated = 0

    high_comp_allocation_times_initial = []
    high_comp_allocation_times_reallo = generate_high_comp_reallocation_time(event_list)
    halt_dict = generate_halt_breakdown(event_list)

    for dnn_id, dnn_result_map in high_comp_last_state_dict.items():
        dnn_result = [event[0] for event in dnn_result_map]
        if "HIGH_COMP_FINISH" in dnn_result:
            high_comp_finish = high_comp_finish + 1
        if "OUTBOUND_TASK_ALLOCATION_HIGH" in dnn_result:
            high_comp_success_count = high_comp_success_count + 1
        if "VIOLATED_DEADLINE" in dnn_result:
            high_comp_violated += 1
        if "HIGH_COMP_ALLOCATION_FAIL" in dnn_result:
            high_comp_fail += 1
        if "HIGH_COMP_REALLOCATION_SUCCESS" in dnn_result:
            high_comp_prempt_success += 1
        if "HIGH_COMP_REALLOCATION_FAIL" in dnn_result:
            high_comp_prempt_fail += 1

        if (
            "HIGH_COMP_ALLOCATION_SUCCESS" in dnn_result
            and "OUTBOUND_TASK_ALLOCATION_HIGH" in dnn_result
        ):
            high_comp_allocation_times_initial.append(
                dnn_result_map[2][1] - dnn_result_map[0][1]
            )

    avg_high_comp_allocation_times_initial = statistics.mean(
        high_comp_allocation_times_initial
    )
    stdev_high_comp_allocation_times_initial = statistics.stdev(
        high_comp_allocation_times_initial
    )

    if len(high_comp_allocation_times_reallo) == 0:
        high_comp_allocation_times_reallo = [0, 0]
    avg_high_comp_allocation_times_reallo = statistics.mean(
        high_comp_allocation_times_reallo
    )
    stdev_high_comp_allocation_times_reallo = statistics.stdev(
        high_comp_allocation_times_reallo
    )

    two_by_two_list = []
    one_by_two_list = []

    for item in halt_dict.values():
        if item == "2_2":
            two_by_two_list.append(True)
        else:
            one_by_two_list.append(True)


    return {
        "low_comp_results": {
            "total_low_comp_count": total_low_comp_count,
            "low_comp_success_count": low_comp_success_count,
            "low_comp_preempt_success_count": low_comp_preempt_success_count,
            "low_comp_fail_count": low_comp_fail_count,
            "avg_low_comp_allocation_times_preemp": avg_low_comp_allocation_times_preemp,
            "avg_low_comp_allocation_times_no_preemp": avg_low_comp_allocation_times_no_preemp,
            "stdev_low_comp_allocation_times_no_preemp": stdev_low_comp_allocation_times_no_preemp,
            "stdev_low_comp_allocation_times_preemp": stdev_low_comp_allocation_times_preemp,
        },
        "high_comp_results": {
            "total_high_comp_count": total_high_comp_count,
            "high_comp_success_count": high_comp_success_count,
            "high_comp_fail": high_comp_fail,
            "high_comp_prempt_fail": high_comp_prempt_fail,
            "high_comp_prempt_success": high_comp_prempt_success,
            "high_comp_finish": high_comp_finish,
            "high_comp_violated": high_comp_violated,
            "avg_high_comp_allocation_times_initial": avg_high_comp_allocation_times_initial,
            "stdev_high_comp_allocation_times_initial": stdev_high_comp_allocation_times_initial,
            "avg_high_comp_allocation_times_reallo": avg_high_comp_allocation_times_reallo,
            "stdev_high_comp_allocation_times_reallo": stdev_high_comp_allocation_times_reallo,
            "high_comp_1x2_preemp": len(one_by_two_list),
            "high_comp_2x2_preemp": len(two_by_two_list),
        },
    }


def main(file_name, result_name):
    (
        low_comp_last_state_dict,
        high_comp_last_state_dict,
        event_list,
    ) = generate_event_array(file_name)

    result_dictionary = low_high_summary_processing(
        low_comp_last_state_dict, high_comp_last_state_dict, event_list
    )

    frame_completion = generate_frame_completion(event_list)

    offloaded_and_completed = []
    high_comp_dict = set()

    for item in event_list:
        if item["event_type"] == 'OUTBOUND_TASK_ALLOCATION_HIGH':
            dnn = item["message_content"]["dnn"]

            if dnn["source_host"] != "allocated_host":
                high_comp_dict.add(dnn["dnn_id"])
    
    for item in event_list:
        if item["event_type"] == "HIGH_COMP_FINISH":
            dnn = item["message_content"]["dnn_details"]
            if dnn["dnn_id"] in high_comp_dict:
                offloaded_and_completed.append(dnn["dnn_id"])


    num_frames_completed = 0
    average_high_comp_complete_list = []

    for item in frame_completion:
        if item["frame_completed"] == True:
            num_frames_completed += 1
        if item["high_comp_task"] == True:
            average_high_comp_complete_list.append(len(item["high_comp_tasks"]) / item["high_comp_task_count"])

    result_dictionary["general_stats"] = {
        "frames_generated": len(frame_completion),
        "frames_completed": num_frames_completed,
        "average_high_comp_completed": statistics.mean(average_high_comp_complete_list),
        "stdev_high_comp_completed": statistics.stdev(average_high_comp_complete_list),
        "offloaded_tasks": len(high_comp_dict),
        "completed_offloaded_tasks": len(offloaded_and_completed)
    }
    output_file = open(result_name, "w")
    output_file.write(json.dumps(result_dictionary))
    output_file.close()
    return


def generate_frame_completion(event_list):

    device_list = [event["message_content"]["host"] for event in event_list if event["event_type"] == "DEVICE_REGISTER"]

    frame_list = []

    for i in range(0, len(event_list)):
        print(f"{i} out of {len(event_list)}")
        if event_list[i]["event_type"] == "LOW_COMP_REQUEST":
            result_obj = {
                "low_comp_id": event_list[i]["message_content"]["dnn_id"],
                "low_comp_completed": False,
                "high_comp_task": False,
                "frame_completed": False
            }

            last_index = -1
            for j in range(i + 1, len(event_list)):
                if event_list[j]["event_type"] == "LOW_COMP_FINISH" and event_list[j]["message_content"]["dnn_details"]["dnn_id"] == result_obj["low_comp_id"]:
                    result_obj["low_comp_completed"] = True
                    last_index = j
                    break
            
            if result_obj["low_comp_completed"] == False:
                frame_list.append(result_obj)
                continue
            
            device = result_obj["low_comp_id"].split("_")[0]
            next_base_id_counter = int(result_obj["low_comp_id"].split("_")[1])
            next_id = f"{device}_{next_base_id_counter + 1}"

            for j in range(last_index + 1, len(event_list)):
                if event_list[j]["event_type"] == "HIGH_COMP_REQUEST" and event_list[j]["message_content"]["dnn_id"] == next_id:
                    event_item = event_list[j]
                    result_obj["high_comp_task"] = True
                    result_obj["high_comp_base_id"] = next_id
                    result_obj["high_comp_task_count"] = event_item["message_content"]["task_count"]
                    result_obj["high_comp_tasks"] = []

                    for y in range(0, result_obj["high_comp_task_count"]):
                        for k in range(j + 1, len(event_list)):
                            if event_list[k]["event_type"] == "HIGH_COMP_FINISH" and event_list[k]["message_content"]["dnn_details"]["dnn_id"] == f"{next_id}_{y}":
                                result_obj["high_comp_tasks"].append(f"{next_id}_{y}")

            if result_obj["high_comp_task"] == False:
                result_obj["frame_completed"] = True

            elif result_obj["high_comp_task"] == True and len(result_obj["high_comp_tasks"]) == result_obj["high_comp_task_count"]:
                result_obj["frame_completed"] = True
            
            frame_list.append(result_obj)

    return frame_list


def generate_halt_breakdown(event_list):
    halt_list = []
    halt_dict = {}

    for item in event_list:
        if item["event_type"] == "HIGH_COMP_REALLOCATION_SUCCESS":
            halt_list.append(item["message_content"]["dnn"]["dnn_id"])
        elif item["event_type"] == "HIGH_COMP_REALLOCATION_FAIL":
            halt_list.append(item["message_content"]["dnn_id"])

    for event_item in event_list:
        if event_item["event_type"] == "OUTBOUND_TASK_ALLOCATION_HIGH":
            dnn = event_item["message_content"]["dnn"]
            if dnn["dnn_id"] in halt_list and dnn["dnn_id"] not in halt_dict:
                halt_dict[dnn["dnn_id"]] = f"{dnn['N']}_{dnn['M']}"
    
    return halt_dict


def generate_high_comp_reallocation_time(event_list):
    new_events = []

    halt_times = []

    for i in range(0, len(event_list)):
        if event_list[i]["event_type"] == "OUTBOUND_HALT_REQUEST":
            new_events.append(event_list[i : i + 7])

    for events in new_events:
        transform_list = [event["event_type"] for event in events]
        if "HIGH_COMP_REALLOCATION_SUCCESS" in transform_list:
            halt_times.append(events[-1]["time"] - events[0]["time"])
    
    return halt_times


def create_time_stamp(ms_since_epoch: int):
    # Create a datetime object using timedelta to represent the duration since the epoch
    duration_since_epoch = datetime.timedelta(milliseconds=ms_since_epoch)

    # Add the duration to the epoch datetime (January 1, 1970)
    epoch_datetime = datetime.datetime(1970, 1, 1)
    return epoch_datetime + duration_since_epoch


if __name__ == "__main__":
    file_name = sys.argv[1]
    result_name = sys.argv[2]

    main(file_name, result_name)
