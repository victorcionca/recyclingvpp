import Globals
from inference_engine.utils.DataProcessing import check_if_dnn_halted, check_if_dnn_pruned
from model.OutboundComm import OutboundComm
from datetime import datetime as dt
from enums.OutboundCommTypes import OutboundCommType
from model.NetworkCommModels.TaskForwaring import TaskForwarding
from Constants.Constants import *
import json
import requests


def outbound_comm_loop():
    while True:
        Globals.work_queue_lock.acquire(blocking=True)

        if len(Globals.net_outbound_list) != 0 and Globals.net_outbound_list[0].comm_time <= dt.now():
            comm_item: OutboundComm = Globals.net_outbound_list.pop(0)

            if comm_item.comm_type == OutboundCommType.TASK_FORWARD:
                taskForward(comm_item=comm_item)
            elif comm_item.comm_type == OutboundCommType.TASK_ASSEMBLY:
                assemblyForward(comm_item=comm_item)
            elif comm_item.comm_type == OutboundCommType.STATE_UPDATE:
                stateUpdate(comm_item=comm_item)
            elif comm_item.comm_type == OutboundCommType.DAG_DISRUPTION:
                stateUpdate(comm_item=comm_item)

        Globals.work_queue_lock.release()
    return


# Assumed that lock has been acquired prior to accessing queue
def add_task_to_queue(comm_item: OutboundComm):

    if not check_if_dnn_pruned(comm_item.dnn_id) and not check_if_dnn_halted(dnn_id=comm_item.dnn_id, dnn_version=comm_item.version):
        Globals.net_outbound_list.append(comm_item)
        Globals.net_outbound_list.sort(key=lambda x: x.comm_time)

    return


def dagDisruption(comm_item: OutboundComm):
    if isinstance(comm_item.payload, dict):
        payload: dict = comm_item.payload
        url = f"{CONTROLLER_HOST_NAME}:{CONTROLLER_DEFAULT_PORT}{CONTROLLER_DAG_DISRUPTION}"
        json_obj = json.dumps(payload)
        response = requests.post(url, json=json_obj)
    return


def stateUpdate(comm_item: OutboundComm):
    if isinstance(comm_item.payload, dict):
        payload: dict = comm_item.payload
        url = f"{CONTROLLER_HOST_NAME}:{CONTROLLER_DEFAULT_PORT}{CONTROLLER_STATE_UPDATE}"
        json_obj = json.dumps(payload)
        response = requests.post(url, json=json_obj)
    return


def assemblyForward(comm_item: OutboundComm):
    if isinstance(comm_item.payload, TaskForwarding):
        payload: TaskForwarding = comm_item.payload
        host = payload.high_comp_result.tasks[payload.convidx].assembly_host
        url = f"{host}:{REST_PORT}{TASK_ASSEMBLY}"
        json_obj = json.dumps(payload)
        response = requests.post(url, json=json_obj)
    return


def taskForward(comm_item: OutboundComm):
    if isinstance(comm_item.payload, TaskForwarding):
        payload: TaskForwarding = comm_item.payload
        host = payload.high_comp_result.tasks[payload.convidx].partitioned_tasks[payload.partition_id].allocated_host
        url = f"{host}:{REST_PORT}{TASK_FORWARD}"
        json_obj = json.dumps(payload)
        response = requests.post(url, json=json_obj)
    return


def taskAssembly(comm_item: OutboundComm):
    return
