import os
import json

trace_file_dir = "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/trace_files"

def main():
    file_names = os.listdir(trace_file_dir)

    trace_files = {}

    for fname in file_names:
        with open(f"{trace_file_dir}/{fname}", "r") as f:
            trace_files[fname.split(".")[0]] = json.load(f)

    trace_file_counters = {}

    for trace_file_name, trace_list in trace_files.items():
        low_priority_counter = 0
        high_priority_counter = 0
        for frame in trace_list:
            for task_count in frame:
                if task_count > -1:
                    low_priority_counter += task_count
                    high_priority_counter += 1

        trace_file_counters[trace_file_name] = {"low_priority_count": low_priority_counter, "total_len": len(trace_list), "high_priority_count": high_priority_counter}
    
    with open("/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/trace_file_stats.json", "w") as f:
        f.writelines(json.dumps(trace_file_counters))
    return


if __name__ == "__main__":
    main()