import json
import sys
import numpy as np
import matplotlib.pyplot as plt
import math


def read_data(no_preempt_file_path, preempt_file_path):
    no_preempt_file = open(no_preempt_file_path, "r")
    no_preempt_json = json.loads(no_preempt_file.read())
    no_preempt_file.close()

    preempt_file = open(preempt_file_path, "r")
    preempt_json = json.loads(preempt_file.read())
    preempt_file.close()

    return no_preempt_json, preempt_json


def low_comp_graphing(no_preempt_json, preempt_json, graphs_dir):
    stack_labels = ['Completed (No preemption)', 'Completed (Preemption)', 'Failed']
    categories = ["No Preemption Mechanism", "Preemption Mechanism"]
    stack_1 = [no_preempt_json["low_comp_success_count"] - no_preempt_json["low_comp_preempt_success_count"], preempt_json["low_comp_success_count"] - preempt_json["low_comp_preempt_success_count"]]  # Values for the first stack in the first chart
    stack_2 = [no_preempt_json["low_comp_preempt_success_count"], preempt_json["low_comp_preempt_success_count"]] 
    stack_3 = [no_preempt_json["low_comp_fail_count"], preempt_json["low_comp_fail_count"]] 

    x = np.arange(len(categories)) 

    plt.bar(x, stack_1, width=0.3, label=stack_labels[0])
    plt.bar(x, stack_2, bottom=stack_1, width=0.3, label=stack_labels[1])
    plt.bar(x, stack_3, bottom=np.add(stack_1, stack_2), width=0.3, label=stack_labels[2])

    plt.xlabel('High Priority - Low Comp Completion Rates by Mechanism')
    plt.ylabel('Task Count')
    plt.xticks(x, categories)
    plt.legend()

    plt.savefig(f"{graphs_dir}/high_priority_low_comp_res.pdf")
    plt.close()
    return


def high_comp_graphing_completion(no_preempt_json, preempt_json, graphs_dir):
    stack_labels = ['Completed', 'Failed (No initial resources)', 'Failed (Due to Preemption)', 'Failed (Halted - Time Window violation)']  
    categories = ["No Preemption Mechanism", "Preemption Mechanism"]
    
    finished = [no_preempt_json["high_comp_finish"], preempt_json["high_comp_finish"]]  
    failed = [no_preempt_json["high_comp_fail"], preempt_json["high_comp_fail"]]
    failed_preemption = [no_preempt_json["high_comp_prempt_fail"], preempt_json["high_comp_prempt_fail"]]  
    processing_violation = [no_preempt_json["high_comp_violated"], preempt_json["high_comp_violated"]]  

    x = np.arange(len(categories))  

    plt.bar(x, finished, width=0.3, label=stack_labels[0])
    plt.bar(x, failed, bottom=finished, width=0.3, label=stack_labels[1])
    plt.bar(x, failed_preemption, bottom=np.add(finished, failed), width=0.3, label=stack_labels[2])
    plt.bar(x, processing_violation, bottom=np.add(np.add(finished, failed), failed_preemption), width=0.3, label=stack_labels[3])

    plt.xlabel('Low Priority - High Comp Completion Rates by Mechanism')
    plt.ylabel('Task Count')
    plt.xticks(x, categories)
    plt.legend()

    plt.savefig(f"{graphs_dir}/low_priority_high_comp_res.pdf")
    plt.close()
    return


def preemption_breakdown(preempt_state, graph_dir):  
    categories = ["1x2 Tasks", "2x2 Tasks"]
    
    finished = [preempt_state["high_comp_1x2_preemp"], preempt_state["high_comp_2x2_preemp"]]  

    x = np.arange(len(categories))  

    plt.bar(x, finished, width=0.3)

    plt.xlabel('Partition Config of Preempted Tasks')
    plt.ylabel('Tasks Preempted')
    plt.xticks(x, categories)
    plt.yticks(range(0, 801, 50))

    plt.savefig(f"{graphs_dir}/partition_config_preemption.pdf")
    plt.close()
    return


def average_high_comp_completion_per_request(preempt_state, no_preempt_state, graph_dir):
    categories = ["No Preempt", "Preempt"]
    
    finished = [no_preempt_state["average_high_comp_completed"] * 100, preempt_state["average_high_comp_completed"] * 100]  
    errorbars = [no_preempt_state["stdev_high_comp_completed"] * 100, preempt_state["stdev_high_comp_completed"] * 100]  
    x = np.arange(len(categories))  

    plt.bar(x, finished, width=0.3, yerr=errorbars, capsize=5)

    plt.xlabel('Percentage of High Comp Tasks completed per Request')
    plt.ylabel('High Comp Task Completion')
    plt.xticks(x, categories)
    plt.yticks(range(0, 101, 5))

    plt.savefig(f"{graphs_dir}/average_high_comp_completion_per_request.pdf")
    plt.close()
    return


def frame_completion(no_preempt_json, preempt_json, graphs_dir):
    stack_labels = ["Complete"]  
    categories = ["No Preemption Mechanism", "Preemption Mechanism"]
    
    finished = [(no_preempt_json["frames_completed"] / no_preempt_json["frames_generated"]) * 100, (preempt_json["frames_completed"] / preempt_json["frames_generated"]) * 100]  

    x = np.arange(len(categories))  

    plt.bar(x, finished, width=0.3, label=stack_labels[0])

    plt.xlabel('Frame Completion Rate over 4320 Frames by Mechanism')
    plt.ylabel('Frame Complete %')
    plt.xticks(x, categories)
    plt.yticks(range(0, 61, 5))

    plt.savefig(f"{graphs_dir}/frame_completion.pdf")
    plt.close()
    return


def offloaded_completed(no_preempt_state, preempt_state, graphs_dir):
    stack_labels = ["Complete"]  
    categories = ["No Preemption Mechanism", "Preemption Mechanism"]
    
    finished = [(no_preempt_state["completed_offloaded_tasks"] / no_preempt_state["offloaded_tasks"] ) * 100, (preempt_state["completed_offloaded_tasks"] / preempt_state["offloaded_tasks"] ) * 100]  

    x = np.arange(len(categories))  

    plt.bar(x, finished, width=0.3, label=stack_labels[0])

    plt.xlabel('Offloaded Low Priority - High Complexity Task Completion by Mechanism')
    plt.ylabel('Task Complete %')
    plt.xticks(x, categories)
    plt.yticks(range(0, 100, 5))

    plt.savefig(f"{graphs_dir}/offloaded_completion.pdf")
    plt.close()
    return

def low_comp_proc_time(no_preempt_json, preempt_json, graphs_dir):
    categories = ['NP - No Preempt', '', 'PM - No Preempt', 'PM - Preempt']

    no_preempt = [no_preempt_json["avg_low_comp_allocation_times_no_preemp"], no_preempt_json["avg_low_comp_allocation_times_preemp"], preempt_json["avg_low_comp_allocation_times_no_preemp"], preempt_json["avg_low_comp_allocation_times_preemp"]]
    no_preempt_err = [no_preempt_json["stdev_low_comp_allocation_times_no_preemp"], no_preempt_json["stdev_low_comp_allocation_times_preemp"], preempt_json["stdev_low_comp_allocation_times_no_preemp"], preempt_json["stdev_low_comp_allocation_times_preemp"]]

    f, ax = plt.subplots(1)

    x = np.arange(len(categories)) 

    ax.bar(x, no_preempt, width=0.3, bottom=0, yerr=no_preempt_err, capsize=3)
    ax.set_ylim(ymin=-1)

    plt.xlabel('Average System Allocation Time per High Priority - Low Complexity Request')
    plt.ylabel('Request Allocation Times (ms)')
    plt.xticks(x, categories)

    plt.savefig(f"{graphs_dir}/low_comp_system_time.pdf")
    b = list(range(0, 651, 50))
    plt.yticks(b)
    plt.close()
    return


def high_comp_proc_time(no_preempt_json, preempt_json, graphs_dir):
    categories = ['NP - No Reallo', '', 'PM - No Reallo', 'PM - Reallo']

    no_preempt = [no_preempt_json["avg_high_comp_allocation_times_initial"], no_preempt_json["avg_high_comp_allocation_times_reallo"], preempt_json["avg_high_comp_allocation_times_initial"], preempt_json["avg_high_comp_allocation_times_reallo"]]
    no_preempt_err = [no_preempt_json["stdev_high_comp_allocation_times_initial"], no_preempt_json["stdev_high_comp_allocation_times_reallo"], preempt_json["stdev_high_comp_allocation_times_initial"], preempt_json["stdev_high_comp_allocation_times_reallo"]]

    f, ax = plt.subplots(1)

    x = np.arange(len(categories)) 

    ax.bar(x, no_preempt, width=0.3, bottom=0, yerr=no_preempt_err, capsize=3)
    ax.set_ylim(ymin=-1)

    plt.xlabel('Average System Allocation Time per Low Priority - High Complexity Request')
    plt.ylabel('Request Allocation Times (ms)')
    plt.xticks(x, categories)

    plt.savefig(f"{graphs_dir}/high_comp_system_time.pdf")
    b = list(range(0, 701, 50))
    plt.yticks(b)
    plt.close()
    return


def main(no_preempt_file_path, preempt_file_path, graphs_dir):
    no_preempt_json, preempt_json = read_data(no_preempt_file_path, preempt_file_path)
    
    low_comp_graphing(no_preempt_json["low_comp_results"], preempt_json["low_comp_results"], graphs_dir)
    high_comp_graphing_completion(no_preempt_json["high_comp_results"], preempt_json["high_comp_results"], graphs_dir)
    frame_completion(no_preempt_json["general_stats"], preempt_json["general_stats"], graphs_dir)
    preemption_breakdown(preempt_json["high_comp_results"], graphs_dir)
    average_high_comp_completion_per_request(no_preempt_json["general_stats"], preempt_json["general_stats"], graphs_dir)
    offloaded_completed(no_preempt_json["general_stats"], preempt_json["general_stats"], graphs_dir)
    low_comp_proc_time(no_preempt_json["low_comp_results"], preempt_json["low_comp_results"], graphs_dir)
    high_comp_proc_time(no_preempt_json["high_comp_results"], preempt_json["high_comp_results"], graphs_dir)
    return

if __name__ == "__main__":
    no_preempt_file_path = sys.argv[1]
    preempt_file_path = sys.argv[2]
    graphs_dir = sys.argv[3]
    main(no_preempt_file_path, preempt_file_path, graphs_dir)