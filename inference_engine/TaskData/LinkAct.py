import datetime
from typing import Tuple

class LinkAct:
    def __init__(self, isMeta: bool, hostNames: Tuple[str, str], dataSize: int, startFinTime: Tuple[datetime.datetime, datetime.datetime]):
        self.is_meta = isMeta
        self.host_names = hostNames
        self.data_size = dataSize
        self.start_fin_time = startFinTime