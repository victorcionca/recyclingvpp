import OutboundComm
from datetime import datetime as dt
import Constants
import requests
import logging
import Globals
import utils


def deadlineViolated(
    comm_item: OutboundComm.OutboundComm = OutboundComm.OutboundComm(),
):
    logging.info("Deadline Violation")
    if isinstance(comm_item.payload, dict):
        payload: dict = comm_item.payload
        url = f"http://{Constants.CONTROLLER_HOST_NAME}:{Constants.CONTROLLER_DEFAULT_PORT}{Constants.CONTROLLER_VIOLATED_DEADLINE}"
        payload["request_id"] = f"{dt.now().timestamp()}"
        success = False
        while not success:
            try:
                response = requests.post(url, json=payload)
                success = True

                if response.status_code != 200:
                    logging.info("ERROR REQUEST NOT RECEIVED")
                    success = False
            except Exception as e:
                logging.info(f"DEADLINE VIOLATED Outbound: Failed to reach contr - {e}")
    return


def getImage(source_host):
    success = False
    while not success:
        try:
            requests.get(
                f"http://{source_host}:{Constants.REST_PORT}{Constants.GET_IMAGE}"
            )
            success = True
        except:
            logging.info(f"ImageGet: Failed to reach {source_host}")


def stateUpdate(comm_item: OutboundComm.OutboundComm = OutboundComm.OutboundComm()):
    url = f"http://{Constants.CONTROLLER_HOST_NAME}:{Constants.CONTROLLER_DEFAULT_PORT}{Constants.CONTROLLER_STATE_UPDATE}"
    logging.info(f"Issuing state_update {url}")
    if isinstance(comm_item.payload, dict):
        payload: dict = comm_item.payload

        payload["request_id"] = f"{dt.now().timestamp()}"
        success = False
        while not success:
            try:
                requests.post(url, json=payload)
                success = True
            except:
                logging.info(f"STATE UPDATE Outbound: Failed to reach contr")
                logging.info(payload)
    logging.info(f"State_update success {url}")
    return


def PollingRequest(request_counter, local_capacity, client):
    success = False
    url = f"http://{client}:{Constants.REST_PORT}{Constants.REQUEST_WORK}"
    body = {
        "request_counter": request_counter,
        "capacity": local_capacity,
        "request_id": f"{dt.now().timestamp()}",
        "source": Constants.CLIENT_ADDRESS
    }
    headers = {
        "Content-Type": "application/json",
    }
    response_body = {"success": False}
    while not success:
        try:
            response = requests.post(url, json=body, headers=headers)
            response_body = response.json()
            success = True
            if response.status_code != 200:
                logging.info("ERROR REQUEST NOT RECEIVED")
                success = False
        except Exception as e:
            logging.info(f"POLLING REQUEST ELoop: Failed to reach client - {e}")
    return response_body


def low_comp_allocation_fail(dnn_id: str):
    data = {"dnn_id": dnn_id, "time": int(dt.now().timestamp() * 1000)}

    headers = {
        "Content-Type": "application/json",
    }

    url = f"http://{Constants.CONTROLLER_HOST_NAME}:{Constants.CONTROLLER_DEFAULT_PORT}{Constants.POST_LOW_COMP_FAIL}"

    success = False
    logging.info(f"POSTING LOW COMP FAIL {dnn_id}")
    while not success:
        try:
            response = requests.post(url, json=data, headers=headers)
            success = True

            if response.status_code != 200:
                logging.info("ERROR REQUEST NOT RECEIVED")
                success = False
        except Exception as e:
            print(f"LOW COMP FAIL ELoop: Failed to reach contr - {e}")

    logging.info(f"POSTED LOW COMP FAIL {dnn_id}")


def return_work_to_client(dnn_id: str, deadline: dt):
    data = {
        "dnn_id": dnn_id,
        "deadline": deadline.timestamp() * 1000
    }

    headers = {
        "Content-Type": "application/json",
    }

    url = f"http://{utils.parse_source_device_id(dnn_id)}:{Constants.REST_PORT}{Constants.RETURN_WORK}"

    success = False
    logging.info(f"RETURNING WORK {dnn_id}")
    while not success:
        try:
            response = requests.post(url, json=data, headers=headers)
            success = True

            if response.status_code != 200:
                logging.info("ERROR REQUEST NOT RECEIVED")
                success = False
        except Exception as e:
            print(f"RETURN WORK ELoop: Failed to reach client - {e}")

    logging.info(f"RETURNED WORK {dnn_id}")


def post_halt_controller(dnn_id: str):
    data = {
        "dnn_id": dnn_id,
    }

    headers = {
        "Content-Type": "application/json",
    }

    url = f"http://{Constants.CONTROLLER_HOST_NAME}:{Constants.CONTROLLER_DEFAULT_PORT}{Constants.POST_HALT_EP}"

    success = False
    logging.info(f"POSTING HALT {dnn_id}")
    while not success:
        try:
            response = requests.post(url, json=data, headers=headers)
            success = True

            if response.status_code != 200:
                logging.info("ERROR REQUEST NOT RECEIVED")
                success = False
        except Exception as e:
            print(f"POST HALT ELoop: Failed to reach contr - {e}")

    logging.info(f"POSTED HALT {dnn_id}")


def post_low_task(start_time: dt, finish_time: dt, dnn_id: str, invoke_preemption: bool):
    data = {
        "dnn_id": dnn_id,
        "finish_time": int(finish_time.timestamp() * 1000),
        "start_time": int(start_time.timestamp() * 1000),
        "request_id": f"{dt.now().timestamp()}",
        "invoke_preemption": bool(invoke_preemption)
    }

    headers = {
        "Content-Type": "application/json",
    }

    url = f"http://{Constants.CONTROLLER_HOST_NAME}:{Constants.CONTROLLER_DEFAULT_PORT}{Constants.POST_LOW_TASK}"

    success = False
    logging.info(f"POSTING LOW COMP DNN {dnn_id}")
    while not success:
        try:
            response = requests.post(url, json=data, headers=headers)
            success = True

            if response.status_code != 200:
                logging.info("ERROR REQUEST NOT RECEIVED")
                success = False
        except Exception as e:
            print(f"POST LOW TASK ELoop: Failed to reach contr - {e}")

    logging.info(f"POSTED LOW COMP DNN {dnn_id}")


def issue_low_comp_update(dnn_id: str, time: dt):
    data = {
        "dnn_id": dnn_id,
        "finish_time": int(dt.now().timestamp() * 1000),
        "type": "low",
        "request_id": f"{dt.now().timestamp()}",
    }

    headers = {
        "Content-Type": "application/json",
    }

    url = f"http://{Constants.CONTROLLER_HOST_NAME}:{Constants.CONTROLLER_DEFAULT_PORT}{Constants.CONTROLLER_STATE_UPDATE}"
    logging.info(f"COMPLETED DNN {data}")
    success = False
    while not success:
        try:
            response = requests.post(url, json=data, headers=headers)
            logging.info(f"CONTROLLER ACK COMP DNN {data['dnn_id']}")
            success = True

            if response.status_code != 200:
                logging.info("ERROR REQUEST NOT RECEIVED")
                success = False
        except Exception as e:
            print(f"ISSUE_LOW_UPDATE ELoop: Failed to reach contr - {e}")

    print(f"DNN RESULT {data}")
    return


def generate_high_comp_request(task_body: dict):

    headers = {
        "Content-Type": "application/json",
    }

    url = f"http://{Constants.CONTROLLER_HOST_NAME}:{Constants.CONTROLLER_DEFAULT_PORT}{Constants.CONTROLLER_HIGH_COMP_ALLOCATION}"

    success = False
    while not success:
        try:
            response = requests.post(url, json=task_body, headers=headers)
            success = True

            if response.status_code != 200:
                logging.info("ERROR REQUEST NOT RECEIVED")
                success = False
        except Exception as e:
            logging.info(f"GENERATE_HIGH_COMP: ELoop: Failed to reach contr - {e}")

    return
