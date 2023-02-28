import threading
import logging
import OutboundComms
import WorkWaitingQueue
import inference_engine
import rest_server
import Globals
import iperf_server
import json
import requests
import Constants
import ResultQueueManager
# from grpc_server import run_GRPC_Server


def start_REST(logging):
    ThreadStart(logging, rest_server.run, "REST")


def start_IPERF(logging):
    ThreadStart(logging, iperf_server.run_IperfServer, "IPERF")


def start_ResultsQueueManager(logging):
    ThreadStart(logging, ResultQueueManager.ResultsQueueLoop, "ResultsQueue")


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
    print(f"endpoint: {endpoint}")
    requests.post(endpoint)



def start_inference_engine(logging):
    inference_handler = inference_engine.InferenceHandler()
    ThreadStart(logging, inference_handler.run, "Inference Engine")
    return


def startOutboundComms(logging):
    ThreadStart(logging, OutboundComms.outbound_comm_loop,
                "Outbound Comm Loop")


def start_WorkWaitingQueue(logging):
    ThreadStart(logging, WorkWaitingQueue.work_loop, "Work Waiting Queue")


def main():
    logging.basicConfig(level=logging.INFO)
    start_IPERF(logging)
    start_REST(logging)
    hello(logging)
    start_ResultsQueueManager(logging)
    start_inference_engine(logging)
    startOutboundComms(logging)
    start_WorkWaitingQueue(logging)

    return


if __name__ == "__main__":
    main()
