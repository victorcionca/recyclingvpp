apt install cmake python3-pip ntp libopenjp2-7 libatlas-base-dev iperf3 git libjpeg-dev zlib1g-dev libopenblas-dev
cp /home/pi/recyclingvpp/ntp.conf /etc/
echo "INSTALL: Copied ntp config"
python3 -m venv /home/pi/recyclingvpp/venv
source /home/pi/recyclingvpp/venv/bin/activate
sudo su - pi -c "python3 -m pip install -r /home/pi/recyclingvpp/requirements.txt"