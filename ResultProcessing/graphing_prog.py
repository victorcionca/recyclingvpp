import json
import sys
import numpy as np
import matplotlib.pyplot as plt


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
    plt.xticks(x + 0.15, categories)
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
    plt.xticks(x + 0.15, categories)
    plt.legend()

    plt.savefig(f"{graphs_dir}/low_priority_high_comp_res.pdf")
    plt.close()
    return


def main(no_preempt_file_path, preempt_file_path, graphs_dir):
    no_preempt_json, preempt_json = read_data(no_preempt_file_path, preempt_file_path)
    
    low_comp_graphing(no_preempt_json["low_comp_results"], preempt_json["low_comp_results"], graphs_dir)
    high_comp_graphing_completion(no_preempt_json["high_comp_results"], preempt_json["high_comp_results"], graphs_dir)
    return

if __name__ == "__main__":
    no_preempt_file_path = sys.argv[1]
    preempt_file_path = sys.argv[2]
    graphs_dir = sys.argv[3]
    main(no_preempt_file_path, preempt_file_path, graphs_dir)