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
import http.server
import fused_tiled_partitioning as FTP
import numpy as np

from PIL import Image

# TODO - the following must be configured
model_folder = "vgg16_trashnet_conv_blocks"
model_filename = "vgg16_conv_block_{block_idx}.tflite"
import json
import base64
from time import sleep

class InferenceTaskHandler(http.server.BaseHTTPRequestHandler):

    def serialize_numpy(self, array):
        """
        Serialize numpy array into base64 encoded string.
        Returns: base64 encoding and shape of array.
        """
        array_bytes = array.tobytes()
        array64 = base64.encodebytes(array_bytes)
        return array64, array.shape

    def deserialize_numpy(self, array64, shape):
        """
        Deserialize a numpy array that is represented as base64 encoded bytes.
        Assumes original data is float32
        Returns: numpy array.
        """
        array_bytes = base64.decodebytes(array64)
        array = np.frombuffer(array_bytes, dtype=np.float32)
        return array.reshape(shape)

    def handle_load(self, request):
        if "file" not in request:
            # TODO error
            return None
        img = Image.open(request["file"])
        img = img.resize([224, 224])
        img_data = np.asarray(img)
        # Standardise image
        mean = np.mean(img_data, axis=(0,1), keepdims=True)
        std = np.sqrt(((img_data - mean)**2).mean((0,1), keepdims=True))
        img_data = (img_data-mean)/std
        img_data = np.expand_dims(img_data, axis=0)
        # Serialize
        img_data_64, img_shape  = self.serialize_numpy(img_data)
        # Build and return JSON object
        response = {
                "type": "load_result",
                "file": request["file"],
                "data": img_data_64,
                "shape": img_shape
                }
        response_json = json.dumps(response)
        return response_json

    def handle_partition(self, request):
        if "input" not in request or\
                "shape" not in request or\
                "convblockidx" not in request or\
                "partitionspecs" not in request:
            # TODO error
            return None
        # Extract the input from the request
        input_data = self.deserialize_numpy(request["input"], request["shape"])
        # Extract the partition specs
        partN = request["partitionspecs"]["N"]
        partM = request["partitionspecs"]["M"]
        convblockidx = request["convblockidx"]
        # Get the conv block metadata
        conv_block_metadata = pickle.load(open(os.path.join(model_folder,
                                            "conv_block_metadata.pickle"), 'rb'))
        # Get the partition details
        part_details = FTP.get_partition_details(input_data,
                                                conv_block_metadata[convblockidx],
                                                partN, partM)
        # For each partition, get the input data
        partitions = []
        for p in part_details:
            part_data = FTP.get_partition_data(p, input_data)
            part_data_64, _ = self.serialize_numpy(part_data)
            partitions.append({
                "position": { "N":p.Nidx, "M":p.Midx, "x":top_left_x, "y":top_left_y},
                "data": part_data_64,
                "shape": part_data.shape})

        # Build and return json
        response = {
                "type": "partition_result",
                "tiles": partitions
                }
        response_json = json.dumps(response)
        return response_json


    def handle_process(self, request):
        # Validate the request
        if "input" not in request or\
                "shape" not in request or\
                "convblockidx" not in request or\
                "core" not in request:
            # TODO error
            return None
        # Forks a new process
        childpid = os.fork()
        if not childpid:
            # This is the child
            os.sched_setaffinity(0, [cpu_core])
            cpu_core = request["core"]
            input_shape = request["shape"]
            input_data = self.deserialize_numpy(request["input"], input_shape)
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
            output_64 = self.serialize_numpy(output)
            # Build and return request
            response = {
                    "type": "process_result",
                    "data": output_64,
                    "shape": output.shape
                    }
            response_json = json.dumps(response)
            return response_json
        else:
            print(f"Child process {childpid} started")

    def handle_assemble(self, request):
        # Sanitize request
        if "tiles" not in request or\
                "convblockidx" not in request:
            # TODO error
            return None
        # Get the conv block metadata
        conv_block_metadata = pickle.load(open(os.path.join(model_folder,
                                            "conv_block_metadata.pickle"), 'rb'))
        model = conv_block_metadata["convblockidx"]
        num_layers = len(model)
        conv_kernel_size = int(np.floor(model[0]["kernel_shape"][0]/2))
        # Initialize the output matrix with the shape from the layer metadata
        output_shape = model[-1]["output_shape"]
        output = np.zeros([1]+output_shape[1:])
        # Load the partition data into the output matrix, considering overlaps
        for tile in request["tiles"]:
            position = tile["position"]
            top_x_offset,top_y_offset,bot_x_offset,bot_y_offset = 0,0,0,0
            top_left_x = position["x"]
            top_left_y = position["y"]
            bot_right_x = top_left_x + tile["shape"][2]
            bot_right_y = top_left_y + tile["shape"][1]
            if top_left_x > 0: top_x_offset += num_layers*conv_kernel_size
            if top_left_y > 0: top_y_offset += num_layers*conv_kernel_size
            if bottom_right_x < output.shape[1]-1: bot_x_offset -= num_layers*conv_kernel_size
            if bottom_right_y < output.shape[2]-1: bot_y_offset -= num_layers*conv_kernel_size
            output[:,
                   top_left_x+top_x_offset:bottom_right_x+bot_x_offset+1,
                   top_left_y+top_y_offset:bottom_right_y+bot_y_offset+1,:] = \
                    output_part[:,
                                top_x_offset:width()+bot_x_offset,
                                top_y_offset:height()+bot_y_offset,:]
        # Encode response with output and return
        output_64, _ = self.serialize_numpy(output)
        response = {
                "type": "assemble_result",
                "data": output_64,
                "shape": output_shape
                }
        response_json = json.dumps(response)
        return response_json

    def do_POST(self):
        handlers = {
            "load": self.handle_load,
            "partition": self.handle_partition,
            "process": self.handle_process,
            "assemble": self.handle_assemble
            }
        # Process the request data and extract the input, target core, etc.
        request_str = self.requestline
        request_body = self.rfile.read(int(self.headers['Content-Length']))
        # Try to convert to json
        json_request = None
        try:
            json_request = json.loads(request_body)
        except json.JSONDecodeError:
            print(f"Received request was not json: {request_str}")
            return
        print(json_request)
        # Process based on type
        if "type" not in json_request or json_request["type"] not in handlers:
            # TODO error
            return
        # Delegate processing
        response_json = handlers[json_request["type"]](json_request)

if __name__ == '__main__':
    with http.server.HTTPServer(("localhost", 9999), InferenceTaskHandler) as server:
        print("Serving")
        server.serve_forever()
