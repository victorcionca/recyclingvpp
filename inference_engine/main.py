import threading
import logging
from rest_server import run
from iperf_server import run_IperfServer
import requests
import sys
import Constants

def start_REST():
    logging.basicConfig(level=logging.INFO)
    logging.info("Main    : before creating REST thread")
    x = threading.Thread(target=run)
    logging.info("Main    : before running REST thread")
    x.start()
    logging.info("Main    : running REST thread")

def start_IPERF():
    logging.basicConfig(level=logging.INFO)
    logging.info("Main    : before creating IPERF thread")
    x = threading.Thread(target=run_IperfServer)
    logging.info("Main    : before running IPERF thread")
    x.start()
    logging.info("Main    : running IPERF thread")

def hello():
    logging.info("Main    : Registering with controller")
    host_ip = sys.argv[1]
    requests.post(f'{host_ip}:{Constants.CONTROLLER_DEFAULT_PORT}{Constants.CONTROLLER_DEFAULT_ROUTE}{Constants.CONTROLLER_REGISTER_DEVICE}')

def main():
    hello()
    start_REST()
    start_IPERF()

    
    return

if __name__ == "__main__":
    main()