import json
from os import path


frame_rate_seconds = 18.665072
task_cutoff_minutes = 30
trace_file_dir = "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/trace_files"
trace_file_path = f"{trace_file_dir}/weighted_trace_file_4.json"
trace_save_path = f"{trace_file_dir}/weighted_4_slice_trace_file.json"


def main():
    trace_file = open(trace_file_path, "r")
    trace_data = json.load(trace_file)
    trace_file.close()

    cutoff = int((task_cutoff_minutes * 60) / frame_rate_seconds)

    trace_slice = trace_data[0: cutoff]

    res_file = open(trace_save_path, "w")

    res_file.writelines(json.dumps(trace_slice))
    res_file.close()
    
    return


if __name__ == "__main__":
    main()
