import Globals
import DataProcessing
import OutboundComm
from datetime import datetime as dt
import OutboundCommTypes
import TaskForwarding
import Constants
import json
import requests
import threading


def outbound_comm_loop():
    while True:
        Globals.work_queue_lock.acquire(blocking=True)

        if len(Globals.net_outbound_list) != 0 and Globals.net_outbound_list[0].comm_time <= dt.now():
            comm_item: OutboundComm.OutboundComm = Globals.net_outbound_list.pop(
                0)
            function = None
            if comm_item.comm_type == OutboundCommTypes.OutboundCommType.TASK_FORWARD:
                function = taskForward
            elif comm_item.comm_type == OutboundCommTypes.OutboundCommType.TASK_ASSEMBLY:
                function = assemblyForward
            elif comm_item.comm_type == OutboundCommTypes.OutboundCommType.STATE_UPDATE:
                function = stateUpdate
            elif comm_item.comm_type == OutboundCommTypes.OutboundCommType.DAG_DISRUPTION:
                function = dagDisruption
            threading.Thread(target=function, kwargs={'comm_item': comm_item}).start()

        Globals.work_queue_lock.release()
    return


# Assumed that lock has been acquired prior to accessing queue
def add_task_to_queue(comm_item: OutboundComm.OutboundComm = OutboundComm.OutboundComm()):

    if not DataProcessing.check_if_dnn_pruned(comm_item.dnn_id) and not DataProcessing.check_if_dnn_halted(dnn_id=comm_item.dnn_id, dnn_version=comm_item.version):
        Globals.net_outbound_list.append(comm_item)
        Globals.net_outbound_list.sort(key=lambda x: x.comm_time)

    return


def dagDisruption(comm_item: OutboundComm.OutboundComm = OutboundComm.OutboundComm()):
    if isinstance(comm_item.payload, dict):
        payload: dict = comm_item.payload
        url = f"http://{Constants.CONTROLLER_HOST_NAME}:{Constants.CONTROLLER_DEFAULT_PORT}{Constants.CONTROLLER_DAG_DISRUPTION}"
        requests.post(url, json=payload)
    return


def stateUpdate(comm_item: OutboundComm.OutboundComm = OutboundComm.OutboundComm()):
    if isinstance(comm_item.payload, dict):
        payload: dict = comm_item.payload
        url = f"http://{Constants.CONTROLLER_HOST_NAME}:{Constants.CONTROLLER_DEFAULT_PORT}{Constants.CONTROLLER_STATE_UPDATE}"
        requests.post(url, json=payload)
    return


def assemblyForward(comm_item: OutboundComm.OutboundComm = OutboundComm.OutboundComm()):
    if isinstance(comm_item.payload, TaskForwarding.TaskForwarding):
        comms_start = dt.now()
        payload: TaskForwarding.TaskForwarding = comm_item.payload
        payload.assembly_upload_start = comms_start
        host = payload.high_comp_result.tasks[payload.convidx].assembly_host
        url = f"http://{host}:{Constants.REST_PORT}{Constants.TASK_ASSEMBLY}"
        result_object = payload.task_forwarding_to_dict()
        json_obj = json.dumps(result_object)
        requests.post(url, json=json_obj)
    return


def taskForward(comm_item: OutboundComm.OutboundComm = OutboundComm.OutboundComm()):
    if isinstance(comm_item.payload, TaskForwarding.TaskForwarding):
        payload: TaskForwarding.TaskForwarding = comm_item.payload
        host = payload.high_comp_result.tasks[payload.convidx].partitioned_tasks[payload.partition_id].allocated_host
        url = f"http://{host}:{Constants.REST_PORT}{Constants.TASK_FORWARD}"
        result_dict = payload.task_forwarding_to_dict()
        json_obj = json.dumps(result_dict)
        requests.post(url, json=json_obj)
    return