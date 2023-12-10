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
import PollingThread


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


def startOutboundComms(logging):
    ThreadStart(logging, OutboundComms.outbound_comm_loop,
                "Outbound Comm Loop")


def start_WorkWaitingQueue(logging):
    ThreadStart(logging, WorkWaitingQueue.work_loop, "Work Waiting Queue")


def start_WorkStealing(logging):
    ThreadStart(logging, PollingThread.stealing_loop(), "Work Stealing Poll")


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
    if len(sys.argv) == 3:
        print(f"CLIENT_ADDRESS: {Constants.CLIENT_ADDRESS}")
        print(f"SERVER_ADDRESS: {Constants.CONTROLLER_HOST_NAME}")
        Constants.CONTROLLER_HOST_NAME = sys.argv[2]

    start_IPERF(logging)
    logging.basicConfig(level=logging.INFO)
    logging.getLogger().setLevel(logging.INFO)
    sync_timestamp()
    start_REST(logging)
    start_ResultsQueueManager(logging)
    startOutboundComms(logging)
    start_WorkWaitingQueue(logging)
    hello(logging)
    start_WorkStealing(logging)

    return


if __name__ == "__main__":
    main()
