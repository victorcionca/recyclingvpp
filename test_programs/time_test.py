import ntplib
from datetime import datetime
import os
import json
import requests
from datetime import datetime as dt
import time

# IP address or hostname of the NTP server running on the controller device
ntp_server = 'com-c132-m34579'

# Create an NTP client
client = ntplib.NTPClient()

# Query the NTP server and get the response
response = client.request(ntp_server)

# Adjust the local system time based on the NTP server's response
datetime_now = datetime.fromtimestamp(response.tx_time)

# Set the system time of the current device
# Note: Setting system time may require elevated privileges (e.g., running as administrator)
# Consult the platform-specific documentation for setting system time in your environment
os.system('sudo date -s "{}"'.format(datetime_now))

while(True):
    requests.post(url=f"http://{ntp_server}:9912/time_test", json=json.dumps({"time": dt.now().timestamp() * 1000}))
    time.sleep(1)
    