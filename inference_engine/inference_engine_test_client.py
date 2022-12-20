import numpy as np
import grpc
import requests_pb2_grpc as inference_grpc
import requests_pb2 as inference_pb

# Functionality
# - inference engine is spawned as a thread
# - load image
# - partition
# - process
# - 

def setup_aid_channel():
    options = [('grpc.max_send_message_length', 100*1024*1024),('grpc.max_receive_message_length', 100*1024*1024)]
    channel = grpc.insecure_channel('localhost:8000', options=options)
    stub = inference_grpc.InferenceAidStub(channel)
    return stub

def gen_load_request(stub):
    load_req = inference_pb.LoadRequest()
    load_req.file = "metal110.jpg"
    load_response = stub.LoadImage(load_req)
    return load_response

def gen_partition_request(stub, data, N, M, convblockidx):
    part_req = inference_pb.PartitionRequest()
    part_req.data = data.tobytes()
    part_req.shape.extend(data.shape)
    part_req.convblockidx = convblockidx
    part_req.partitionSpecs.N = N
    part_req.partitionSpecs.M = M
    part_res = stub.PartitionData(part_req)
    return part_res

def gen_assemble_request(stub, partitions, convblockidx):
    """
    Assembles the partitions in the list of inference_pb.Partition
    with each partition
    having a .x and .y top-left coordinates, .data and .shape
    """
    assemble_req = inference_pb.AssembleRequest()
    assemble_req.convblockidx = convblockidx
    for p in partitions:
        assemble_req.tiles.append(p)
    assemble_resp = stub.AssembleData(assemble_req)
    return assemble_resp

processed_tiles = []
def gen_process_request(data, convblockidx, core):
    # Prepare the data
    proc_req = inference_pb.ProcessRequest()
    proc_req.data = data.tobytes()
    proc_req.shape.extend(data.shape)
    proc_req.convblockidx = convblockidx
    proc_req.core = core
    # Make the request to server listening at 8000+core
    options = [('grpc.max_send_message_length', 100*1024*1024),('grpc.max_receive_message_length', 100*1024*1024)]
    channel = grpc.insecure_channel(f'localhost:{8000+core}', options=options)
    stub = inference_grpc.InferenceStub(channel)
    proc_res = stub.ProcessData(proc_req)
    return proc_res

def process_tile(part_data, convblockidx, core, tile):
    print(f"Requesting processing of tile for core {core} shape {part_data.shape}")
    proc_res = gen_process_request(part_data, convblockidx, core)
    processed_tiles.append((proc_res, tile))

from threading import Thread
def distr_processing(stub, data, convblockidx):
    part_res = gen_partition_request(stub, data, 2, 2, convblockidx)
    tile_threads = []
    for tile_idx, tile in enumerate(part_res.tiles):
        part_data = np.frombuffer(tile.data, dtype=np.float32)
        part_data = part_data.reshape(tile.shape)
        t = Thread(target=process_tile, args=(part_data, convblockidx, tile_idx+1, tile))
        t.start()
        tile_threads.append(t)
    for t in tile_threads:
        t.join()
    tiles = []
    for proc_res, tile in processed_tiles:
        part = inference_pb.Partition()
        part.position.x = tile.position.x
        part.position.y = tile.position.y
        part.data = proc_res.data
        part.shape.extend(proc_res.shape)
        tiles.append(part)
    return tiles
