import iperf3
import Constants

def run_IperfServer():
    server = iperf3.Server()
    server.bind_address = Constants.CLIENT_ADDRESS
    server.port = Constants.IPERF_PORT
    server.verbose = False

    # while True:
    server.run()