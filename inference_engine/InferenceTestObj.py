import threading
from datetime import datetime as dt
from datetime import timedelta
import Globals


class InferenceTestObj(threading.Thread):
    def __init__(self, request, deadline: dt):
        super().__init__()
        self.halt_task = False
        self.task_id = request["TaskID"]
        self.deadline = deadline

        self.partN = request["N"]
        self.partM = request["M"]

    def halt(self):
        self.halt_task = True

    def is_halted(self):
        return self.halt_task

    def run(self):
        while not self.halt_task and dt.now() < (self.deadline - timedelta(seconds=1)):
            continue

        if self.is_halted():
            return
        else:
            Globals.results_queue.put({"TaskID": self.task_id})
