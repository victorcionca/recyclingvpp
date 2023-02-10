from datetime import datetime as dt
class AssemblyHold:
    def __init__(self, deadline: dt = dt.now(), dnn_id: str = "", convidx: str = "", assembly_data: bytes = bytes(), shape: list[int] = []) -> None:
        self.deadline = deadline
        self.dnn_id = dnn_id
        self.convidx = convidx
        self.assembly_data = assembly_data
        self.shape = shape
        