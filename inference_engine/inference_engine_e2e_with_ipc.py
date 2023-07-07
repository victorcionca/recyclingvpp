"""
Inference engine for end-to-end tiled partitioning (FTP).

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

import pickle
import os
from random import shuffle, randint, random
import fused_tiled_partitioning as FTP
import numpy as np
import base64
import json
from PIL import Image
import threading
import Globals

# TODO - the following must be configured
model_folder = "/home/pi/recyclingvpp/models/"
model_filename = "vgg16_conv_block_{block_idx}.tflite"
maxpool_filename = "vgg16_maxpool_{block_idx}.tflite"
from time import sleep, time
from multiprocessing import Process, Queue, Lock, Pipe
from multiprocessing.connection import wait
import signal
from queue import Queue
Queue()
import logging
import tflite_runtime.interpreter as tflite

logging.basicConfig(level=logging.WARNING)
def serialize_numpy(array):
    """
    Serialize numpy array into base64 encoded string.
    Returns: base64 encoding and shape of array.
    """
    array_bytes = array.tobytes()
    array64 = base64.encodebytes(array_bytes)
    return array64

def deserialize_numpy64(array, shape):
    """
    Deserialize a numpy array that is represented as base64 encoded bytes.
    Assumes original data is float32
    Returns: numpy array.
    """
    array_bytes = base64.decodebytes(array)
    array = np.frombuffer(array_bytes, dtype=np.float32)
    return array.reshape(shape)

def deserialize_numpy(array_bytes, shape):
    """
    Deserialize a numpy array that is represented as bytes.
    Assumes original data is float32
    Returns: numpy array.
    """
    array = np.frombuffer(array_bytes, dtype=np.float32)
    return array.reshape(shape)

def LoadImage(request, taskid):
    #if "filename" not in request:
    #    # TODO signal error
    #    return None
    #img = Image.open(request["filename"])
    #img = img.resize([224, 224])
    #img_data = np.asarray(img, dtype=np.float32)
    ## Standardise image
    #mean = np.mean(img_data, axis=(0,1), keepdims=True)
    #std = np.sqrt(((img_data - mean)**2).mean((0,1), keepdims=True))
    #img_data = (img_data-mean)/std
    #img_data = np.expand_dims(img_data, axis=0)
    inputs = pickle.load(open(os.path.join(model_folder, "conv_block_inputs.pickle"), 'rb'))
    img_data = inputs[0]
    # Serialize
    img_data_bytes = img_data.tobytes()
    # Build and return JSON object
    response = dict()
    response["filename"] = "inputs"
    response["data"] = img_data_bytes
    response["shape"] = list(img_data.shape)
    response["TaskID"] = taskid
    return response

# Load the metadata and create the flat list for processing
metadata_list = pickle.load(open(os.path.join(model_folder,
                                        "conv_block_metadata.pickle"), 'rb'))

# For experiments
#request_lock = threading.Lock()
response_queue = Queue()


class PartitionProcess(threading.Thread):
    # Generate the pipes for processing and results
    # Create a pipe for each core
    # processing_conns is a list of (r, w) pipes
    processing_conns = None
    results_conns = None
    def __init__(self, request):
        """
        Creates a Partition and Process manager to process an incoming
        request.
        The manager will follow the request through all its blocks.
        """
        super().__init__()
        # Process the fields of the request
        reqd_fields = ["data", "shape", "N", "M", "cores", "TaskID"]
        for f in reqd_fields:
            if f not in request:
                # TODO raise ValueError
                return None
        # Extract the input from the request
        self.input_data = deserialize_numpy(request["data"], request["shape"])
        # Extract the partition specs
        self.partN = request["N"]
        self.partM = request["M"]
        self.taskid = request["TaskID"]

        self.processing_conns = {core: Pipe() for core in request["cores"]}
        self.results_conns = {core: Pipe() for core in request["cores"]}
        # Setup the inference processors on the required cores
        self.handlers = []
        self.handler_pipes = []
        self.cores = request['cores']
        for idx, core in enumerate(request["cores"]):
            handler = InferenceHandler(core, self.partN*self.partM, idx, self.processing_conns[core], self.results_conns[core])
            handler.start()
            self.handlers.append(handler)
            self.handler_pipes.append(self.results_conns[core])
        self.halt_event = threading.Event()

    def halt(self):
        """
        Halts an ongoing DNN. Stops the processing of the convolutional blocks
        and kills all the subprocesses involved.

        The majority of processing time is spent waiting for the inference 
        subprocesses. Therefore the halt operation will first kill the subprocesses
        and then must ensure the PartitionProcess thread finishes gracefully.
        """
        self.halt_event.set()
        # Kill the subprocesses
        for handler in self.handlers:
            handler.kill()
            handler.join()

    def run(self):
        # Go through the chain of models
        logging.debug(f"Process {self.taskid}")
        output = self.input_data
        prev_tile_shapes = [None for _ in range(self.partN*self.partM)]
        # This only goes through the conv blocks as the maxpool layers
        # are processed by the InferenceProcessors
        for block_idx in range(1,5+1):
            logging.debug(f"Process block {block_idx}")
            # Generate the tiles for this block
            tiles = FTP.FTP(metadata_list[block_idx], self.partN, self.partM)
            tiles = [t for tlist in tiles[0] for t in tlist]
            # Package the tiles into requests and dispatch to processors
            start = time()
            for idx, tile in enumerate(tiles):
                # Generate tile processing requests
                tile_req = dict()
                tile_data = output[:,
                            tile.top_left_y:tile.bottom_right_y+1,
                            tile.top_left_x:tile.bottom_right_x+1,:]
                if prev_tile_shapes[idx] == None or block_idx == 5:
                    logging.debug(f"Sending full tile {tile_data.shape}")
                    tile_req["data"] = {"data":tile_data, "type":"new"}
                else:
                    new_columns = None
                    new_rows = None
                    column_position = None
                    row_position = None
                    logging.debug(f"Previous tile {prev_tile_shapes[idx]}, current tile {tile}")
                    logging.debug(f"Current tile: {tile.top_left_x, tile.top_left_y, tile.bottom_right_x, tile.bottom_right_y}")
                    # What we add on x axis (additional columns)
                    if tile.top_left_x < prev_tile_shapes[idx]['top_x']:
                        new_columns = output[:,
                                prev_tile_shapes[idx]['top_y']:prev_tile_shapes[idx]['bot_y']+1,
                                tile.top_left_x:prev_tile_shapes[idx]['top_x'], :]
                        column_position = 'before'
                    if tile.bottom_right_x > prev_tile_shapes[idx]['bot_x']:
                        new_columns = output[:,
                                prev_tile_shapes[idx]['top_y']:prev_tile_shapes[idx]['bot_y']+1,
                                prev_tile_shapes[idx]['bot_x']+1:tile.bottom_right_x+1, :]
                        column_position = 'after'
                    # What we add on y axis (additional rows)
                    if tile.top_left_y < prev_tile_shapes[idx]['top_y']:
                        new_rows = output[:,
                                tile.top_left_y:prev_tile_shapes[idx]['top_y'],
                                tile.top_left_x:tile.bottom_right_x+1, :]
                        row_position = 'before'
                    if tile.bottom_right_y > prev_tile_shapes[idx]['bot_y']:
                        new_rows = output[:,
                                prev_tile_shapes[idx]['bot_y']+1:tile.bottom_right_y+1,
                                tile.top_left_x:tile.bottom_right_x+1, :]
                        row_position = 'after'
                    if column_position == None and row_position == None:
                        logging.debug(f"Tile is not changing")
                        tile_req["data"] = {"type": "same"}
                    else:
                        tile_req["data"] = {"type":"offset",
                                        "new_columns": new_columns, "column_position": column_position,
                                        "new_rows": new_rows, "row_position": row_position} 
                        logging.debug(f"Sending columns {new_columns.shape if column_position else ''} {column_position} and rows {new_rows.shape if row_position else ''} {row_position}")
                tile_req["shape"] = tile_data.shape
                tile_req['convblockidx'] = block_idx
                tile_req["tile_details"] = dict()
                tile_req["tile_details"]["top_x"] = tile.top_left_x
                tile_req["tile_details"]["top_y"] = tile.top_left_y
                tile_req["tile_details"]["bot_x"] = tile.bottom_right_x
                tile_req["tile_details"]["bot_y"] = tile.bottom_right_y
                tile_req["tile_details"]["Nidx"] = int(np.floor(idx/self.partN))
                tile_req["tile_details"]["Midx"] = idx % self.partM
                tile_req["main_input"] = dict()
                block_output_shape = metadata_list[block_idx*10][-1]['output_shape']
                tile_req["main_input"]["width"] = output.shape[2]
                tile_req["main_input"]["height"] = output.shape[1]
                #tile_req["main_input"]["width"] = block_output_shape[2]
                #tile_req["main_input"]["height"] = block_output_shape[1]
                tile_req["TaskID"] = self.taskid
                # Tell the processor the size of the edges of the tile to return
                # This is equal to num_conv_layers*
                # Feed the tiles into the processing queue of the proper core
                logging.info(f"{time()}: Submit tile {idx} to core")
                self.processing_conns[self.cores[idx]][1].send_bytes(pickle.dumps(tile_req))
            # Wait for all the tiles to be processed
            tile_resp = []
            readers = [r for (r,w) in self.handler_pipes]
            while len(tile_resp) < self.partN*self.partM:
                if self.halt_event.is_set():
                    return
                for r in wait(readers, timeout=1):
                    tile_resp_bytes = r.recv_bytes()
                    if len(tile_resp_bytes) == 0: continue
                    logging.info(f"{time()}: Received tile response {len(tile_resp_bytes)} bytes. Readers: {len(readers)}")
                    # TODO filter task ID
                    if self.halt_event.is_set():
                        return
                    tile_resp.append(pickle.loads(tile_resp_bytes))
                    readers.remove(r)
            if self.halt_event.is_set():
                return
            # Assemble
            output_shape = metadata_list[block_idx*10][-1]['output_shape']
            logging.info(f"{time()}: Assembling block {block_idx} into {output_shape}")
            output = np.zeros((1, *output_shape[1:]), dtype=np.float32)
            # Sort tiles in order of Nidx*N+Midx
            sorted_tiles = sorted(tile_resp,
                          key=lambda t: t["tile_details"]["Nidx"]*self.partN+t["tile_details"]["Midx"])
            # Assemble in grid format
            crt_x = 0
            crt_y = 0
            for tidx, tile in enumerate(sorted_tiles):
                tile_data = tile["data"]
                #if metadata_list[block_idx][-1]['layer_type'] == 'maxpool':
                output[:,
                        crt_y:crt_y+tile["shape"][1],
                        crt_x:crt_x+tile["shape"][2],:] = tile_data
                prev_tile_shapes[tidx] = {
                        'top_x': crt_x, 'top_y': crt_y,
                        'bot_x': crt_x+tile["shape"][2]-1,
                        'bot_y': crt_y+tile["shape"][1]-1}
                if tidx % self.partM == self.partM - 1:
                    crt_y += tile["shape"][1]
                    crt_x = 0
                else:
                    crt_x += tile["shape"][2]
        logging.debug(f"Finished processing task {self.taskid}. Output shape {output.shape}") 
        # Destroy the processors
        for handler in self.handlers:
            handler.kill()
            handler.join()
        # Indicate that we have finished processing a request
        Globals.results_queue.put({"TaskID": self.taskid})


class InferenceHandler(Process):
    """
    Spawns an inference processor on a specific core.
    This will take requests from the processing_queue as they arrive, process
    them and put the results into the results queue.
    """

    processing_conn = None
    result_conn = None
    

    def __init__(self, core, num_tiles, tile_index, processing_pipe, result_pipe):
        """
        Inference processor, processes a single partition end-to-end.

        Parameters
        core        -- core id on the CPU
        num_tiles   -- total number of tiles (partitions) for this task
        tile_index  -- which tile is handled by this processor.
        """
        super().__init__()
        self.processing_conn = processing_pipe
        self.result_conn = result_pipe
        self.running = False
        self.core = core
        self.num_tiles = num_tiles
        self.tile_index = tile_index
        # Load the models and the metadata
        # Create the chain of models
        self.model_list = {}
        self.metadata_list = metadata_list
        # Load the block input shapes
        if self.num_tiles == 4:
            self.output_shapes = pickle.load(open(os.path.join(model_folder,
                                      "e2e_ftp_with_ipc_2x2_shapes.pickle"), 'rb'))
        elif self.num_tiles == 2:
            self.output_shapes = pickle.load(open(os.path.join(model_folder,
                                      "e2e_ftp_with_ipc_1x2_shapes.pickle"), 'rb'))
        # Preload the models and the metadata, resize the tensor inputs
        for block_idx in range(1,5+1):
            block_model = tflite.Interpreter(os.path.join(model_folder,
                                      model_filename.format(block_idx=block_idx)))
            num_channels = self.metadata_list[block_idx][0]['input_shape'][3]
            # TODO output_shapes is a list of layer shapes, 0 indexed
            # Should change to a dict to avoid the hack
            block_model.resize_tensor_input(0,
                    (1, *self.output_shapes[self.tile_index][(block_idx-1)*2], num_channels),
                                            strict=True)
            block_model.allocate_tensors()
            self.model_list[block_idx] = block_model
            maxpool_model = tflite.Interpreter(os.path.join(model_folder,
                                      maxpool_filename.format(block_idx=block_idx)))
            num_channels = self.metadata_list[block_idx*10][0]['input_shape'][3]
            maxpool_model.resize_tensor_input(0,
                    (1, *self.output_shapes[self.tile_index][(block_idx-1)*2+1], num_channels),
                                            strict=True)
            maxpool_model.allocate_tensors()
            self.model_list[block_idx*10] = maxpool_model
        self.prev_tile = None

    def process_tile(self, request):
        # Validate the request
        # tile_details should contain Nidx, Midx, top/bot_x/y
        reqd_fields = ["data", "convblockidx", "tile_details", "main_input", "TaskID"]
        for f in reqd_fields:
            if f not in request:
                # TODO signal error
                return None
        logging.debug(f"[{self.core}]: Processing tile {request['TaskID']} "+
                f"shape={request['shape']} "+
                f"Nidx={request['tile_details']['Nidx']} "+
                f"Midx={request['tile_details']['Midx']} "+
                f"through conv block {request['convblockidx']}")
        # Process tile will always be called on the same machine, so data won't be marshalled
        new_tile_shape = request["shape"]
        if request["data"]["type"] == "same":
            input_data = self.prev_tile
        elif request["data"]["type"] == "offset":
            # We are getting an update to the tile, not the whole tile
            input_data = np.zeros((1, *new_tile_shape[1:]), dtype=np.float32)
            new_rows = request["data"]["new_rows"]
            new_cols = request["data"]["new_columns"]
            # Add rows
            col_start = 0
            if request["data"]["row_position"] == 'before':
                input_data[0,0:new_rows.shape[1], :, :] = new_rows
                col_start = new_rows.shape[1]
            elif request["data"]["row_position"] == 'after':
                input_data[0,
                        self.prev_tile.shape[1]:self.prev_tile.shape[1]+new_rows.shape[1],
                        :, :] = new_rows
            # Add columns
            if request["data"]["column_position"] == 'before':
                input_data[0,col_start:col_start+new_cols.shape[1],
                             0:new_cols.shape[2], :] = new_cols
                input_data[0,col_start:col_start+self.prev_tile.shape[1],
                             new_cols.shape[2]:new_cols.shape[2]+self.prev_tile.shape[2],:] = self.prev_tile
            elif request["data"]["column_position"] == 'after':
                input_data[0,col_start:col_start+self.prev_tile.shape[1],
                             0:self.prev_tile.shape[2],:] = self.prev_tile
                input_data[0,col_start:col_start+new_cols.shape[1],
                             self.prev_tile.shape[2]:self.prev_tile.shape[2]+new_cols.shape[2], :] = new_cols
        elif request["data"]["type"] == "new":
            input_data = request["data"]["data"]
        tile = request["tile_details"]
        main_input = request["main_input"]
        convblockidx = request['convblockidx']
        # Run the processing through the convolutional block first
        output = input_data
        model = self.model_list[convblockidx]
        # Get input and output tensors.
        input_details = model.get_input_details()
        output_details = model.get_output_details()
        # Set the input data for the convolutional block
        model.set_tensor(input_details[0]['index'], output)
        # Invoke
        model.invoke()
        # Get the response
        output = model.get_tensor(output_details[0]['index'])
        # On convolutional layers remove the overlapping region
        # Maxpool layers have no overlap
        if self.metadata_list[convblockidx][0]['layer_type'] == 'conv':
            top_x_offset,top_y_offset,bot_x_offset,bot_y_offset = 0,0,0,0
            num_layers = len(self.metadata_list[convblockidx])
            conv_kernel_size = int(np.floor(
                    self.metadata_list[convblockidx][-1]['kernel_shape'][0]/2))
            conv_output_shape = self.metadata_list[convblockidx][-1]['output_shape']
            top_left_x = tile["top_x"]
            top_left_y = tile["top_y"]
            bot_right_x = tile["bot_x"]
            bot_right_y = tile["bot_y"]
            if top_left_x > 0:
                top_x_offset += num_layers*conv_kernel_size
            if top_left_y > 0: top_y_offset += num_layers*conv_kernel_size
            if bot_right_x < main_input["width"]-1:
                bot_x_offset -= num_layers*conv_kernel_size
            if bot_right_y < main_input["height"]-1:
                bot_y_offset -= num_layers*conv_kernel_size
            if convblockidx == 5:
                if top_x_offset != 0: top_x_offset -= 1
                if bot_x_offset != 0: bot_x_offset -= 1
                if top_y_offset != 0: top_y_offset -= 1
                if bot_y_offset != 0: bot_y_offset -= 1
            logging.debug(f"[{self.core}] Trim offsets from {output.shape} with {top_x_offset, top_y_offset, bot_x_offset, bot_y_offset}. Tile pos: {top_left_x, top_left_y, bot_right_x, bot_right_y} in {main_input['width'], main_input['height']}")
            output = output[:,
                    top_y_offset:output.shape[1]+bot_y_offset,
                    top_x_offset:output.shape[2]+bot_x_offset, :]
        # Process through the following maxpool layer
        model = self.model_list[convblockidx*10]
        # Get input and output tensors.
        input_details = model.get_input_details()
        output_details = model.get_output_details()
        # Set the input data for the convolutional block
        model.set_tensor(input_details[0]['index'], output)
        # Invoke
        model.invoke()
        # Get the response
        output = model.get_tensor(output_details[0]['index'])
        logging.debug(f"[{self.core}]: Done")
        self.prev_tile = output
        # Build response
        response = dict()
        response["TaskID"] = request["TaskID"]
        response["data"] = output
        response["shape"] = output.shape
        response["tile_details"] = {'Nidx': tile['Nidx'], 'Midx': tile['Midx']}
        # Insert request into the results queue
        logging.info(f"{[self.core]} {time()}: Put result {output.shape}")
        self.result_conn[1].send_bytes(pickle.dumps(response))

    def run(self):
        # Pin to the requested core
        os.sched_setaffinity(0, [self.core])
        logging.debug(f"Inference handler {self.core} started")
        # Start the processing loop
        self.running = True
        while self.running:
            # Wait for a processing task
            proc_task = self.processing_conn[0].recv_bytes()
            if len(proc_task) == 0: continue
            logging.info(f"{[self.core]} {time()}: received proc task {len(proc_task)} bytes")
            self.process_tile(pickle.loads(proc_task))

# TODO in main
# * run the main request handler
# * create the inference handlers

if __name__ == '__main__':
    # create the inference handlers for each core
    os.sched_setaffinity(0, [3])
    # Keep track of start times
    start_times = {}
    # Parallel experiment
    cores = [0 for _ in range(4)] # This stores tasks allocated to cores
    while True:
        # Wait until 2 cores are available
        available_cores = []
        for cidx,c in enumerate(cores):
            if c == 0:
                available_cores.append(cidx)
        if len(available_cores) == 0:
            response = Globals.results_queue.get() # Wait for a request to finish processing
            total_time = time() - start_times[response['TaskID']]
            del start_times[response['TaskID']]
            print(f"{response['TaskID']} completed, Time: {total_time}")
            for cidx,c in enumerate(cores):
                if c == response['TaskID']:
                    available_cores.append(cidx)
        if len(available_cores) > 2:
            available_cores = available_cores[:2]
        # Generate a new request
        task_id = f"task{randint(100,1000)}"
        img_resp = LoadImage(None, task_id)
        img_resp['N'] = 1
        img_resp['M'] = 2
        img_resp['cores'] = available_cores
        # Mark the cores as in-use
        for c in available_cores:
            cores[c] = task_id
        # Create the partition and process thread
        print(f"Processing {task_id} on {available_cores}")
        proc_thread = PartitionProcess(img_resp)
        # Record the start time
        start_times[task_id] = time()
        # Dispatch the thread
        proc_thread.start()
        # Take a little break
        sleep(0.5 + random())


    # Below is sequential experiment
    #img_resp = LoadImage(None)
    #img_resp['N'] = 2
    #img_resp['M'] = 2
    #img_resp['cores'] = [0,1,2,3]
    #start = time()
    #num_iters = 10
    #for i in range(num_iters):
    #    print(f"Processing {i}")
    #    request_lock.acquire()
    #    PartitionProcess(img_resp)
    #end = time()
    #print(f"Average processing {(end-start)/num_iters}")
