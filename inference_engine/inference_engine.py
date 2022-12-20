"""
Inference engine for fused tiled partitioning (FTP).

Works on blocks of convolutional layers, splitting the input into a grid.

Implements a master-worker architecture:
    * the master receives inference tasks over a socket
    * each inference task is then executed in a sub-process which is pinned to
    a specific core.

Inference tasks consist of:
    * id of the convolutional block
    * input data
    * size of the input (wxh)
    * IP address of node where result should be sent.

TODO:
    * dense layers at the end.
"""

from time import time
import pickle
import os
from random import shuffle
import fused_tiled_partitioning as FTP
import numpy as np
from PIL import Image
import threading

# TODO - the following must be configured
model_folder = "../../models/vgg16_trashnet_conv_blocks"
model_filename = "vgg16_conv_block_{block_idx}.tflite"
from time import sleep
import multiprocessing
import signal

import logging
import tflite_runtime.interpreter as tflite
import Globals

def serialize_numpy(self, array):
    """
    Serialize numpy array into base64 encoded string.
    Returns: base64 encoding and shape of array.
    """
    array_bytes = array.tobytes()
    array64 = base64.encodebytes(array_bytes)
    return array64, array.shape

def deserialize_numpy(self, array_bytes, shape):
    """
    Deserialize a numpy array that is represented as base64 encoded bytes.
    Assumes original data is float32
    Returns: numpy array.
    """
    array = np.frombuffer(array_bytes, dtype=np.float32)
    return array.reshape(shape)

def LoadImage(self, request):
    if "filename" not in request:
        # TODO signal error
        return None
    img = Image.open(request["filename"])
    img = img.resize([224, 224])
    img_data = np.asarray(img, dtype=np.float32)
    # Standardise image
    mean = np.mean(img_data, axis=(0,1), keepdims=True)
    std = np.sqrt(((img_data - mean)**2).mean((0,1), keepdims=True))
    img_data = (img_data-mean)/std
    img_data = np.expand_dims(img_data, axis=0)
    # Serialize
    img_data_bytes = img_data.tobytes()
    # Build and return JSON object
    response = dict()
    response["filename"] = request["filename"]
    response["data"] = img_data_bytes
    response["shape"] = list(img_data.shape)
    response["TaskID"] = request["TaskID"]
    return response

def PartitionData(self, request):
    reqd_fields = ["data", "shape", "N", "M", "convblockidx", "TaskID"]
    for f in reqd_fields:
        if f not in request:
            # TODO signal error
            return None
    # Extract the input from the request
    input_data = self.deserialize_numpy(request["data"], request["shape"])
    # Extract the partition specs
    partN = request["N"]
    partM = request["M"]
    convblockidx = request["convblockidx"]
    # Get the conv block metadata
    conv_block_metadata = pickle.load(open(os.path.join(model_folder,
                                        "conv_block_metadata.pickle"), 'rb'))
    # Get the partition details
    part_details = FTP.get_partition_details(input_data,
                                            conv_block_metadata[convblockidx],
                                            partN, partM)
    response = dict()
    response["TaskID"] = request["TaskID"]
    response["Tiles"] = []
    # For each partition, get the input data
    for p in part_details:
        tile = dict()
        part_data = FTP.get_partition_data(p, input_data)
        tile["data"] = part_data.tobytes()
        tile["shape"] = list(part_data.shape)
        tile["Nidx"] = p.Nidx
        tile["Midx"] = p.Midx
        tile["top_x"] = p.top_left_x
        tile["bot_x"] = p.top_left_x + part_data.shape[2] - 1
        tile["top_y"] = p.top_left_y
        tile["bot_y"] = p.top_left_y + part_data.shape[1] - 1
        response["Tiles"].append(tile)
    return response

def AssembleData(self, request):
    reqd_fields = ["TaskID", "convblockidx", "Tiles"]
    for f in reqd_fields:
        if f not in request:
            # TODO signal error
            return None
    # Get the conv block metadata
    conv_block_metadata = pickle.load(open(os.path.join(model_folder,
                                        "conv_block_metadata.pickle"), 'rb'))
    model = conv_block_metadata[request["convblockidx"]]
    num_layers = len(model)
    conv_kernel_size = int(np.floor(model[0]["kernel_shape"][0]/2))
    # Initialize the output matrix with the shape from the layer metadata
    output_shape = model[-1]["output_shape"]
    output = np.zeros((1,*output_shape[1:]), dtype=np.float32)
    # Load the partition data into the output matrix, considering overlaps
    for tile in request["Tiles"]:
        top_x_offset,top_y_offset,bot_x_offset,bot_y_offset = 0,0,0,0
        top_left_x = tile["top_x"]
        top_left_y = tile["top_y"]
        print(f"Tile at {top_left_x} {top_left_y}")
        bot_right_x = tile["bot_x"]
        bot_right_y = tile["bot_y"]
        if top_left_x > 0: top_x_offset += num_layers*conv_kernel_size
        if top_left_y > 0: top_y_offset += num_layers*conv_kernel_size
        if bot_right_x < output.shape[1]-1: bot_x_offset -= num_layers*conv_kernel_size
        if bot_right_y < output.shape[2]-1: bot_y_offset -= num_layers*conv_kernel_size
        # Restore tile data to proper shape
        tile_data = self.deserialize_numpy(tile["data"], tile["shape"])
        #print((position.x, position.y), (bot_right_x, bot_right_y), top_x_offset,top_y_offset,bot_x_offset,bot_y_offset, tile.shape)
        output[:,
               top_left_y+top_y_offset:bot_right_y+bot_y_offset+1,
               top_left_x+top_x_offset:bot_right_x+bot_x_offset+1,:] = \
                tile_data[:,
                            top_y_offset:tile["shape"][2]+bot_y_offset,     # TODO should be shape[1] instead
                            top_x_offset:tile["shape"][1]+bot_x_offset,:]   # TODO should be shape[2] instead
    # Encode response with output and return
    output_bytes = output.tobytes()
    response = dict()
    response["TaskID"] = request["TaskID"]
    response["data"] = output_bytes
    response["shape"] = list(output.shape)
    return response

class InferenceHandler(threading.Thread):

    def __init__(self):
        self.running = False
        self.work_queue = Globals.work_queue
        self.results_queue = Globals.results_queue

    def ProcessData(self, request):
        # Validate the request
        reqd_fields = ["data", "shape", "convblockidx", "core", "TaskID"]
        for f in reqd_fields:
            if f not in request:
            # TODO signal error
            return None
        # Fork a new process
        childpid = os.fork()
        if not childpid:
            # This is the child
            os.sched_setaffinity(0, [request["core"]])
            input_shape = request["shape"]
            input_data = self.deserialize_numpy(request["data"], input_shape)
            convblockidx = request["convblockidx"]
            # Run the processing    -------------------------------
            # Load and instantiate the tflite model
            interpreter = tflite.Interpreter(os.path.join(model_folder,
                                    model_filename.format(block_idx=convblockidx)))
            # Update the size of the tensor to that of the partition
            interpreter.resize_tensor_input(0, input_data.shape, strict=True)
            interpreter.allocate_tensors()
            # Get input and output tensors.
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            # Set the input data
            interpreter.set_tensor(input_details[0]['index'], input_data)
            # Invoke
            interpreter.invoke()
            # Get the response
            output = interpreter.get_tensor(output_details[0]['index'])
            output_bytes = output.tobytes()
            # Build request
            response = dict()
            response["TaskID"] = request["TaskID"]
            response["data"] = output_bytes
            response["shape"] = list(output.shape)
            # Insert request into the results queue
            self.results_queue.put(response)

    def run(self):
        """
        Read tasks arriving in the work queue and process them accordingly
        """
        self.running = True
        while self.running:
            task = self.work_queue.get()
            if task['type'] == "halt":
                # Halt all currently running children
                children = multiprocessing.active_children()
                for ch in children:
                    os.kill(signal.SIGKILL, ch, /)
            elif task['type'] == "task":
                self.ProcessData(task)

if __name__ == '__main__':
    aid_server = Process(target=aid_server)
    aid_server.start()
    inf_core1 = Process(target=inference_server, args=(1,))
    inf_core1.start()
    inf_core2 = Process(target=inference_server, args=(2,))
    inf_core2.start()
    inf_core3 = Process(target=inference_server, args=(3,))
    inf_core3.start()
    inf_core4 = Process(target=inference_server, args=(4,))
    inf_core4.start()

