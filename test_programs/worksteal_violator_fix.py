import json

centralised_preempt_path = "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/ExperimentLogs/weighted_4_worksteal_preempt_centralised.json"
centralised_nopreempt_path = "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/ExperimentLogs/weighted_4_worksteal_no_preempt_centralised.json"

decentralised_preempt_path = "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/ExperimentLogs/weighted_4_worksteal_preempt_decentralised.json"
decentralised_nopreempt_path = "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/ExperimentLogs/weighted_4_worksteal_no_preempt_decentralised.json"

centralised_events = ["HIGH_COMP_REQUEST", "HIGH_COMP_FINISH", "VIOLATED_DEADLINE", "VIOLATED_DEADLINE_REQUEST", "LOW_COMP_ALLOCATION_FAIL", "HIGH_COMP_ALLOCATION_SUCCESS"]

result_path = "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/ResultFolder/violation_correction.json"

def main():
    centralised_preemp = centralised_parser(centralised_preempt_path, True, False)
    centralised_no_preemp = centralised_parser(centralised_nopreempt_path, False, False)
    decentralised_preemp = centralised_parser(decentralised_preempt_path, True, True)
    decentralised_no_preemp = centralised_parser(decentralised_nopreempt_path, False, True)
    
    summary = {
        "centralised_preempt": centralised_preemp,
        "centralised_nopreempt": centralised_no_preemp,
        "decentralised_preempt": decentralised_preemp,
        "decentralised_nopreempt": decentralised_no_preemp
    }

    with open(result_path, "w") as f:
        f.writelines(json.dumps(summary))
    return

def centralised_parser(js_file_path: str, preempt: bool, decentralised: bool):
    loaded_json = []

    with open(js_file_path, "r") as f:
        loaded_json = json.load(f)


    events = [item for item in loaded_json if item["event_type"] in centralised_events]
    
    dnn_event_dict = {}

    for event in events:
        if event["event_type"] == "HIGH_COMP_REQUEST":
            for i in range(0, event["message_content"]["task_count"]):
                dnn_event_dict[f"{event['message_content']['dnn_id']}_{i}"] = {}

        elif event["event_type"] == "HIGH_COMP_FINISH" or event["event_type"] == "VIOLATED_DEADLINE" or event["event_type"] == "HIGH_COMP_ALLOCATION_SUCCESS":
            dnn = event["message_content"]["dnn"] if not decentralised else event["message_content"]
            if dnn["dnn_id"] not in dnn_event_dict.keys():
                dnn_event_dict[dnn["dnn_id"]] = {}
            dnn_event_dict[dnn["dnn_id"]][event["event_type"]] = event

        elif event["event_type"] == "VIOLATED_DEADLINE_REQUEST":
            dnn_event_dict[event["message_content"]["dnn_id"]][event["event_type"]] = event


    if preempt:
        low_comp_preempt_dict = {}

        for event in events:
            if event["event_type"] == "LOW_COMP_ALLOCATION_FAIL":
                dnn_id = event["message_content"]["dnn_id"]
                source_device = dnn_id.split("_")[0]

                preempted_task = ""

                for device in event["message_content"]["network"]["devices"]:
                    if source_device == device["host_name"]:
                        deadline = -1
                        for task in device["tasks"]:
                            if task["deadline"] > deadline:
                                preempted_task = task["dnn_id"]
                                deadline = task["deadline"]

                        dnn_event_dict[preempted_task]["PREEMPTED"] = event["message_content"]["dnn_id"]
                        break
                
                low_comp_preempt_dict[dnn_id] = {}
                low_comp_preempt_dict[dnn_id]["preempted_task"] = preempted_task

    new_dnn_dict = {ky:item for ky, item in dnn_event_dict.items() if "HIGH_COMP_FINISH" not in item.keys() and "HIGH_COMP_ALLOCATION_SUCCESS" in item.keys()}

    violations = {}
    preemptions = {}
    if preempt:
        violations = {ky: item for ky, item in new_dnn_dict.items() if "PREEMPTED" not in item.keys()}
        preemptions = {ky: item for ky, item in new_dnn_dict.items() if "PREEMPTED" in item.keys()}

    else:
        violations = new_dnn_dict
    
    if preempt:
        return {"violations": len(violations.keys()), "preemptions": len(preemptions.keys())}
    else:
        return {"violations": len(violations.keys())}

if __name__ == "__main__":
    main()