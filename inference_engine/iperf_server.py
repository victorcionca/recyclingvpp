import iperf3
import Constants
import Globals
import logging


def run_IperfServer():
    server = iperf3.Server()
    logging.info(f"LOG: Binding Address: {Constants.CLIENT_ADDRESS} {Constants.IPERF_PORT}")
    server.bind_address = Constants.CLIENT_ADDRESS
    server.port = Constants.IPERF_PORT
    server.verbose = True
    server.json_output = False

    server.run()
