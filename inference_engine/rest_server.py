from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import Constants
import rest_functions
import Globals
from datetime import datetime as dt

hostName = "localhost"


device_host_list = []

version_list = []

class RestInterface(BaseHTTPRequestHandler):

    def _set_response(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        json_request = {}

        # Process the request data and extract the input, target core, etc.
        request_str = self.requestline
        request_body = self.rfile.read(int(self.headers['Content-Length']))

        response_json = ""

        try:
            json_request = {}

            if 'multipart/form-data' in self.headers["Content-Type"]:
                content_length = int(self.headers.get('Content-Length'))
                
                post_data = request_body
                content_type = self.headers['Content-Type']
                
                # Parse the multipart/form-data request
                boundary = content_type.split('boundary=')[1].encode()
                parts = post_data.split(b'--' + boundary)

                json_data = None

                for part in parts:
                    if b'Content-Disposition: form-data;' in part:
                        if b'payload' in part:
                            json_data = part

                if json_data is not None:
                    left_item = '{'
                    right_item = '\r'

                    json_data = json_data.decode()
                    before, _, after = json_data.partition(left_item)
                    json_data = left_item + after
                    before, _, after = json_data.partition(right_item)
                    
                    json_request = json.loads(before)

            else:
                json_request = json.loads(request_body)

            if "request_version" in json_request.keys():
                if json_request["request_version"] in version_list:
                    print(f"DUPLICATE REQUEST RECEIVED:\n{json_request}")
                    response_code = 200

                    self.send_response(response_code)
                    self.end_headers()
                    return
                else:
                    version_list.append(json_request["request_version"])

            function = None
            if self.path == Constants.TASK_ALLOCATION:
                function = rest_functions.general_allocate_and_forward_function
            elif self.path == Constants.TASK_FORWARD:
                function = rest_functions.task_allocation_function
            elif self.path == Constants.HALT_ENDPOINT:
                function = rest_functions.halt_endpoint

            # if callable(function):
            #      x = Thread(target=function, args=(json_request,))
            #      x.start()
            Globals.work_queue_lock.acquire(blocking=True)
            if callable(function):
                function(json_request)
            Globals.work_queue_lock.release()

            response_code = 200

            self.send_response(response_code)
            self.end_headers()

        except json.JSONDecodeError:
            print(f"Received request was not json: {request_str}")
            response_code = 400
            return
        

def run(server_class=HTTPServer, handler_class=RestInterface, port=Constants.REST_PORT):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('REST: Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print('REST: Stopping httpd...\n')
