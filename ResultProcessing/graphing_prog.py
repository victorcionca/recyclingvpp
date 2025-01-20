import json
import sys
import numpy as np
import matplotlib.pyplot as plt
import math
from textwrap import wrap

wrap_value = 13

font_size = 20

plot_width = 12
plot_height = 8


def filter_string(input_str):
    name = filter_function(input_str)
    return "\n".join(wrap(name, wrap_value))


def filter_function(input_str):
    name = input_str.replace("_", " ").upper()
    name = name.replace("UNIFORM", "UNI.")
    name = name.replace("DECENTRALISED", "DECENT.")
    name = name.replace("CENTRALISED", "CENTR.")
    name = name.replace("WEIGHTED ", "W.")
    name = name.replace("SCHEDULER", "SCHED.")
    name = name.replace("WORKSTEAL", "W.STEAL")
    return name.title()


def read_data(names_and_paths):

    data_map = {}

    for name, file_path in names_and_paths.items():
        data_file = open(file_path, "r")
        data_json = json.loads(data_file.read())
        data_file.close()
        data_map[name] = data_json

    return data_map


def low_comp_graphing(data_map, graphs_dir, file_name):
    stack_labels = ['Completed (No preemption)', 'Completed (Preemption)']
    categories = [filter_string(name) for name in data_map.keys()]
    stack_1 = [((data_json["low_comp_success_count"] - data_json["low_comp_preempt_success_count"]) / data_json["total_low_comp_count"]) * 100 for data_json in data_map.values()]  # Values for the first stack in the first chart
    stack_2 = [(data_json["low_comp_preempt_success_count"] / data_json["total_low_comp_count"]) * 100 for data_json in data_map.values()] 

    x = np.arange(len(categories)) 

    fig, ax = plt.subplots(figsize=(plot_width, plot_height))  # Increase the figure size for better readability

    ax.bar(x, stack_1, width=0.3, label=stack_labels[0])
    ax.bar(x, stack_2, bottom=stack_1, width=0.3, label=stack_labels[1])

    ax.set_xlabel('High Priority Completion Rates by Mechanism')
    ax.set_ylabel('Task Count')
    plt.xticks(x, categories, rotation=45, ha="right")  # Rotate the x tick labels
    y_ticks = np.arange(0, 101, 10)
    plt.yticks(y_ticks)
    fig.legend()
    # Set tick label font sizes
    plt.tick_params(axis='both', which='major', labelsize=font_size)  # 'both' applies to x and y axis
    ax.yaxis.grid(True)
    plt.tight_layout()  # Adjust the layout to fit everything
    plt.savefig(f"{graphs_dir}/{file_name}_high_priority_low_comp_res.pdf")
    plt.close()
    return


def high_comp_graphing_completion(data_map, graphs_dir, file_name):
    # stack_labels = ['Completed', 'Failed (Due to Preemption)', 'Failed (Halted - Time Window violation)']  
    stack_labels = ['Completed']
    categories = [filter_string(name) for name in data_map.keys()]
    
    finished = [(data_item["high_comp_finish"] / data_item["total_high_comp_count"]) * 100 for data_item in data_map.values()]  
    # failed_preemption = [data_item["high_comp_prempt_fail"] for data_item in data_map.values()]  
    # processing_violation = [data_item["high_comp_violated"] for data_item in data_map.values()]  

    x = np.arange(len(categories))  

    fig, ax = plt.subplots(figsize=(plot_width, plot_height))  # Increase the figure size for better readability

    ax.bar(x, finished, width=0.3, label=stack_labels[0])

    # plt.bar(x, failed_preemption, bottom=finished, width=0.3, label=stack_labels[1])
    # plt.bar(x, processing_violation, bottom=np.add(finished, failed_preemption), width=0.3, label=stack_labels[2])

    # Set tick label font sizes
    plt.tick_params(axis='both', which='major', labelsize=font_size)  # 'both' applies to x and y axis
    ax.set_xlabel('Low Priority - High Comp Completion Rates')
    ax.set_ylabel('Task Count')
    plt.xticks(x, categories, rotation=45, ha="right")  # Rotate the x tick labels
    fig.legend()

    ax.yaxis.grid(True)

    plt.tight_layout()  # Adjust the layout to fit everything
    plt.savefig(f"{graphs_dir}/{file_name}_low_priority_high_comp_res.pdf")
    plt.close()
    return


def preemption_breakdown(data_mp, graph_dir, file_name):  
    stack_labels = ['1x2 Partition Config', '2x2 Partition Config']
    data_map = {name: data_item for name, data_item in data_mp.items() if "no_preempt" not in name}
    categories = []

    wrap_val = 20
    for data_name, data_item in data_map.items():
        categories.append(filter_string(data_name))

    stack_1 = []
    stack_2 = []

    for data_item in data_map.values():
        total_preemp_count = (data_item["high_comp_1x2_preemp"] + data_item["high_comp_2x2_preemp"])
        stack_1.append((data_item["high_comp_1x2_preemp"] / total_preemp_count) * 100 if data_item["high_comp_1x2_preemp"] != 0 else 0)
        stack_2.append((data_item["high_comp_2x2_preemp"] / total_preemp_count) * 100 if data_item["high_comp_2x2_preemp"] != 0 else 0)


    x = np.arange(len(categories))  

    fig, ax = plt.subplots(figsize=(plot_width, plot_height))  # Increase the figure size for better readability

    ax.bar(x, stack_1, width=0.3, label=stack_labels[0])
    ax.bar(x, stack_2, bottom=stack_1, width=0.3, label=stack_labels[1])

    ax.set_xlabel('Partition Config of Preempted Tasks')
    ax.set_ylabel('Tasks Preempted Percentage')
    plt.xticks(x, categories, rotation=45, ha="right")  # Rotate the x tick labels
    fig.legend()

    ax.yaxis.grid(True)

    # Set tick label font sizes
    plt.tick_params(axis='both', which='major', labelsize=font_size)  # 'both' applies to x and y axis
    plt.tight_layout()  # Adjust the layout to fit everything
    plt.savefig(f"{graphs_dir}/{file_name}_partition_config_preemption.pdf")
    plt.close()
    return


def average_high_comp_completion_per_request(data_map, graph_dir, file_name):
    categories = [filter_string(name) for name in data_map.keys()]
    
    finished = [data_item["average_high_comp_completed"] * 100 for data_item in data_map.values()]  
    errorbars = [data_item["stdev_high_comp_completed"] * 100 for data_item in data_map.values()]  
    x = np.arange(len(categories))  

     # Calculate upper and lower error bars
    upper_errorbars = [
        min(stdev, 100 - finish)
        for finish, stdev in zip(finished, errorbars)
    ]
    lower_errorbars = [
        min(stdev, finish)
        for finish, stdev in zip(finished, errorbars)
    ]

    fig, ax = plt.subplots(figsize=(plot_width, plot_height))  # Increase the figure size for better readability

    ax.bar(x, finished, width=0.3, yerr=[lower_errorbars, upper_errorbars], capsize=5)

    ax.set_xlabel('Percentage of Low Priority Tasks completed per Request')
    ax.set_ylabel('Low Priority Task Completion')
    plt.xticks(x, categories, rotation=45, ha="right")  # Rotate the x tick labels
    plt.yticks(range(0, 101, 5))
    ax.yaxis.grid(True)

    # Set tick label font sizes
    plt.tick_params(axis='both', which='major', labelsize=font_size)  # 'both' applies to x and y axis
    plt.tight_layout()  # Adjust the layout to fit everything
    plt.savefig(f"{graphs_dir}/{file_name}_average_high_comp_completion_per_request.pdf")
    plt.close()
    return


def frame_completion(data_map, graphs_dir, file_name):
    stack_labels = ["Complete", "Incomplete"]
    categories = [filter_string(name) for name in data_map.keys()]

    # Calculate frames completed and frames remaining
    frames_completed = [data_item["frames_completed"] for data_item in data_map.values()]
    frames_remaining = [data_item["frames_generated"] - data_item["frames_completed"] for data_item in data_map.values()]

    x = np.arange(len(categories))

    fig, ax = plt.subplots(figsize=(plot_width, plot_height))  # Increase the figure size for better readability

    # Plotting the bars with stacking
    ax.bar(x, frames_completed, width=0.3, label=stack_labels[0])
    ax.bar(x, frames_remaining, width=0.3, bottom=frames_completed, label=stack_labels[1])  # Stacked on top of frames completed

    ax.set_xlabel('Frame Completion by Mechanism')
    ax.set_ylabel('Number of Frames')

    # Set y ticks every 250 values
    max_value = 0

    for i in range(0, len(frames_completed)):
        if frames_completed[i] + frames_remaining[i] > max_value:
            max_value = frames_completed[i] + frames_remaining[i]
    num_ticks = int(max_value // 250) + (1 if max_value % 250 != 0 else 0)  # Ensure at least one tick
    y_ticks = np.linspace(0, max_value, num_ticks)

    # Customize y tick labels (optional)
    y_tick_labels = [f"{int(val):,}" for val in y_ticks]  # Use comma separators for readability

    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_tick_labels)

    # Add y grid lines
    ax.yaxis.grid(True)

    plt.xticks(x, categories, rotation=45, ha="right")  # Rotate the x tick labels

    ax.legend()  # Add a legend to distinguish between complete and remaining frames

    plt.tight_layout()  # Adjust the layout to fit everything

    # Set tick label font sizes
    plt.tick_params(axis='both', which='major', labelsize=font_size)  # 'both' applies to x and y axis
    plt.savefig(f"{graphs_dir}/{file_name}_frame_completion.pdf")
    plt.close()
    return


def offloaded_completed(data_map, graphs_dir, file_name):
    # stack_labels = ["Complete", "Incomplete"]  
    categories = [filter_string(name) for name in data_map.keys()]
    
    finished = [(data_item["completed_offloaded_tasks"] / data_item["offloaded_tasks"] ) * 100 for data_item in data_map.values()]  

    # offloaded_completed = [data_item["completed_offloaded_tasks"] for data_item in data_map.values()]
    # offloaded_remaining = [data_item["offloaded_tasks"] - data_item["completed_offloaded_tasks"] for data_item in data_map.values()]

    x = np.arange(len(categories))  

    fig, ax = plt.subplots(figsize=(plot_width, plot_height))  # Increase the figure size for better readability

    # Plotting the bars with stacking
    ax.bar(x, finished, width=0.3)
    # ax.bar(x, offloaded_remaining, width=0.3, bottom=offloaded_completed, label=stack_labels[1])  # Stacked on top of frames completed

        # Set y ticks every 250 values
    max_value = 0

    # for i in range(0, len(offloaded_completed)):
    #     if offloaded_completed[i] + offloaded_remaining[i] > max_value:
    #         max_value = offloaded_completed[i] + offloaded_remaining[i]
    # num_ticks = int(max_value // 250) + (1 if max_value % 250 != 0 else 0)  # Ensure at least one tick
    y_ticks = np.linspace(0, 100, 10)

    # Customize y tick labels (optional)
    y_tick_labels = [f"{int(val):,}" for val in y_ticks]  # Use comma separators for readability

    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_tick_labels)

    ax.set_xlabel('Offloaded Low Priority - High Complexity Task Completion by Mechanism')
    ax.set_ylabel('Offloaded Tasks')
    plt.xticks(x, categories, rotation=45, ha="right")  # Rotate the x tick labels
    ax.yaxis.grid(True)
    # ax.legend()
    # Set tick label font sizes
    plt.tick_params(axis='both', which='major', labelsize=font_size)  # 'both' applies to x and y axis
    plt.tight_layout()  # Adjust the layout to fit everything
    plt.savefig(f"{graphs_dir}/{file_name}_offloaded_completion.pdf")
    plt.close()
    return


def local_completion(data_map, graphs_dir, file_name):
    stack_labels = ["Complete"]  
    categories = [filter_string(name) for name in data_map.keys()]
    
    finished = [(data_item["completed_offloaded_tasks"] / data_item["offloaded_tasks"] ) * 100 for data_item in data_map.values()]  
    
    x = np.arange(len(categories))  

    fig, ax = plt.subplots(figsize=(plot_width, plot_height))  # Increase the figure size for better readability

    ax.bar(x, finished, width=0.3, label=stack_labels[0])

    ax.set_xlabel('Offloaded Low Priority - High Complexity Task Completion by Mechanism')
    ax.set_ylabel('Task Complete %')
    plt.xticks(x, categories, rotation=45, ha="right")  # Rotate the x tick labels
    plt.yticks(range(0, 100, 5))
    ax.yaxis.grid(True)
    # Set tick label font sizes
    plt.tick_params(axis='both', which='major', labelsize=font_size)  # 'both' applies to x and y axis

    plt.tight_layout()  # Adjust the layout to fit everything
    plt.savefig(f"{graphs_dir}/{file_name}_offloaded_completion.pdf")
    plt.close()
    return

def low_comp_proc_time(data_map, graphs_dir, file_name):
    categories = []

    no_preempt = []
    no_preempt_err = []
    for name, data_item in data_map.items():
        if "scheduler" not in name:
            continue
        
        categories.append("\n".join(wrap(f"{filter_function(name)} No Preemp", wrap_value)))
        categories.append("\n".join(wrap(f"{filter_function(name)} Preemp", wrap_value)))

        no_preempt.append(data_item["avg_low_comp_allocation_times_no_preemp"])
        no_preempt.append(data_item["avg_low_comp_allocation_times_preemp"])

        no_preempt_err.append(data_item["stdev_low_comp_allocation_times_no_preemp"])
        no_preempt_err.append(data_item["stdev_low_comp_allocation_times_preemp"])

    f, ax = plt.subplots(figsize=(plot_width, plot_height))

    x = np.arange(len(categories)) 

    ax.bar(x, no_preempt, width=0.3, bottom=0, yerr=no_preempt_err, capsize=3)
    ax.set_ylim(ymin=-1)
    ax.set_ylim(ymax=max(no_preempt))

    ax.set_xlabel('Average System Allocation Time per High Priority Task')
    ax.set_ylabel('Request Allocation Times (ms)')
    plt.xticks(x, categories, rotation=45, ha="right")  # Rotate the x tick labels
    ax.yaxis.grid(True)
    # Set tick label font sizes
    plt.tick_params(axis='both', which='major', labelsize=font_size)  # 'both' applies to x and y axis

    plt.tight_layout()  # Adjust the layout to fit everything
    b = list(range(0, 651, 50))

    plt.yticks(b)
    plt.savefig(f"{graphs_dir}/{file_name}_low_comp_system_time.pdf")
    plt.close()
    return


def high_comp_proc_time(data_map, graphs_dir, file_name):
    categories = []

    no_preempt = []
    no_preempt_err = []

    for name, data_item in  data_map.items():
        if "scheduler" not in name:
            continue

        categories.append("\n".join(wrap(f"{filter_function(name)} Initial", wrap_value)))
        categories.append("\n".join(wrap(f"{filter_function(name)} Reallo", wrap_value)))


        no_preempt.append(data_item["avg_high_comp_allocation_times_initial"])
        no_preempt.append(data_item["avg_high_comp_allocation_times_reallo"])
        no_preempt_err.append(data_item["stdev_high_comp_allocation_times_initial"])
        no_preempt_err.append(data_item["stdev_high_comp_allocation_times_reallo"])

    f, ax = plt.subplots(figsize=(plot_width, plot_height))

    x = np.arange(len(categories))

    ax.bar(x, no_preempt, width=0.3, bottom=0, yerr=no_preempt_err, capsize=3)
    ax.set_ylim(ymin=-1, ymax=max(no_preempt))

    ax.set_xlabel('Average System Allocation Time per Low Priority Task')
    ax.set_ylabel('Request Allocation Times (ms)')
    plt.xticks(x, categories, rotation=45, ha="right")  # Rotate the x tick labels
    ax.yaxis.grid(True)
    # Set tick label font sizes
    plt.tick_params(axis='both', which='major', labelsize=font_size)  # 'both' applies to x and y axis

    plt.tight_layout()  # Adjust the layout to fit everything
    b = list(range(0, 701, 50))
    plt.yticks(b)
    plt.savefig(f"{graphs_dir}/{file_name}_high_comp_system_time.pdf")
    
    plt.close()
    return


def main(names_and_paths, graphs_dir):
    data_map = read_data(names_and_paths)
    netload_keys = ["weighted_1_scheduler_preempt", "weighted_2_scheduler_preempt", "weighted_3_scheduler_preempt", "weighted_4_scheduler_preempt"]
    preempt_vs_no_preempt_keys = ["uniform_scheduler_preempt",  "uniform_scheduler_no_preempt", "weighted_4_scheduler_no_preempt", "weighted_4_scheduler_preempt", "centralised_worksteal_preempt", "centralised_worksteal_no_preempt", "decentralised_worksteal_preempt", "decentralised_worksteal_no_preempt"]
    
    netload_map = {name: data for name, data in data_map.items() if name in netload_keys}
    preempt_vs_no_preempt_map = {name: data for name, data in data_map.items() if name in preempt_vs_no_preempt_keys}
    
    generate_graphs(netload_map, graphs_dir, "task_load_variance")
    generate_graphs(preempt_vs_no_preempt_map, graphs_dir, "preempt_vs_non_preempt")
    return


def generate_graphs(data_map, graphs_dir, file_name):
    low_comp_graphing({name: data_json["low_comp_results"] for name, data_json in data_map.items()}, graphs_dir, file_name)
    high_comp_graphing_completion({name: data_json["high_comp_results"] for name, data_json in data_map.items()}, graphs_dir, file_name)
    frame_completion({name: data_json["general_stats"] for name, data_json in data_map.items()}, graphs_dir, file_name)
    preemption_breakdown({name: data_json["high_comp_results"] for name, data_json in data_map.items()}, graphs_dir, file_name)
    average_high_comp_completion_per_request({name: data_json["general_stats"] for name, data_json in data_map.items()}, graphs_dir, file_name)
    offloaded_completed({name: data_json["general_stats"] for name, data_json in data_map.items()}, graphs_dir, file_name)
    low_comp_proc_time({name: data_json["low_comp_results"] for name, data_json in data_map.items()}, graphs_dir, file_name)
    high_comp_proc_time({name: data_json["high_comp_results"] for name, data_json in data_map.items()}, graphs_dir, file_name)
    return

if __name__ == "__main__":
    # no_preempt_file_path = sys.argv[1]
    # preempt_file_path = sys.argv[2]

    names_and_paths = {
        "uniform_scheduler_no_preempt": "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/ResultFolder/no_preemption_summary.json",
        "uniform_scheduler_preempt": "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/ResultFolder/preemption_summary.json",
        "weighted_1_scheduler_preempt": "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/ResultFolder/weighted_1_scheduler_preempt_summary.json",
        "weighted_2_scheduler_preempt": "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/ResultFolder/weighted_2_scheduler_preempt_summary.json",
        "weighted_3_scheduler_preempt": "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/ResultFolder/weighted_3_scheduler_preempt_summary.json",
        "weighted_4_scheduler_preempt": "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/ResultFolder/weighted_4_scheduler_preempt_summary.json",
        "weighted_4_scheduler_no_preempt": "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/ResultFolder/weighted_4_scheduler_no_preempt_summary.json",
        "centralised_worksteal_preempt": "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/ResultFolder/weighted_4_worksteal_preempt_centralised_summary.json",
        "centralised_worksteal_no_preempt": "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/ResultFolder/weighted_4_worksteal_no_preempt_centralised_summary.json",
        "decentralised_worksteal_preempt": "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/ResultFolder/weighted_4_worksteal_preempt_decentralised_summary.json",
        "decentralised_worksteal_no_preempt": "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/ResultFolder/weighted_4_worksteal_no_preempt_decentralised_summary.json",
        "ema": "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/ResultFolder/weighted_4_slice_scheduler_preempt_ema_summary.json",
        "static_bw_slice": "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/ResultFolder/weighted_4_slice_scheduler_preempt_old_bw_summary.json",
        "signal_variance": "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/ResultFolder/variance_weighted_4_slice_scheduler_preempt_ema_summary.json"
        
    }

    # graphs_dir = sys.argv[1]
    graphs_dir = "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultProcessing/graphs"
    main(names_and_paths, graphs_dir)