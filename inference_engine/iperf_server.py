import iperf3
import Constants
import Globals

def run_IperfServer():
    server = iperf3.Server()
    server.bind_address = Constants.CLIENT_ADDRESS
    server.port = Constants.IPERF_PORT
    server.verbose = True
    server.json_output = False

    # while True:
    server.run()
    Globals.work_request_lock.release()