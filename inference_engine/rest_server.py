from http.server import BaseHTTPRequestHandler, HTTPServer, SimpleHTTPRequestHandler
import json
from socketserver import ThreadingMixIn
import Constants
import rest_functions
import threading

import Globals
from datetime import datetime as dt

hostName = "localhost"


device_host_list = []

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class RestInterface(BaseHTTPRequestHandler):

    def _set_response(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # Suppress the default logging
        pass

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

            function = None
            if self.path == Constants.TASK_ALLOCATION:
                function = rest_functions.general_allocate_and_forward_function
            elif self.path == Constants.HALT_ENDPOINT:
                function = rest_functions.halt_endpoint
            elif self.path == Constants.LOW_CAP:
                function = rest_functions.lower_capacity
            elif self.path == Constants.RAISE_CAP:
                function = rest_functions.increment_capacity

            # x = threading.Thread(target=work_function, args=(json_request, function, self.path))
            # x.start()
            work_function(json_request=json_request, function=function, path=self.path)

            # print(f"REST SERVER: Requesting lock, held by {Globals.queue_locker}")
            # Globals.work_queue_lock.acquire(blocking=True)
            # print(f"REST SERVER: Acquired lock for {self.path}")
            # Globals.queue_locker = "REST SERVER"
            # if callable(function):
            #     function(json_request)

            # print(f"REST SERVER: Releasing lock")
            # Globals.queue_locker = "N/A"
            # Globals.work_queue_lock.release()

            response_code = 200

            self.send_response(response_code)
            self.end_headers()

        except json.JSONDecodeError:
            print(f"Received request was not json: {request_str}")
            response_code = 400
            return

    def do_GET(self):
        print(f"GET RECEIVED: {self.path}")
        if self.path == Constants.GET_IMAGE:
            image_content = None
            # Open and read the image file
            with open(Constants.INITIAL_FILE_PATH, 'rb') as f:
                image_content = f.read()

            # Set the content type to 'image/jpeg'
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.end_headers()

            # Send the image content
            self.wfile.write(image_content)

        elif self.path == Constants.EXPERIMENT_START:
            Globals.work_request_lock.release()
            self.send_response(200)
            self.end_headers()

def work_function(json_request, function, path):
    print(f"REST SERVER: Requesting lock, held by {Globals.queue_locker}")
    Globals.work_queue_lock.acquire(blocking=True)
    print(f"REST SERVER: Acquired lock for {path}")
    Globals.queue_locker = f"REST SERVER: {path}"

    try:
        function(json_request)
    except:
        print(f"REST SERVER: AN ERROR HAS OCCURRED {path}")
        pass

    print(f"REST SERVER: Releasing lock")
    Globals.queue_locker = "N/A"
    Globals.work_queue_lock.release()

def run(server_class=HTTPServer, handler_class=RestInterface, port=Constants.REST_PORT):
    server_address = ('', port)
    httpd = ThreadedHTTPServer(server_address, handler_class)
    print('REST: Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print('REST: Stopping httpd...\n')
