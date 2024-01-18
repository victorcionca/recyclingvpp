from typing import List

def trace_parser(trace_list: List, device_task: int) -> List:
    return [list_item[device_task] for list_item in trace_list]