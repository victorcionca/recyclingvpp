import numpy as np
import inference_engine as engine
import threading
import Globals  # For the multiprocessing queues
import logging
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO)
# Functionality
# - need constructors for the requests
# - inference engine is spawned as a thread
# - load image
# - partition
# - process
# - assemble

def setup_aid_channel():
    options = [('grpc.max_send_message_length', 100*1024*1024),('grpc.max_receive_message_length', 100*1024*1024)]
    channel = grpc.insecure_channel('localhost:8000', options=options)
    stub = inference_grpc.InferenceAidStub(channel)
    return stub

def gen_load_request(filename):
    request = {}
    request['filename'] = filename
    request['TaskID'] = 1
    return request

def gen_partition_request(data, data_shape, N, M, convblockidx):
    """
    Important: data should be a bytearray
    """
    part_req = {}
    part_req["data"] = data#.tobytes()
    part_req["shape"] = data_shape
    part_req["convblockidx"] = convblockidx
    part_req["N"] = N
    part_req["M"] = M
    part_req['TaskID'] = 1
    return part_req

def gen_assemble_request(partitions, convblockidx):
    """
    Assembles the partitions in the list of partition processing results.
    Each partition has a "TaskID", "data", "shape", and "tile_details".
    The partitions must be added to the "Tiles" field of the assembly request.
    """
    assemble_req = {}
    assemble_req["convblockidx"] = convblockidx
    assemble_req["Tiles"] = []
    for p in partitions:
        assemble_req["Tiles"].append(p)
    assemble_req["TaskID"] = 1
    return assemble_req

def gen_process_request(data, data_shape, tile_details, convblockidx, core, taskid):
    # Prepare the data
    proc_req = {}
    proc_req["type"] = "task"
    proc_req["data"] = data#.tobytes()
    proc_req["shape"] = data_shape
    proc_req["convblockidx"] = convblockidx
    proc_req["core"] = core
    proc_req["tile_details"] = tile_details
    proc_req["TaskID"] = taskid
    return proc_req

class ResultProcessing(threading.Thread):
    """
    Gather the results of processing tiles from the same conv block
    and assemble.
    """

    def __init__(self, taskids):
        """
        Parameters

        * taskids   --  list of task ids corresponding to processing requests
                        that are being executed
        """
        super().__init__()
        self.results_queue = Globals.results_queue
        self.taskids = taskids
        self.result = None

    def run(self):
        self.results = []
        logging.info("Waiting for results")
        while len(self.results) < len(self.taskids):
            result = self.results_queue.get()
            logging.info(f"Received result for {result['TaskID']}, shape {result['shape']}")
            if result['TaskID'] not in self.taskids: continue
            self.results.append(result)
        if len(self.results) > 1:
            # Assemble results
            assemble_req = gen_assemble_request(self.results, 1)
            assemble_res = engine.AssembleData(assemble_req)
            self.result = assemble_res
        else:
            self.result = self.results[0]

def test_inference_engine(filename, N, M):
    # Start the inference engine
    proc_handler = engine.InferenceHandler()
    proc_handler.start()
    # Generate and issues load request
    load_req = gen_load_request(filename)
    load_res = engine.LoadImage(load_req)
    logging.info(f"Loaded image from {load_req['filename']}. Shape: {load_res['shape']}")
    # Generate and issue partition
    part_req = gen_partition_request(load_res['data'], load_res['shape'], 2, 2, 1)
    part_res = engine.PartitionData(part_req)
    logging.info("Resulting partitions:")
    proc_requests = []
    task_ids = []
    # Generate process requests for each tile, save and run afterwards
    for idx, tile in enumerate(part_res["Tiles"]):
        logging.info(f"Tile N:{tile['tile_details']['Nidx']} M:{tile['tile_details']['Midx']}"
                     f"-- {tile['shape']} "
                     f"({tile['tile_details']['top_x']}, {tile['tile_details']['top_y']}"
                     f"{tile['tile_details']['bot_x']}, {tile['tile_details']['bot_y']})")
        # Generate the proces request using the data from the partition response
        preq = gen_process_request(tile['data'], tile['shape'], tile['tile_details'], 1, idx+2, idx)
        proc_requests.append(preq)
        # Save the task id of the process request for the Results Processors
        task_ids.append(idx)
    # Start result processing thread
    res_proc = ResultProcessing(task_ids)
    res_proc.start()
    # Put the processing requests in the work queue
    for preq in proc_requests:
        Globals.work_queue.put(preq)
    # Wait for results processing to be done
    res_proc.join()
    # Collect the assembled result
    assembled = res_proc.result
    logging.info(f"Assembled shape for Task {assembled['TaskID']}: {assembled['shape']}")
    distr_proc_result = engine.deserialize_numpy(assembled['data'], assembled['shape'])
    # Process single for comparison
    tile_details = {
             'Nidx': 0, 'Midx': 0, 'top_x': 0, 'top_y': 0,
            'bot_x': load_res['shape'][2]-1, 'bot_y': load_res['shape'][1]-1
            }
    single_proc = gen_process_request(load_res['data'], load_res['shape'], tile_details, 1, 1, 10)
    res_proc = ResultProcessing({10:{}})
    res_proc.start()
    Globals.work_queue.put(single_proc)
    res_proc.join()
    single = res_proc.result
    logging.info(f"Assembled shape for Task {single['TaskID']}: {single['shape']}")
    single_result = engine.deserialize_numpy(single['data'], single['shape'])
    fig, axs = plt.subplots(1, 2)
    axs[0].imshow(distr_proc_result[0, :, :, 0])
    axs[0].set_title('Distributed')
    axs[1].imshow(single_result[0, :, :, 0])
    axs[1].set_title('Single')
    plt.show()

if __name__ == '__main__':
    test_inference_engine('metal110.jpg', 2, 2)
