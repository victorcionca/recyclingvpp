import threading
import logging
import OutboundComms
import WorkWaitingQueue
import rest_server
import iperf_server
import requests
import Constants
import ResultQueueManager
import ntplib
import os
from datetime import datetime
import sys
import Constants


def start_REST(logging):
    ThreadStart(logging, rest_server.run, "REST")


def start_IPERF(logging):
    ThreadStart(logging, iperf_server.run_IperfServer, "IPERF")


def start_ResultsQueueManager(logging):
    ThreadStart(logging, ResultQueueManager.ResultsQueueLoop, "ResultsQueue")


def ThreadStart(logging, function, thread_name):
    print(f"Main    : before creating {thread_name} thread")
    x = threading.Thread(target=function)
    print(f"Main    : before running {thread_name} thread")
    x.start()
    print(f"Main    : running {thread_name} thread")
    return


def hello(logging):
    print("Main    : Registering with controller")
    host_ip = Constants.CONTROLLER_HOST_NAME
    endpoint = f'http://{host_ip}:{Constants.CONTROLLER_DEFAULT_PORT}{Constants.CONTROLLER_REGISTER_DEVICE}'
    print(f"endpoint: {endpoint}")
    requests.post(endpoint)


def start_inference_engine(logging):
    inference_handler = inference_engine.InferenceHandler() # type: ignore
    ThreadStart(logging, inference_handler.run, "Inference Engine")
    return


def startOutboundComms(logging):
    ThreadStart(logging, OutboundComms.outbound_comm_loop,
                "Outbound Comm Loop")


def start_WorkWaitingQueue(logging):
    ThreadStart(logging, WorkWaitingQueue.work_loop, "Work Waiting Queue")


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
    Constants.CLIENT_ADDRESS = sys.argv[1]
    logging.basicConfig(level=logging.INFO)
    logging.getLogger().setLevel(logging.INFO)
    sync_timestamp()
    start_IPERF(logging)
    start_REST(logging)
    hello(logging)
    start_ResultsQueueManager(logging)
    startOutboundComms(logging)
    start_WorkWaitingQueue(logging)

    return


if __name__ == "__main__":
    main()
