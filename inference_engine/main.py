import threading
import logging
from inference_engine.OutboundComms import outbound_comm_loop
from inference_engine.WorkWaitingQueue import work_loop
from inference_engine.inference_engine import InferenceHandler
from rest_server import run
from iperf_server import run_IperfServer
import requests
import sys
from Constants.Constants import *
from ResultQueueManager import ResultsQueueLoop
# from grpc_server import run_GRPC_Server


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
    host_ip = CONTROLLER_HOST_NAME
    requests.post(
        f'{host_ip}{CONTROLLER_DEFAULT_ROUTE}{CONTROLLER_REGISTER_DEVICE}')


def start_inference_engine(logging):
    inference_handler = InferenceHandler()
    ThreadStart(logging, inference_handler.run, "Inference Engine")
    return


def startOutboundComms(logging):
    ThreadStart(logging, outbound_comm_loop, "Outbound Comm Loop")


def start_WorkWaitingQueue(logging):
    ThreadStart(logging, work_loop, "Work Waiting Queue")


def main():
    logging.basicConfig(level=logging.INFO)
    hello(logging)
    start_REST(logging)
    start_IPERF(logging)
    start_ResultsQueueManager(logging)
    start_inference_engine(logging)
    startOutboundComms(logging)
    start_WorkWaitingQueue(logging)

    return


if __name__ == "__main__":
    main()
