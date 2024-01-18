import OutboundComm
from datetime import datetime as dt
import Constants
import requests
import logging
import Globals


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
                logging.info(f"Outbound: Failed to reach contr - {e}")
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
                logging.info(f"Outbound: Failed to reach contr")
    logging.info(f"State_update success {url}")
    return


def PollingRequest(request_counter, local_capacity):
    success = False
    url = f"http://{Constants.CONTROLLER_HOST_NAME}:{Constants.CONTROLLER_DEFAULT_PORT}{Constants.CONTROLLER_HIGH_WORK_REQUEST}"
    body = {"request_counter": request_counter, "capacity": local_capacity, "request_id": f"{dt.now().timestamp()}"}
    headers = {
        "Content-Type": "application/json",
    }
    while not success:
        try:
            response = requests.post(url, json=body, headers=headers)

            success = True
            if response.status_code != 200:
                logging.info("ERROR REQUEST NOT RECEIVED")
                success = False
            else:
                logging.info("WORK_REQUEST SUCCESS")
        except Exception as e:
            logging.info(f"ELoop: Failed to reach contr - {e}")


def issue_low_comp_update(dnn_id: str, time: dt):
    data = {
        "dnn_id": dnn_id,
        "finish_time": int(dt.now().timestamp() * 1000),
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
            print(f"ELoop: Failed to reach contr - {e}")

    print(f"DNN RESULT {data}")
    return


def generate_low_comp_request(deadline: dt, dnn_id: int):
    data = {
        "dnn_id": str(dnn_id),
        "deadline": int(deadline.timestamp() * 1000),
        "request_id": f"{dt.now().timestamp()}",
    }

    headers = {
        "Content-Type": "application/json",
    }

    url = f"http://{Constants.CONTROLLER_HOST_NAME}:{Constants.CONTROLLER_DEFAULT_PORT}{Constants.CONTROLLER_LOW_COMP_ALLOCATION}"

    success = False
    logging.info(f"BEGINNING HIGH COMP OFFLOAD REQ")

    if Globals.local_capacity < 4:
        Globals.local_capacity += 1
    while not success:
        try:
            response = requests.post(url, json=data, headers=headers)
            success = True
        
            if response.status_code != 200:
                logging.info("ERROR REQUEST NOT RECEIVED")
                success = False
        except Exception as e:
            logging.info(f"ELoop: Failed to reach contr - {e}")

    logging.info(f"BEGINNING HIGH COMP OFFLOAD REQ SUCCESS")
    return


def generate_high_comp_request(deadline: dt, dnn_id: int, task_count: int):
    data = {
        "dnn_id": str(dnn_id),
        "deadline": int(deadline.timestamp() * 1000),
        "task_count": task_count,
        "request_id": f"{dt.now().timestamp()}",
    }

    headers = {
        "Content-Type": "application/json",
    }

    url = f"http://{Constants.CONTROLLER_HOST_NAME}:{Constants.CONTROLLER_DEFAULT_PORT}{Constants.CONTROLLER_HIGH_COMP_ALLOCATION}"

    success = False
    while not success:
        try:
            response = requests.post(url, json=data, headers=headers)
            success = True

            if response.status_code != 200:
                logging.info("ERROR REQUEST NOT RECEIVED")
                success = False
        except Exception as e:
            logging.info(f"ELoop: Failed to reach contr - {e}")

    return
