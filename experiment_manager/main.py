import ntplib
import threading
import logging
import experiment_loop
import experiment_manager
from datetime import datetime
import sys
import json
import TraceParser
import Globals
import Constants
import os

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


def sync_timestamp():
    # Create an NTP client
    client = ntplib.NTPClient()

    # Query the NTP server and get the response
    response = client.request(Constants.CONTROLLER_HOST_NAME)

    # Adjust the local system time based on the NTP server's response
    now = datetime.fromtimestamp(response.tx_time)

    # Set the system time of the current device
    # Note: Setting system time may require elevated privileges (e.g., running as administrator)
    # Consult the platform-specific documentation for setting system time in your environment
    os.system('sudo date -s "{}"'.format(now))


def main():
    sync_timestamp()
    logging.basicConfig(level=logging.INFO)
    start_REST(logging)
    start_experiment_loop(logging)
    return


'''
Program arguments
device task - int   : Indicates which track in the trace file it will use
Set A or B  - bool  : Boolean value that indicates if the device is offset in processing
test mode   - bool  : Boolean value for testing
eg. python3 main.py 0 True False 
'''
if __name__ == "__main__":
    device_task = int(sys.argv[1]) if len(sys.argv) != 1 else 0
    Globals.SET_A_OR_B = bool(sys.argv[2]) if len(sys.argv) != 1 else False
    test_mode = bool(sys.argv[3]) if len(sys.argv) != 1 else True
    trace_file_path = "/home/pi/recyclingvpp/experiment_manager/test_trace_file.json" if test_mode else "/home/pi/recyclingvpp/experiment_manager/trace_file.json"
    trace_file = open(trace_file_path, "r")
    trace_data = json.load(trace_file)
    Globals.trace_list = TraceParser.trace_parser(trace_data, device_task)
    main()