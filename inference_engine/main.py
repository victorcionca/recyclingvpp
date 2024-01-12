import threading
import logging
import WorkWaitingQueue
import rest_server
import iperf_server
import requests
import Constants
import ResultQueueManager
import ntplib
import os
import Globals
from datetime import datetime
import sys
import Constants
import PollingThread
import traceback


def start_REST(logging):
    ThreadStart(logging, rest_server.run, "REST")


def start_IPERF(logging):
    ThreadStart(logging, iperf_server.run_IperfServer, "IPERF")


def start_main_loop(logging):
    ThreadStart(logging, main_loop, "loop")


def ThreadStart(logging, function, thread_name):
    logging.info(f"Main    : before creating {thread_name} thread")
    x = threading.Thread(target=function)
    logging.info(f"Main    : before running {thread_name} thread")
    x.start()
    logging.info(f"Main    : running {thread_name} thread")
    return


def hello(logging):
    logging.info("Main    : Registering with controller")
    host_ip = Constants.CONTROLLER_HOST_NAME
    endpoint = f'http://{host_ip}:{Constants.CONTROLLER_DEFAULT_PORT}{Constants.CONTROLLER_REGISTER_DEVICE}'
    logging.info(f"endpoint: {endpoint}")
    requests.post(endpoint)



def main_loop():
    while Globals.work_request_lock.locked():
        continue

    while True:
        acquire_lock_run(PollingThread.stealing_loop, "Poller")
        acquire_lock_run(ResultQueueManager.ResultsQueueLoop, "ResultQueue")
        acquire_lock_run(WorkWaitingQueue.worker_watcher, "WorkWatcher")
        acquire_lock_run(WorkWaitingQueue.halt_function, "HaltStage")
        acquire_lock_run(WorkWaitingQueue.work_loop, "WorkWaiting")


def acquire_lock_run(function, function_name):
    Globals.queue_locker = function_name
    old_lk = Globals.lock_counter
    Globals.lock_counter += 1
    
    try:
        function()
    except Exception as e:
        logging.info(f"CORE_MAP: {Globals.core_map}\n")
        logging.info(f"WORK WAITING QUEUE: {Globals.work_waiting_queue}\n")
        logging.info(f"THREAD_HOLDER: {Globals.thread_holder}")
        logging.info(f"REQUEST_VERSION_DICT: {Globals.request_version_list}")

        print(e)
        print(traceback.format_exc())
        exit()

    Globals.queue_locker = "N/A"

def sync_timestamp():
    retry = True
    while retry:
        try:
            # Create an NTP client
            client = ntplib.NTPClient()

            # Query the NTP server and get the response
            response = client.request(Constants.CONTROLLER_HOST_NAME)

            # Adjust the local system time based on the NTP server's response
            now = datetime.fromtimestamp(response.tx_time)

            # Set the system time of the current device
            # Note: Setting system time may require elevated privileges (e.g., running as administrator)
            # Consult the platform-specific documentation for setting system time in your environment
            #TODO Make sure to set this back for RPi's
            os.system('sudo date -s "{}"'.format(now))
            logging.info("NTP SYNC: Timestamp successfully synced with server")
            retry = False
        except:
            logging.info("NTP SYNC: Timestamp sync with server failed, retrying.")
            retry = True


def main():
    logging.basicConfig(level=logging.INFO)
    logging.getLogger().setLevel(logging.INFO)
    Constants.CLIENT_ADDRESS = sys.argv[1]
    if len(sys.argv) == 3:
        logging.info(f"CLIENT_ADDRESS: {Constants.CLIENT_ADDRESS}")
        logging.info(f"SERVER_ADDRESS: {Constants.CONTROLLER_HOST_NAME}")
        Constants.CONTROLLER_HOST_NAME = sys.argv[2]

    start_IPERF(logging)
    sync_timestamp()
    start_REST(logging)
    hello(logging)
    start_main_loop(logging)

    return


if __name__ == "__main__":
    main()
