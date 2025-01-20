import subprocess


# Function to ping a host and return the output as a string
def ping(host, byte_size):
    # Run the ping command with subprocess
    process = subprocess.Popen(
        ['ping', '-c', '10', '-i', '0.1', '-s', byte_size, host],
        stdout=subprocess.PIPE,     # Redirect standard output
        stderr=subprocess.PIPE      # Redirect standard error
    )
    
    # Capture the output and error
    stdout, stderr = process.communicate()
    
    # Convert bytes to string and return the output
    if process.returncode == 0:
        return stdout.decode('utf-8')  # Return output on success
    else:
        return stderr.decode('utf-8') 


def parse_ping_result(ping_res: str, bytes_calc: int):
    parsed_result = ping_res.split("\n")

    parsed_result = [res for res in parsed_result if str(bytes_calc)[0: 2] == res[0:2] and res[-2: len(res)] == "ms"]

    parsed_result_values = []

    for i in range(0, len(parsed_result)):
        parsed_result_split = parsed_result[i].split(" ")
        rtt = float(parsed_result_split[-2].split("=")[1])
        bits_per_second = (((bytes_calc * 8) * 2) / rtt) * 1000
        parsed_result_values.append(bits_per_second)


    return parsed_result_values


def main():
    byte_size = 1400
    bytes_calc_size = 1442
    ping_result = ping("raspberrypi4.local", str(byte_size))
    parsed_result = parse_ping_result(ping_result, bytes_calc_size)
    print(parsed_result)
    return

if __name__ == "__main__":
    main()