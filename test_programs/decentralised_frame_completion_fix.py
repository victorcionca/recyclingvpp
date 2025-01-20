import json
import statistics

weighted_four_trace_path = "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/trace_files/weighted_trace_file_4.json"
weighted_four_preempt = "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/ExperimentLogs/weighted_4_worksteal_preempt_decentralised.json"
weighted_four_non_preempt = "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/ExperimentLogs/weighted_4_worksteal_no_preempt_decentralised.json"

frame_comp_fix_result_file = "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/ResultFolder/decent_frame_comp_fix.json"
def main():

    weighted_json = {}
    with open(weighted_four_trace_path, "r") as f:
        weighted_json = json.load(f)
    
    preempt_frame_comp, preempt_avg_task_comp, preempt_low, preempt_high, preemp_low_comp, preempt_avg_task_comp_stdev, preemp_high_comp =  generate_frame_completion(weighted_json, weighted_four_preempt)
    non_preempt_frame_comp, non_preempt_avg_task_comp, non_preempt_low, non_preempt_high, non_preemp_low_comp, non_preempt_avg_task_comp_stdev, non_preemp_high_comp = generate_frame_completion(weighted_json, weighted_four_non_preempt)

    result_dict = {
        "preempt": {
            "frame_completion": preempt_frame_comp,
            "avg_task_comp": preempt_avg_task_comp,
            "avg_task_comp_stdev": preempt_avg_task_comp_stdev,
            "total_high": preempt_low,
            "total_low": preempt_high,
            "total_high": preemp_low_comp,
            "total_high_completion": preemp_high_comp
        },
        "non_preempt": {
            "frame_completion": non_preempt_frame_comp,
            "avg_task_comp": non_preempt_avg_task_comp,
            "avg_task_comp_stdev": non_preempt_avg_task_comp_stdev,
            "total_high": non_preempt_low,
            "total_low": non_preempt_high,
            "total_high": non_preemp_low_comp,
            "total_high_completion": non_preemp_high_comp
        }
    }

    with open(frame_comp_fix_result_file, "w") as f:
        f.writelines(json.dumps(result_dict))
    return


def generate_frame_completion(weighted_json, result_path):
    meta_res_map = generate_meta_res_map(weighted_json)

    event_list = {}

    with open(result_path, "r") as f:
        event_list = json.load(f)

    for event in event_list:
        if event["event_type"] == "LOW_COMP_FINISH" or event["event_type"] == "HIGH_COMP_FINISH":
            dnn_id = event["message_content"]["dnn_id"]
            host_id, task_id = hostname_to_index(dnn_id)
            meta_res_map[host_id][task_id]["complete"].append(True)

    frame_completion = 0
    average_task_completion = []

    total_low_frame_count = 0
    total_high_frame_count = 0
    total_low_completion_count = 0
    total_high_completion_count = 0
    for i in range(0, len(meta_res_map.keys())):
        for j in range(0, len(meta_res_map[i])):
            if meta_res_map[i][j]["type"] == "low":
                total_low_frame_count += 1

                if len(meta_res_map[i][j]["complete"]) != 1:
                    continue

                total_low_completion_count += 1

                if j + 1 < len(meta_res_map[i].keys()) and meta_res_map[i][j + 1]["type"] == "high":
                    total_high_frame_count += 1
                    
                    if len(meta_res_map[i][j + 1]["complete"]) == 0:
                        average_task_completion.append(0)
                    else:
                        average_task_completion.append(len(meta_res_map[i][j + 1]["complete"]) / meta_res_map[i][j + 1]["count"])

                    if len(meta_res_map[i][j+1]["complete"]) == meta_res_map[i][j + 1]["count"]:
                        frame_completion += 1

                    total_high_completion_count += len(meta_res_map[i][j+1]["complete"])
                else:
                    frame_completion += 1
    return frame_completion, sum(average_task_completion) / len(average_task_completion), total_low_frame_count, total_high_frame_count, total_low_completion_count, statistics.stdev(average_task_completion), total_high_completion_count


def generate_meta_res_map(weighted_json):
    meta_res_map = {}
    for j in range(0, 4):
        result_map = {}
        dnn_counter = 0
        for i in range(0, len(weighted_json)):
            if weighted_json[i][j] == -1:
                continue
            else:
                result_map[dnn_counter] = {"type": "low", "count": weighted_json[i][j], "complete": []}
                dnn_counter += 1

                if weighted_json[i][j] > 0:
                    result_map[dnn_counter] = {"type": "high", "count": weighted_json[i][j], "complete": []}
                    dnn_counter += 1
        meta_res_map[j] = result_map

    return meta_res_map


def hostname_to_index(dnn_id):
    split_list = dnn_id.split("_")
    hostname = split_list[0]
    host_id = int(hostname.split(".")[-1])

    task_id = int(split_list[1])
    return host_id - 2, task_id


if __name__ == "__main__":
    main()