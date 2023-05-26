import ntplib
from datetime import datetime
import os
import json
import requests
from datetime import datetime as dt
from datetime import timedelta
import time

# IP address or hostname of the NTP server running on the controller device
ntp_server = 'com-c132-m34579'

INITIAL_TIME_SYNC = True
REFRESH_TIME = True

now = dt.now()

# Create an NTP client
client = ntplib.NTPClient()

if INITIAL_TIME_SYNC:
    # Query the NTP server and get the response
    response = client.request(ntp_server)

    # Adjust the local system time based on the NTP server's response
    now = datetime.fromtimestamp(response.tx_time)

    # Set the system time of the current device
    # Note: Setting system time may require elevated privileges (e.g., running as administrator)
    # Consult the platform-specific documentation for setting system time in your environment
    os.system('sudo date -s "{}"'.format(now))

delta = timedelta(minutes=10)

finish_time = now + delta
while(now < finish_time):
    requests.post(url=f"http://{ntp_server}:9911/time_test", json={"time": now.timestamp() * 1000})
    time.sleep(1)

    if REFRESH_TIME:
        # Query the NTP server and get the response
        response = client.request(ntp_server)

        # Adjust the local system time based on the NTP server's response
        now = datetime.fromtimestamp(response.tx_time)
    else:
        now = dt.now()


requests.post(url=f"http://{ntp_server}:9911/fin")
    