from http.server import BaseHTTPRequestHandler, HTTPServer, SimpleHTTPRequestHandler
import json
import Constants
import rest_functions
import logging
import Globals
from datetime import datetime as dt
from datetime import timedelta as td
import traceback

hostName = "localhost"

device_host_list = []

def search_and_prune_version(request_version):

    version_found = False

    new_request_list = {}
    for vers, time_val in Globals.request_version_list.items():
        if vers == request_version:
            version_found = True
        
        if dt.now() < time_val + td(seconds=10):
            new_request_list[vers] = time_val
    
    if version_found == False:
        new_request_list[request_version] = dt.now()

    Globals.request_version_list = new_request_list

    return version_found


class RestInterface(BaseHTTPRequestHandler):
    
    def do_POST(self):
        json_request = {}

        # Process the request data and extract the input, target core, etc.
        request_str = self.requestline
        request_body = self.rfile.read(int(self.headers['Content-Length']))

        response_json = ""  

        try:
            json_request = {}

            json_request = json.loads(request_body)
            
            if isinstance(json_request, dict) and "request_version" in json_request.keys():
                if search_and_prune_version(json_request["request_version"]):
                    response_code = 200

                    self.send_response(response_code)
                    self.end_headers()

                    logging.info(f"REST SERVER: Duplicate Request for {self.path}, version_id: {json_request['request_version']}")

                    return

            function = None

            if self.path == Constants.TASK_ALLOCATION:
                logging.info(f"REST: ALLOCATE - REQUEST COUNTER {json_request['request_counter']}")
                function = rest_functions.general_allocate_and_forward_function
            elif self.path == Constants.HALT_ENDPOINT:
                function = rest_functions.halt_endpoint
            response_code = work_function(json_request=json_request, function=function, path=self.path)

            self.send_response(response_code)
            self.end_headers()

        except Exception as e:
            print(e)
            response_code = 400
            self.send_response(response_code)
            self.end_headers()
            return

    def do_GET(self):
        logging.info(f"GET RECEIVED: {self.path}")
        if self.path == Constants.EXPERIMENT_START:
            Globals.work_request_lock.release()
            self.send_response(200)
            self.end_headers()
        
        elif self.path == "/get_cores":
            self.send_header('Content-Type', 'application/json')
            self.send_response(200)
            self.end_headers()
            self.wfile.write(f"CORE_MAP {Globals.core_map} CORE_CAP {rest_functions.capacity_gatherer()} REQUEST_LOCKED {Globals.work_request_lock.locked()} WORK_QUEUE_LOCKED {Globals.queue_locker}".encode("utf-8"))
            return

def work_function(json_request, function, path):
    try:
        function(json_request)
    except Exception as e:
        print(f"REST SERVER: AN ERROR HAS OCCURRED {path} \n")
        print(json_request)
        print("\n")
        print(e)
        print(traceback.format_exc())
        # if path == Constants.TASK_ALLOCATION:
        #     Globals.work_request_lock.release()
        exit()
        return 400
    return 200

def run(server_class=HTTPServer, handler_class=RestInterface, port=Constants.REST_PORT):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('REST: Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('REST: Stopping httpd...\n')
