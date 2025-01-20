import subprocess
import sys

if __name__ == "__main__":
    file_name = sys.argv[1]

    for i in range(1, 5):
        print(f"scp ./{file_name} pi@raspberrypi{i}.local:/home/pi/recyclingvpp/experiment_manager/trace_file.json")
        subprocess.call(["scp", f"./{file_name}", f"pi@raspberrypi{i}.local:/home/pi/recyclingvpp/experiment_manager/trace_file.json"])