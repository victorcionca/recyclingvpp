import OutboundComm
from datetime import datetime as dt
import Constants
import requests
import logging


def deadlineViolated(comm_item: OutboundComm.OutboundComm = OutboundComm.OutboundComm()):
    logging.info("Deadline Violation")
    if isinstance(comm_item.payload, dict):
        payload: dict = comm_item.payload
        url = f"http://{Constants.CONTROLLER_HOST_NAME}:{Constants.CONTROLLER_DEFAULT_PORT}{Constants.CONTROLLER_VIOLATED_DEADLINE}"
        payload["request_id"] = f"{dt.now().timestamp()}"
        success = False
        while not success:
            try:    
                requests.post(url, json=payload)
                success = True
            except Exception as e:
                logging.info(f"Outbound: Failed to reach contr - {e}")
    return


def getImage(source_host):
    success = False
    while not success:
        try:
            requests.get(f"http://{source_host}:{Constants.EXPERIMENT_INFERFACE}{Constants.GET_IMAGE}")
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


def PollingRequest(request_counter):
    success = False
    url = f"http://{Constants.CONTROLLER_HOST_NAME}:{Constants.CONTROLLER_DEFAULT_PORT}{Constants.CONTROLLER_HIGH_WORK_REQUEST}"
    body = {"request_counter": request_counter, "request_id": f"{dt.now().timestamp()}"}
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