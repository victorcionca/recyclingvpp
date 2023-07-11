import sys
import json

valid_event_items = [
    "LOW_COMP_ALLOCATION_SUCCESS",
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
                    low_comp_last_state_dict[dnn_id] = []
                low_comp_last_state_dict[dnn_id].append(event["event_type"])
            else:
                if dnn_id not in high_comp_last_state_dict:
                    high_comp_last_state_dict[dnn_id] = []
                high_comp_last_state_dict[dnn_id].append(event["event_type"])
    return low_comp_last_state_dict, high_comp_last_state_dict


def main(file_name, result_name):
    low_comp_last_state_dict, high_comp_last_state_dict = generate_event_array(file_name)


    total_low_comp_count = len(low_comp_last_state_dict.keys())
    low_comp_success_count = 0
    low_comp_preempt_success_count = 0
    low_comp_fail_count = 0


    for dnn_result in low_comp_last_state_dict.values():
        if "LOW_COMP_FINISH" in dnn_result:
            low_comp_success_count = low_comp_success_count + 1
            if "LOW_COMP_PREMPT_ALLOCATION_SUCCESS" in dnn_result:
                low_comp_preempt_success_count = low_comp_preempt_success_count + 1
        if "LOW_COMP_ALLOCATION_FAIL" in dnn_result and "LOW_COMP_FINISH" not in dnn_result:
            low_comp_fail_count = low_comp_fail_count + 1
    
    total_high_comp_count = len(high_comp_last_state_dict.keys())
    high_comp_success_count = 0
    high_comp_fail = 0
    high_comp_prempt_fail = 0
    high_comp_prempt_success = 0
    high_comp_finish = 0
    high_comp_violated = 0

    for dnn_result in high_comp_last_state_dict.values():
        if "HIGH_COMP_FINISH" in dnn_result:
            high_comp_finish = high_comp_finish + 1
        if 'HIGH_COMP_ALLOCATION_SUCCESS' in dnn_result:
            high_comp_success_count = high_comp_success_count + 1
        if 'VIOLATED_DEADLINE' in dnn_result:
            high_comp_violated += 1
        if 'HIGH_COMP_ALLOCATION_FAIL' in dnn_result:
            high_comp_fail += 1
        if "HIGH_COMP_REALLOCATION_SUCCESS" in dnn_result:
            high_comp_prempt_success += 1
        if "HIGH_COMP_REALLOCATION_FAIL" in dnn_result: 
            high_comp_prempt_fail += 1
    
    result_dictionary = {
        "low_comp_results": {
            "total_low_comp_count": total_low_comp_count,
            "low_comp_success_count": low_comp_success_count,
            "low_comp_preempt_success_count": low_comp_preempt_success_count,
            "low_comp_fail_count": low_comp_fail_count,
        },
        "high_comp_results": {
            "total_high_comp_count": total_high_comp_count,
            "high_comp_success_count": high_comp_success_count,
            "high_comp_fail": high_comp_fail,
            "high_comp_prempt_fail": high_comp_prempt_fail,
            "high_comp_prempt_success": high_comp_prempt_success,
            "high_comp_finish": high_comp_finish,
            "high_comp_violated": high_comp_violated
        }
    }

    output_file = open(result_name, "w")
    output_file.write(json.dumps(result_dictionary))
    output_file.close()
    return


if __name__ == "__main__":
    file_name = sys.argv[1]
    result_name = sys.argv[2]


    main(file_name, result_name)
