apt install python3-pip
apt install libopenjp2-7
apt install libatlas-base-dev
apt install iperf3
apt install git
apt install ntp
sudo su - pi -c "python3 -m pip install -r /home/pi/recyclingvpp/requirements.txt"
cp "/home/pi/recyclingvpp/ntp.conf" "/etc/"
