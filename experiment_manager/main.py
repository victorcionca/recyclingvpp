from typing import List
import threading
import logging
import experiment_loop
import experiment_manager
import sys
import json
import TraceParser
import Globals


def start_REST(logging):
    ThreadStart(logging, experiment_manager.run_server, "REST") # type: ignore # type: ignore


def start_experiment_loop(logging):
    ThreadStart(logging, experiment_loop.run_loop, "Experiment Loop")


def ThreadStart(logging, function, thread_name):
    logging.info(f"Main    : before creating {thread_name} thread")
    x = threading.Thread(target=function)
    logging.info(f"Main    : before running {thread_name} thread")
    x.start()
    logging.info(f"Main    : running {thread_name} thread")
    return


def main():
    logging.basicConfig(level=logging.INFO)
    start_REST(logging)
    start_experiment_loop(logging)
    return


if __name__ == "__main__":
    test_mode = len(sys.argv) < 2
    device_task = int(sys.argv[1]) if not test_mode else 0
    Globals.SET_A_OR_B = bool(sys.argv[2]) if not test_mode else False
    trace_file_path = "/home/pi/recyclingvpp/experiment_manager/test_trace_file.json" if test_mode else "trace_file.json"
    trace_file = open(trace_file_path, "r")
    trace_data = json.load(trace_file)
    Globals.trace_list = TraceParser.trace_parser(trace_data, device_task)
    main()