apt install cmake python3-pip ntp libopenjp2-7 libatlas-base-dev iperf3 git libjpeg-dev zlib1g-dev
cp /home/pi/recyclingvpp/ntp.conf /etc/
echo "INSTALL: Copied ntp config"
sudo su - pi -c "python3 -m pip install -r /home/pi/recyclingvpp/requirements.txt"