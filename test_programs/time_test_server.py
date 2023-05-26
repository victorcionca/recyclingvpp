from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
from datetime import datetime as dt
hostName = "localhost"
import time_test_global

class RestInterface(BaseHTTPRequestHandler):

    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_POST(self):
        json_request = {}

        # Process the request data and extract the input, target core, etc.
        request_str = self.requestline
        request_body = self.rfile.read(int(self.headers['Content-Length']))

        response_json = ""

        response_code = 200

        try:
            if self.path == "/time_test":
                json_request: dict = json.loads(request_body)
                time_str = json_request["time"]
                incoming_time = from_ms_since_epoch(json_request['time'])
                current_time = dt.now()
                print(f"\n\n\nTime from client: {incoming_time}\nCurrent Time: {current_time}\n\n\n")

                if incoming_time > current_time:
                    time_test_global.desync_count = time_test_global.desync_count + 1
                    print(f"ERROR: Client time out of sync: \n\n CLIENT: {incoming_time} \n\n CURRENT: {current_time}\n\n\n")

            if self.path == "/fin":
                print(f"Total desync over 10 mins is: {time_test_global.desync_count}")

        except json.JSONDecodeError:
            print(f"Received request was not json: {request_str}")
            response_code = 400
            return

        self.send_response(response_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        self.wfile.write(bytes(response_json, "utf8"))

    
def from_ms_since_epoch(ms: str) -> dt:
    return dt.fromtimestamp(int(ms) / 1000.0)


def run_server(server_class=HTTPServer, handler_class=RestInterface, port=9911):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('REST: Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('REST: Stopping httpd...\n')

run_server()

