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

# TODO - the following must be configured
model_folder = "../../models/vgg16_trashnet_conv_blocks"
model_filename = "vgg16_conv_block_{block_idx}.tflite"
from time import sleep

import grpc
import requests_pb2_grpc as inference_grpc
import requests_pb2 as inference_pb
import logging
import tflite_runtime.interpreter as tflite

class InferenceAidHandler(inference_grpc.InferenceAidServicer):

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

    def LoadImage(self, request, context):
        # TODO - should we perform request validation?
        img = Image.open(request.file)
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
        response = inference_pb.LoadResponse()
        response.file = request.file
        response.data = img_data_bytes
        response.shape.extend(img_data.shape)
        return response

    def PartitionData(self, request, context):
        # Extract the input from the request
        input_data = self.deserialize_numpy(request.data, request.shape)
        # Extract the partition specs
        partN = request.partitionSpecs.N
        partM = request.partitionSpecs.M
        convblockidx = request.convblockidx
        # Get the conv block metadata
        conv_block_metadata = pickle.load(open(os.path.join(model_folder,
                                            "conv_block_metadata.pickle"), 'rb'))
        # Get the partition details
        part_details = FTP.get_partition_details(input_data,
                                                conv_block_metadata[convblockidx],
                                                partN, partM)
        response = inference_pb.PartitionResponse()
        # For each partition, get the input data
        for p in part_details:
            tile = inference_pb.Partition()
            part_data = FTP.get_partition_data(p, input_data)
            tile.data = part_data.tobytes()
            tile.shape.extend(part_data.shape)
            tile.position.N = p.Nidx
            tile.position.M = p.Midx
            tile.position.x = p.top_left_x
            tile.position.y = p.top_left_y
            response.tiles.append(tile)
        return response

    def AssembleData(self, request, context):
        # Get the conv block metadata
        conv_block_metadata = pickle.load(open(os.path.join(model_folder,
                                            "conv_block_metadata.pickle"), 'rb'))
        model = conv_block_metadata[request.convblockidx]
        num_layers = len(model)
        conv_kernel_size = int(np.floor(model[0]["kernel_shape"][0]/2))
        # Initialize the output matrix with the shape from the layer metadata
        output_shape = model[-1]["output_shape"]
        output = np.zeros((1,*output_shape[1:]), dtype=np.float32)
        # Load the partition data into the output matrix, considering overlaps
        for tile in request.tiles:
            position = tile.position
            top_x_offset,top_y_offset,bot_x_offset,bot_y_offset = 0,0,0,0
            top_left_x = position.x
            top_left_y = position.y
            print(f"Tile at {top_left_x} {top_left_y}")
            bot_right_x = top_left_x + tile.shape[2]-1
            bot_right_y = top_left_y + tile.shape[1]-1
            if top_left_x > 0: top_x_offset += num_layers*conv_kernel_size
            if top_left_y > 0: top_y_offset += num_layers*conv_kernel_size
            if bot_right_x < output.shape[1]-1: bot_x_offset -= num_layers*conv_kernel_size
            if bot_right_y < output.shape[2]-1: bot_y_offset -= num_layers*conv_kernel_size
            # Restore tile data to proper shape
            tile_data = self.deserialize_numpy(tile.data, tile.shape)
            print((position.x, position.y), (bot_right_x, bot_right_y), top_x_offset,top_y_offset,bot_x_offset,bot_y_offset, tile.shape)
            output[:,
                   top_left_y+top_y_offset:bot_right_y+bot_y_offset+1,
                   top_left_x+top_x_offset:bot_right_x+bot_x_offset+1,:] = \
                    tile_data[:,
                                top_y_offset:tile.shape[2]+bot_y_offset,
                                top_x_offset:tile.shape[1]+bot_x_offset,:]
        # Encode response with output and return
        output_bytes = output.tobytes()
        response = inference_pb.AssembleResponse()
        response.data = output_bytes
        response.shape.extend(output.shape)
        return response

class InferenceTaskHandler(inference_grpc.InferenceServicer):

    def __init__(self, core):
        os.sched_setaffinity(0, [core])

    def deserialize_numpy(self, array_bytes, shape):
        """
        Deserialize a numpy array that is represented as base64 encoded bytes.
        Assumes original data is float32
        Returns: numpy array.
        """
        array = np.frombuffer(array_bytes, dtype=np.float32)
        return array.reshape(shape)

    def ProcessData(self, request, context):
        input_shape = request.shape
        input_data = self.deserialize_numpy(request.data, input_shape)
        convblockidx = request.convblockidx
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
        # Build and return request
        response = inference_pb.ProcessResponse()
        response.data = output_bytes
        response.shape.extend(output.shape)
        return response

from concurrent import futures
def aid_server():
    options = [('grpc.max_send_message_length', 100*1024*1024),('grpc.max_receive_message_length', 100*1024*1024)]
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10), options=options)
    inference_grpc.add_InferenceAidServicer_to_server(InferenceAidHandler(), server)
    server.add_insecure_port('[::]:8000')
    logging.basicConfig()
    logging.info("Main server listening")
    server.start()
    server.wait_for_termination()

def inference_server(core):
    options = [('grpc.max_send_message_length', 100*1024*1024),('grpc.max_receive_message_length', 100*1024*1024)]
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10), options=options)
    inference_grpc.add_InferenceServicer_to_server(InferenceTaskHandler(core), server)
    server.add_insecure_port(f'[::]:{8000+core}')
    logging.basicConfig()
    logging.info(f"Core {core} processor listening")
    server.start()
    server.wait_for_termination()

from multiprocessing import Process

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

