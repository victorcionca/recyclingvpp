from enum import Enum, auto
import json
import pickle

class TaskType(Enum):
    LOW_COMP = auto()
    HIGH_COMP = auto()

class TaskCoreConf(Enum):
    CORE2X2 = auto()
    CORE2X1 = auto()

class EventType(Enum):
    ALLOC_SUCCESS = auto()
    ALLOC_FAIL = auto()
    PREEMPT_SUCCESS = auto()
    PREEMPT_FAIL = auto()
    REALLOC_SUCCESS = auto()
    REALLOC_FAIL = auto()
    FINISH = auto()
    VIOLATE = auto()

class Task():

    def __init__(self, ttype, dnn_id, source, time, deadline):
        self.type = ttype
        self.dnn_id = dnn_id
        self.received_at = time
        self.deadline = deadline
        self.src = source
        self.proc_host = None   # Where it's processed, can be != src
        self.core_conf = None
        self.events = []

    def has_event(self, etype):
        for e in self.events:
            if e.etype == etype:
                return True
        return False

    def is_finished(self):
        for e in self.events:
            if e.etype == EventType.FINISH: return True
        return False

    def is_local(self):
        return self.src == self.proc_host

class Event():
    def __init__(self, etype, time, details):
        self.etype = etype
        self.time = time
        self.details = details

class Frame():

    def __init__(self):
        self.low_comp = None
        self.high_comp = []


def parse_LOW_COMP_REQUEST(msg_content, time, state,
                        workstealer=False,
                        decentralised=False):
    """
    Create a new low comp task and frame, append to state of source
    """
    src_host = msg_content['source_host']
    task = Task(TaskType.LOW_COMP,
                msg_content['dnn_id'],
                src_host, time, msg_content['deadline'])
    frame = Frame()
    frame.low_comp = task
    if src_host not in state:
        state[src_host] = []
    state[src_host].append(frame)

def parse_LOW_COMP_ALLOCATION_SUCCESS(msg_content, time, state,
                        workstealer=False,
                        decentralised=False):
    """
    Update the state and timing details of the low comp request
    """
    if workstealer:
        if decentralised:
            dnn_details = msg_content
        else:
            dnn_details = msg_content['dnn']
    else:
        dnn_details = msg_content['dnn_details']
    dnn_id = dnn_details['dnn_id']
    src_host = dnn_details['source_host']
    # Find the task in the state of the src host
    # Only need to search if we can have interleaved frames
    task = None
    if decentralised:
        # In decentralised we are not notified of the request, so
        # this is where we register the task
        task = Task(TaskType.LOW_COMP,
                    dnn_id,
                    src_host, time, msg_content['finish_time'])
        # We register a new task
        frame = Frame()
        frame.low_comp = task
        if src_host not in state:
            state[src_host] = []
        state[src_host].append(frame)
    else:
        for frame in reversed(state[src_host]):
            if frame.low_comp.dnn_id == dnn_id:
                task = frame.low_comp
                break
    if task == None:
        print(f"Error on LOW_COMP_ALLOCATION_SUCCESS {dnn_id} {time}")
        return
    if decentralised:
        ev_keys = ['start_time', 'finish_time', 'invoke_preemption']
    else:
        ev_keys = ['estimated_finish', 'estimated_start']
    ev_details = {k:dnn_details[k] for k in ev_keys}
    task.events.append(Event(EventType.ALLOC_SUCCESS,
                            time, ev_details))

def parse_LOW_COMP_ALLOCATION_FAIL(msg_content, time, state,
                                workstealer=False,
                                decentralised=False):
    """
    Update the state and timing details of the low comp request
    """
    dnn_id = msg_content['dnn_id']
    host_key = "source_device"
    if decentralised:
        host_key = "source_host"
    src_host = msg_content[host_key]
    # Find the task in the state of the src host
    # Only need to search if we can have interleaved frames
    task = None

    if src_host not in state:
        state[src_host] = []
    
    if decentralised:
        if src_host not in state.keys():
            state[src_host] = []
        # In decentralised we are not notified of the request, so
        # this is where we register the task
        task = Task(TaskType.LOW_COMP,
                    dnn_id,
                    src_host, time, -1)
        # We register a new task
        frame = Frame()
        frame.low_comp = task
        if src_host not in state:
            state[src_host] = []
        state[src_host].append(frame)
    
    else:
        for frame in reversed(state[src_host]):
            if frame.low_comp.dnn_id == dnn_id:
                task = frame.low_comp
                break
        if task == None:
            print(f"Error on LOW_COMP_ALLOCATION_FAIL {dnn_id} {time}")
            return
    task.events.append(Event(EventType.ALLOC_FAIL, time, None))

def parse_LOW_COMP_PREMPT_ALLOCATION_SUCCESS(msg_content, time, state,
                                        workstealer=False,
                                        decentralised=False):
    """
    Update the state and timing details of the low comp request
    """
    if workstealer:
        dnn_details = msg_content['dnn']
    else:
        dnn_details = msg_content['dnn_details']
    dnn_id = dnn_details['dnn_id']
    src_host = dnn_details['source_host']
    # Find the task in the state of the src host
    # Only need to search if we can have interleaved frames
    task = None
    for frame in reversed(state[src_host]):
        if frame.low_comp.dnn_id == dnn_id:
            task = frame.low_comp
            break
    if task == None:
        print(f"Error on LOW_COMP_PREMPT_ALLOC_SUCCESS {dnn_id} {time}")
        return
    ev_keys = ['estimated_finish', 'estimated_start']
    ev_details = {k:dnn_details[k] for k in ev_keys}
    task.events.append(Event(EventType.PREEMPT_SUCCESS,
                            time, ev_details))

def parse_LOW_COMP_FINISH(msg_content, time, state,
                         workstealer=False,
                         decentralised=False):
    """
    Update the state and timing details of the low comp request
    """
    if workstealer:
        if decentralised:
            dnn_details = msg_content
        else:
            dnn_details = msg_content['dnn']
    else:
        dnn_details = msg_content['dnn_details']
    dnn_id = dnn_details['dnn_id']
    if workstealer:
        src_host = dnn_id.split('_')[0]
    else:
        src_host = dnn_details['source_host']
    # Find the task in the state of the src host
    # Only need to search if we can have interleaved frames
    task = None
    for frame in reversed(state[src_host]):
        if frame.low_comp.dnn_id == dnn_id:
            task = frame.low_comp
            break
    if task == None:
        print(f"Error on LOW_COMP_FINISH {dnn_id} {time}")
        return
    if decentralised:
        ev_keys = ['finish_time']
    else:
        ev_keys = ['actual_finish']
    ev_details = {k:dnn_details[k] for k in ev_keys}
    task.events.append(Event(EventType.FINISH, time, ev_details))

def parse_HIGH_COMP_REQUEST(msg_content, time, state,
                            workstealer=False,
                            decentralised=False):
    """
    Create a set of high comp requests
    """
    dnn_id = msg_content['dnn_id']
    src_host = msg_content['source_host']
    # These will be inserted into the last frame of this device
    frame = state[src_host][-1]
    for task_id in range(msg_content['task_count']):
        task = Task(TaskType.HIGH_COMP,
                    f"{dnn_id}_{task_id}",
                    src_host,
                    time,
                    msg_content['deadline'])
        frame.high_comp.append(task)

def parse_HIGH_COMP_ALLOCATION_SUCCESS(msg_content, time, state,
                                    workstealer=False,
                                    decentralised=False):
    """
    Update allocation for high comp task
    """
    if decentralised:
        dnn_details = msg_content
    else:
        dnn_details = msg_content['dnn']
    dnn_id = dnn_details['dnn_id']
    src_host = dnn_details['source_host']
    # Find the task from the list of frames of this host
    task = None
    if decentralised:
        # In decentralised we don't have a record of the task yet
        # Will store this with the latest frame of the host
        frame = state[src_host][-1]
        if frame is None:
            print(f"Error on HIGH_COMP_ALLOCATION_SUCCESS {dnn_id} {time}")
            return
        # This is the first notice so we generate a new task and add
        task = Task(TaskType.HIGH_COMP,
                    f"{dnn_id}",
                    src_host,
                    time,
                    msg_content['deadline'])
        frame.high_comp.append(task)
    else:
        for frame in reversed(state[src_host]):
            for hctask in frame.high_comp:
                if hctask.dnn_id == dnn_id:
                    task = hctask
                    break
            if task is not None: break
    if task == None:
        print(f"Error on HIGH_COMP_ALLOCATION_SUCCESS {dnn_id} {time}")
        return
    # Record the core configuration
    if dnn_details['N'] == 2:
        task.core_conf = TaskCoreConf.CORE2X2
    if dnn_details['N'] == 1:
        task.core_conf = TaskCoreConf.CORE2X1
    # Record allocated host
    task.proc_host = dnn_details['allocated_host']
    if decentralised:
        ev_keys = ['finish_time', 'start_time', 'M', 'N', 'allocated_host']
    else:
        ev_keys = ['estimated_finish', 'estimated_start', 'M', 'N', 'allocated_host']
    ev_details = {k:dnn_details[k] for k in ev_keys}
    task.events.append(Event(EventType.ALLOC_SUCCESS, time, ev_details))

def parse_HIGH_COMP_ALLOCATION_FAIL(msg_content, time, state,
                                workstealer=False,
                                decentralised=False):
    """
    Update allocation for high comp task
    """
    if workstealer:
        # Ignore
        return
    dnn_id = msg_content['dnn_id']
    src_host = dnn_id.split('_')[0]
    # Find the task from the list of frames of this host
    task = None
    for frame in reversed(state[src_host]):
        for hctask in frame.high_comp:
            if hctask.dnn_id == dnn_id:
                task = hctask
                break
        if task is not None: break
    if task == None:
        print(f"Error on HIGH_COMP_ALLOCATION_FAIL {dnn_id} {time}")
        return
    task.events.append(Event(EventType.ALLOC_FAIL, time, None))

def parse_HIGH_COMP_REALLOCATION_FAIL(msg_content, time, state,
                            workstealer=False,
                            decentralised=False):
    """
    Update allocation for high comp task
    """
    dnn_id = msg_content['dnn_id']
    src_host = dnn_id.split('_')[0]
    # Find the task from the list of frames of this host
    task = None
    for frame in reversed(state[src_host]):
        for hctask in frame.high_comp:
            if hctask.dnn_id == dnn_id:
                task = hctask
                break
        if task is not None: break
    if task == None:
        print(f"Error on HIGH_COMP_REALLOCATION_FAIL {dnn_id} {time}")
        return
    task.events.append(Event(EventType.REALLOC_FAIL, time, None))

def parse_HIGH_COMP_REALLOCATION_SUCCESS(msg_content, time, state,
                                        workstealer=False,
                                        decentralised=False):
    """
    Update allocation for high comp task
    """
    dnn_details = msg_content['dnn']
    dnn_id = dnn_details['dnn_id']
    src_host = dnn_details['source_host']
    # Find the task from the list of frames of this host
    task = None
    for frame in reversed(state[src_host]):
        for hctask in frame.high_comp:
            if hctask.dnn_id == dnn_id:
                task = hctask
                break
        if task is not None: break
    if task == None:
        print(f"Error on HIGH_COMP_REALLOCATION_SUCCESS {dnn_id} {time}")
        return
    ev_keys = ['estimated_finish', 'estimated_start', 'M', 'N', 'allocated_host']
    ev_details = {k:dnn_details[k] for k in ev_keys}
    task.events.append(Event(EventType.REALLOC_SUCCESS, time, ev_details))

def parse_HIGH_COMP_FINISH(msg_content, time, state,
                        workstealer=False,
                        decentralised=False):
    """
    Update allocation for high comp task
    """
    if workstealer:
        if decentralised:
            dnn_details = msg_content
        else:
            dnn_details = msg_content['dnn']
    else:
        dnn_details = msg_content['dnn_details']
    dnn_id = dnn_details['dnn_id']
    if workstealer:
        src_host = dnn_id.split('_')[0]
    else:
        src_host = dnn_details['source_host']
    # Find the task from the list of frames of this host
    task = None
    for frame in reversed(state[src_host]):
        for hctask in frame.high_comp:
            if hctask.dnn_id == dnn_id:
                task = hctask
                break
        if task is not None: break
    if task == None:
        print(f"Error on HIGH_COMP_FINISH {dnn_id} {time}")
        return
    if workstealer:
        if decentralised:
            ev_keys = ['finish_time']
        else:
            ev_keys = ['estimated_finish']
    else:
        ev_keys = ['actual_finish']
    ev_details = {k:dnn_details[k] for k in ev_keys}
    task.events.append(Event(EventType.FINISH, time, ev_details))

def parse_VIOLATED_DEADLINE(msg_content, time, state,
                            workstealer=False,
                            decentralised=False):
    """
    Update allocation for high comp task
    """
    if workstealer:
        if decentralised:
            dnn_details = msg_content
        else:
            dnn_details = msg_content['dnn']
    else:
        dnn_details = msg_content['dnn_details']
    dnn_id = dnn_details['dnn_id']
    if workstealer:
        src_host = dnn_id.split('_')[0]
    else:
        src_host = dnn_details['source_host']
    # Find the task from the list of frames of this host
    task = None
    if decentralised:
        if len(dnn_id.split('_')) == 2:
            print(f"Low comp task violation: {dnn_id}")
        # In decentralised workstealer the violation can happen to 
        # a task that has been allocated, as well as one that wasn't
        # This means if we don't find the task in the last frame we will
        # have to add it.
        frame = state[src_host][-1]
        if frame is None:
            print(f"Error on VIOLATED_DEADLINE {dnn_id} {time}")
            return
        for hctask in frame.high_comp:
            if hctask.dnn_id == dnn_id:
                task = hctask
                break
        if task is None:
            task = Task(TaskType.HIGH_COMP,
                    f"{dnn_id}",
                    src_host,
                    time,
                    time) # Don't have the deadline, likely it's the ev time
    else:
        for frame in reversed(state[src_host]):
            for hctask in frame.high_comp:
                if hctask.dnn_id == dnn_id:
                    task = hctask
                    break
            if task is not None: break
    if task == None:
        print(f"Error on VIOLATED_DEADLINE {dnn_id} {time}")
        return
    task.events.append(Event(EventType.VIOLATE, time, None))

ev_proc_funcs = {
        "LOW_COMP_REQUEST": parse_LOW_COMP_REQUEST,
        "LOW_COMP_ALLOCATION_SUCCESS": parse_LOW_COMP_ALLOCATION_SUCCESS,
        "LOW_COMP_ALLOCATION_FAIL": parse_LOW_COMP_ALLOCATION_FAIL,
        "LOW_COMP_PREMPT_ALLOCATION_SUCCESS": parse_LOW_COMP_PREMPT_ALLOCATION_SUCCESS,
        "LOW_COMP_FINISH": parse_LOW_COMP_FINISH,
        "HIGH_COMP_REQUEST": parse_HIGH_COMP_REQUEST,
        "HIGH_COMP_ALLOCATION_FAIL": parse_HIGH_COMP_ALLOCATION_FAIL,
        "HIGH_COMP_ALLOCATION_SUCCESS": parse_HIGH_COMP_ALLOCATION_SUCCESS,
        "HIGH_COMP_REALLOCATION_FAIL": parse_HIGH_COMP_REALLOCATION_FAIL,
        "HIGH_COMP_REALLOCATION_SUCCESS": parse_HIGH_COMP_REALLOCATION_SUCCESS,
        "HIGH_COMP_FINISH": parse_HIGH_COMP_FINISH,
        "VIOLATED_DEADLINE": parse_VIOLATED_DEADLINE
        }

def parse_exp_logs(exp_logs):
    """
    Parse the experiment logs and return a dictionary of 
    source device --> list of Frames
    It is expected that the experiment logs are a list of 
    dictionaries.
    """
    exp_data = None
    with open(exp_logs, 'r') as f:
        exp_data = json.load(f)
    workstealer = False
    if 'worksteal' in exp_logs:
        workstealer = True
    decentralised = False
    if 'decentr' in exp_logs:
        decentralised = True
    if exp_data is None:
        print("Error parsing json")
        return None
    # Parse events sequentially creating the timeline of frames
    dev_state = {}
    print(f"Experiment has {len(exp_data)} events")
    for ev_json in exp_data:
        ev_type = ev_json['event_type']
        msg_content = ev_json['message_content']
        time = ev_json['time']
        if ev_type not in ev_proc_funcs: continue
        ev_proc_funcs[ev_type](msg_content, time, dev_state,
                                workstealer, decentralised)
    print("Summary of frames")
    for src in dev_state:
        print(f"{src} -> {len(dev_state[src])}")
    return dev_state

def query_frames_complete_per_device(dev_frames):
    """
    dev_frames -- list of frames for a device
    """
    # A frame is complete if all its tasks are finished
    complete_frames = []
    for f in dev_frames:
        complete = True
        if not f.low_comp.is_finished(): continue
        for hc_task in f.high_comp:
            if not hc_task.is_finished():
                complete = False
                break
        if complete:
            complete_frames.append(f)
    return complete_frames 


def query_frames_complete(exp_pickle):
    result_map = {}
    exp_frames = pickle.load(open(exp_pickle, 'rb'))
    for host, frames in exp_frames.items():
        result_map[host] = {}
        result_map[host]["frames"] = len(frames)
        complete = query_frames_complete_per_device(frames)
        result_map[host]["complete"] = len(complete)
        print(f"{host} -> {len(complete)}/{len(frames)}")

    return result_map

def query_low_prio_stats_per_device(frames):
    stats = {'gen':0, 'alloc':0, 'complete':0,
             'violation':0, 'preempted':0, 'realloc': 0}
    for f in frames:
        for hc in f.high_comp:
            stats['gen'] += 1
            if hc.has_event(EventType.ALLOC_SUCCESS): stats['alloc'] += 1
            if hc.is_finished(): stats['complete'] += 1
            if hc.has_event(EventType.VIOLATE): stats['violation'] += 1
            if hc.has_event(EventType.REALLOC_FAIL)\
                or hc.has_event(EventType.REALLOC_SUCCESS): stats['preempted'] += 1
            if hc.has_event(EventType.REALLOC_SUCCESS): stats['realloc'] += 1
    return stats

def query_low_prio_stats(exp_pickle):
    result_map = {}
    exp_frames = pickle.load(open(exp_pickle, 'rb'))
    stats = {'gen':0, 'alloc':0, 'complete':0,
             'violation':0, 'preempted':0, 'realloc': 0}
    for host, frames in exp_frames.items():
        host_stats = query_low_prio_stats_per_device(frames)
        for k, v in host_stats.items():
            stats[k] += v
        print(host, "->", host_stats)
        result_map[host] = host_stats
    result_map["total"] = stats
    print("Total:", stats)
    return result_map

def query_task_core_distribution(exp_pickle):
    exp_frames = pickle.load(open(exp_pickle, 'rb'))
    stats = {'local':{conf:0 for conf in TaskCoreConf},
             'offloaded':{conf:0 for conf in TaskCoreConf}}
    for host, frames in exp_frames.items():
        for f in frames:
            for hc in f.high_comp:
                if hc.core_conf is not None:
                    if hc.is_local():
                        stats['local'][hc.core_conf] += 1
                    else:
                        stats['offloaded'][hc.core_conf] += 1
    print(stats)

    result_map = {
        "local": {
            "2x1": stats['local'][TaskCoreConf.CORE2X1],
            "2x2": stats['local'][TaskCoreConf.CORE2X2]
        },
        "offloaded": {
            "2x1": stats['offloaded'][TaskCoreConf.CORE2X1],
            "2x2": stats['offloaded'][TaskCoreConf.CORE2X2]
        }
    }
    return result_map

def query_frames_with_preemption(exp_pickle):
    pass

def high_comp_total(exp_pickle):
    result_map = {}
    exp_frames = pickle.load(open(exp_pickle, 'rb'))
    for host, frames in exp_frames.items():
        host_hc_total = 0
        for f in frames:
            host_hc_total += len(f.high_comp)
        result_map[host] = host_hc_total
        print(f"{host}->{host_hc_total}")
    return result_map

import pandas as pd
import matplotlib.pyplot as plt
def plot_completion_state_timeseries(exp_pickle):
    """
    Represent the completion state as a timeseries.
    For each frame indicates if the number of tasks (LC and HC) that
    successfully completed.
    Returns a list of (timestamp, LC complete, HC complete), representing
    each frame in the experiment.
    The list will be sorted in increasing order of the timestamp.
    """
    exp_frames = pickle.load(open(exp_pickle, 'rb'))
    ts = []
    for host, frames in exp_frames.items():
        for f in frames:
            lc_cnt = 1 if f.low_comp.is_finished() else 0
            hc_gen = len(f.high_comp)
            hc_cnt = sum([1 if hc.is_finished() else 0 for hc in f.high_comp])
            ts.append((f.low_comp.received_at, lc_cnt, hc_gen, hc_cnt))
    ts.sort(key=lambda x:x[0])
    # Convert to DataFrame, Pandas allows us to resample timeseries
    pdata = pd.DataFrame(ts)
    pdata['ts'] = pd.to_datetime(pdata[0], unit='ms')
    pdata = pdata.set_index('ts')
    # Group data in bins of 1min and sum LC and HC values
    #pdata_min = pdata.resample("1min").sum()
    pdata_min = pdata
    #pdata_min[1].plot(kind='bar', style='.')
    pdata_min[2].plot(kind='bar', color='r')
    pdata_min[3].plot(kind='bar', color='g')
    plt.show()

queries = {
        'frames_complete': query_frames_complete,
        'frames_with_preemption': query_frames_with_preemption,
        'high_comp_total': high_comp_total,
        'low_prio_stats': query_low_prio_stats,
        'task_core_dist': query_task_core_distribution,
        # 'plot_completion_state_ts': plot_completion_state_timeseries,
        }

import argparse
import os
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            prog='Results processing',
            description='Parse result logs and issue queries')
    parser.add_argument('filename',
                         help='JSON file for parsing, pickle for querying')
    parser.add_argument('-a', '--action', choices=['parse', 'query'])
    parser.add_argument('-q', '--query', choices=[queries.keys()] + ["all"])
    args = parser.parse_args()

    if args.action == 'parse':
        logs = os.listdir(args.filename)
        results = {filename: parse_exp_logs(f"{args.filename}/{filename}") for filename in logs if os.path.isfile(f"{args.filename}/{filename}")}
        
        stats_folder = f"{args.filename}/stats_results"

        if not os.path.exists(stats_folder):
            os.mkdir(stats_folder)

        pickle_directory = f"{stats_folder}/pickle_results"
        
        if not os.path.exists(pickle_directory):
            os.mkdir(pickle_directory)

        for result_name, result_data in results.items():
            print(f"Saving {result_name} to pickle")
            pickle.dump(result_data, open(f"{pickle_directory}/{result_name.split('.')[0]}.pickle", 'wb'))
            print("Done")
        
    elif args.action == 'query':
        pickle_dir = f"{args.filename}/pickle_results"
        pickle_files = os.listdir(pickle_dir)

        if args.query == "all":

            result_map = {}

            for pickle_file in pickle_files:
                pickle_file_name = pickle_file.split(".")[0]
                result_map[pickle_file_name] = {}
                if not os.path.isfile(f"{pickle_dir}/{pickle_file}") or pickle_file.lower() == ".ds_store":
                    continue
                
                for query_name, query in queries.items():
                    result_map[pickle_file_name][query_name] = query(f"{pickle_dir}/{pickle_file}")

            with open(f"{args.filename}/result_file.json", "w") as f:
                f.writelines(json.dumps(result_map))

        else:
            result_map = {}

            for pickle_file in pickle_files:
                pickle_file_name = pickle_file.split(".")[0]
                result_map[pickle_file_name] = {}

                if not os.path.isfile(f"{pickle_dir}/{pickle_file}") or pickle_file.lower() == ".ds_store":
                    continue

                result_map[pickle_file_name][args.query] = queries[args.query](f"{pickle_dir}/{pickle_file}")
