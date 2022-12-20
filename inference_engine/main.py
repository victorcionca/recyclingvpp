import threading
import logging
from rest_server import run
from iperf_server import run_IperfServer
import requests
import sys
import Constants
from ResultQueueManager import ResultsQueueLoop

def start_REST(logging):
    ThreadStart(logging, run, "REST")

def start_IPERF(logging):
    ThreadStart(logging, run_IperfServer, "IPERF")

def start_ResultsQueueManager(logging):
    ThreadStart(logging, ResultsQueueLoop, "ResultsQueue")

def ThreadStart(logging, function, thread_name):
    logging.info(f"Main    : before creating {thread_name} thread")
    x = threading.Thread(target=function)
    logging.info(f"Main    : before running {thread_name} thread")
    x.start()
    logging.info(f"Main    : running {thread_name} thread")
    return

def hello(logging):
    logging.info("Main    : Registering with controller")
    host_ip = sys.argv[1]
    requests.post(f'{host_ip}:{Constants.CONTROLLER_DEFAULT_PORT}{Constants.CONTROLLER_DEFAULT_ROUTE}{Constants.CONTROLLER_REGISTER_DEVICE}')

def main():
    logging.basicConfig(level=logging.INFO)
    hello(logging)
    start_REST(logging)
    start_IPERF(logging)
    start_ResultsQueueManager(logging)

    
    return

if __name__ == "__main__":
    main()