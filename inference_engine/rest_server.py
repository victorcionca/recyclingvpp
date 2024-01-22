import Constants
import rest_functions
import Globals
import utils
from typing import Dict, Any
from fastapi.responses import FileResponse
import logging
from fastapi import FastAPI, Request
from uvicorn import run
from datetime import datetime as dt
from datetime import timedelta as td
import HighCompAlloFunctions
import DataProcessing


app = FastAPI()


def search_and_prune_version(request_version):
    if request_version in Globals.request_version_list:
        return True

    else:
        Globals.request_version_list.append(request_version)
        return False


@app.post(Constants.REQUEST_WORK)
async def work_request(request: Request):
    if request.client is not None:
        hostname = request.client.host
        req_body = await request.json()
        capacity = int(req_body["capacity"])
        result = HighCompAlloFunctions.task_search(capacity, hostname)

        return result
    else:
        return {"success": False}


@app.post(Constants.RETURN_WORK)
def return_work(item: Dict[Any, Any]):
    tasks = [
        {
            "dnn_id": item["dnn_id"],
            "deadline": DataProcessing.from_ms_since_epoch(item["deadline"]),
        }
    ]
    HighCompAlloFunctions.add_high_comp_to_stealing_queue(tasks)
    return


@app.post(Constants.TASK_ALLOCATION)
def add_high_task(item: Dict[Any, Any]):
    if search_and_prune_version(item["request_version"]) == False:
        rest_functions.general_allocate_and_forward_function(item)
    else:
        logging.info(f"Duplicate Request: {item['request_version']}")
    return {}


@app.post(Constants.HALT_ENDPOINT)
def halt_task(item: Dict[Any, Any]):
    if search_and_prune_version(item["request_version"]) == False:
        rest_functions.halt_endpoint(item)
    else:
        logging.info(f"Duplicate Request: {item['request_version']}")

    return {}


@app.post(Constants.ALLOCATE_LOW_TASK)
def add_low_task(item: Dict[Any, Any]):
    if search_and_prune_version(item["request_version"]) == False:
        rest_functions.allocate_low_task(item)
    else:
        logging.info(f"Duplicate Request: {item['request_version']}")

    return {}


@app.post(Constants.SET_EXPERIMENT_START)
def experiment_start(item: Dict[Any, Any]):
    logging.info(item)
    Globals.client_list = item["client_list"]
    Globals.bytes_per_ms = int(item["bytes_per_ms"])
    rest_functions.set_experiment_start_time(item)
    return


@app.get(Constants.EXPERIMENT_START)
def experi_strt():
    Globals.work_request_lock.release()
    return {}


@app.get("/get_cores")
def get_cores():
    return {
        "CORE_MAP": f"{Globals.core_map}",
        "CORE_CAP_GATHER": {utils.capacity_gatherer()},
        "LOCAL_CORE_CAP": {Globals.local_capacity},
        "REQUEST_LOCKED": {Globals.work_request_lock.locked()},
        "WORK_QUEUE_LOCKED": {Globals.queue_locker},
        "CLIENT_LIST": {tuple(Globals.client_list)},
    }


@app.get(Constants.GET_IMAGE)
def get_image():
    return FileResponse(Constants.INITIAL_FILE_PATH)


def run_server(port=Constants.REST_PORT):
    run(app, host=Constants.CLIENT_ADDRESS, port=port, log_level="critical")


# hostName = "localhost"

# device_host_list = []

# ifp = open(Constants.INITIAL_FILE_PATH, "rb")
# image_content = ifp.read()
# ifp.close()


# class RestInterface(SimpleHTTPRequestHandler):
#     def do_POST(self):
#         json_request = {}

#         # Process the request data and extract the input, target core, etc.
#         request_str = self.requestline
#         request_body = self.rfile.read(int(self.headers["Content-Length"]))

#         response_json = ""

#         try:
#             json_request = {}

#             json_request = json.loads(request_body)

#             if (
#                 isinstance(json_request, dict)
#                 and "request_version" in json_request.keys()
#             ):
#                 if search_and_prune_version(json_request["request_version"]):
#                     response_code = 200

#                     self.send_response(response_code)
#                     self.end_headers()

#                     logging.info(
#                         f"REST SERVER: Duplicate Request for {self.path}, version_id: {json_request['request_version']}"
#                     )

#                     return

#             function = None

#             if self.path == Constants.TASK_ALLOCATION:
#                 logging.info(
#                     f"REST: ALLOCATE - REQUEST COUNTER {json_request['request_counter']}"
#                 )
#                 function = rest_functions.general_allocate_and_forward_function
#             elif self.path == Constants.HALT_ENDPOINT:
#                 function = rest_functions.halt_endpoint
#             elif self.path == Constants.ALLOCATE_LOW_TASK:
#                 function = rest_functions.allocate_low_task
#             elif self.path == Constants.SET_EXPERIMENT_START:
#                 function = rest_functions.set_experiment_start_time

#             response_code = work_function(
#                 json_request=json_request, function=function, path=self.path
#             )


#             self.send_response(response_code)
#             self.end_headers()

#         except Exception as e:
#             print(e)
#             response_code = 400
#             self.send_response(response_code)
#             self.end_headers()
#             return

#     def do_GET(self):
#         logging.info(f"GET RECEIVED: {self.path}")
#         if self.path == Constants.EXPERIMENT_START:
#             Globals.work_request_lock.release()
#             self.send_response(200)
#             self.end_headers()

#         elif self.path == "/get_cores":
#             self.send_header("Content-Type", "application/json")
#             self.send_response(200)
#             self.end_headers()
#             self.wfile.write(
#                 f"CORE_MAP {Globals.core_map} CORE_CAP {utils.capacity_gatherer()} REQUEST_LOCKED {Globals.work_request_lock.locked()} WORK_QUEUE_LOCKED {Globals.queue_locker}".encode(
#                     "utf-8"
#                 )
#             )

#         elif self.path == Constants.GET_IMAGE:
#             try:
#                 # Set the content type to 'image/jpeg'
#                 self.send_response(200)
#                 self.send_header("Content-type", "image/png")
#                 self.send_header("Content-Length", f"{len(image_content)}")
#                 self.end_headers()

#                 # Send the image content
#                 self.wfile.write(image_content)
#                 logging.info(f"IMAGE TRANSFERRED: {self.path}")
#             except Exception as e:
#                 logging.info(f"TRANSFERRING IMAGE FAILED: {e}")
#             return


# def work_function(json_request, function, path):
#     try:
#         function(json_request)
#     except Exception as e:
#         print(f"REST SERVER: AN ERROR HAS OCCURRED {path} \n")
#         print(json_request)
#         print("\n")
#         print(e)
#         print(traceback.format_exc())
#         # if path == Constants.TASK_ALLOCATION:
#         #     Globals.work_request_lock.release()
#         exit()
#         return 400
#     return 200


# def run(server_class=HTTPServer, handler_class=RestInterface, port=Constants.REST_PORT):
#     server_address = ("", port)
#     httpd = server_class(server_address, handler_class)
#     logging.info("REST: Starting httpd...\n")
#     try:
#         httpd.serve_forever()
#     except KeyboardInterrupt:
#         pass
#     httpd.server_close()
#     logging.info("REST: Stopping httpd...\n")
