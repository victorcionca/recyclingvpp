from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import logging
from datetime import datetime as dt
import Constants
import datetime
import Globals
import EventType
import utils
hostName = "localhost"


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
            json_request: dict = json.loads(request_body)

            if self.path == Constants.ALLOCATE_LOW_TASK:
                self.allocate_low_task(json_request=json_request)
            if self.path == Constants.SET_EXPERIMENT_START:
                self.set_experiment_start_time(json_request=json_request)

        except json.JSONDecodeError:
            print(f"Received request was not json: {request_str}")
            response_code = 400
            return

        self.send_response(response_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        self.wfile.write(bytes(response_json, "utf8"))

    def allocate_low_task(self, json_request: dict) -> None:
        dnn_id: str = json_request["dnn_id"]

        finish_time: dt = dt.now()
        if isinstance(json_request["start_time"], str):
            finish_time = from_ms_since_epoch(json_request["finish_time"])
        else:
            finish_time = from_ms_since_epoch(str(json_request["finish_time"]))

        print(f'{finish_time.strftime("%Y-%m-%d %H:%M:%S:%f")} LOW COMP ALLO FIN')

        utils.add_task_to_event_queue(
            event_item={"event_type": EventType.EventTypes.LOW_COMP_FINISH, "time": finish_time})
        return

    def set_experiment_start_time(self, json_request: dict):
        start_time: dt = dt.now()

        if isinstance(json_request["start_time"], str):
            start_time = from_ms_since_epoch(json_request["start_time"])
        else:
            start_time = from_ms_since_epoch(str(json_request["start_time"]))

        if Globals.SET_A_OR_B:
            start_time = start_time + \
                datetime.timedelta(seconds=Constants.FRAME_RATE / 2)

        for i in range(0, len(Globals.trace_list)):
            delta = datetime.timedelta(seconds=Constants.FRAME_RATE) * i
            utils.add_task_to_event_queue(event_item={
                                          "event_type": EventType.EventTypes.OBJECT_DETECT_START, "time": start_time + delta})
            delta = delta + \
                datetime.timedelta(
                    milliseconds=Constants.OBJECT_DETECTION_TIME_MS)
            utils.add_task_to_event_queue(event_item={
                                          "event_type": EventType.EventTypes.OBJECT_DETECT_FINISH, "time": start_time + delta})

        experiment_finish_time = start_time + \
            (datetime.timedelta(seconds=Constants.FRAME_RATE)
             * (Constants.OBJECT_DETECTION_COUNT + 1))
        Globals.EXPERIMENT_FINISH_TIME = experiment_finish_time
        Globals.EXPERIMENT_START = True
        return


def from_ms_since_epoch(ms: str) -> dt:
    return dt.fromtimestamp(int(ms) / 1000.0)


def run_server(server_class=HTTPServer, handler_class=RestInterface, port=Constants.EXPERIMENT_INFERFACE):
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
