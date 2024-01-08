import subprocess

def open_iterm2_tab(command_to_run):
    subprocess.run(["osascript", "-e", f'tell application "iTerm2"\n'
                                       'tell current window\n'
                                       f'create tab with default profile\n'
                                       'tell current session\n'
                                       f'write text "{command_to_run}"\n'
                                       'end tell\n'
                                       'end tell\n'
                                       'end tell'])

def main():
    # Check if the correct number of arguments is provided
    import sys
    if len(sys.argv) != 7:
        print(f"Usage: {sys.argv[0]} <script_name.py> <controller_hostname> <client1_hostname> <client2_hostname> <client3_hostname> <client4_hostname>")
        sys.exit(1)

    profile_application = (sys.argv[1]).lower()
    controller_hostname = sys.argv[2]
    client_hostnames = sys.argv[3:]
    username = "pi"
    recyclingvpp_directory = "/home/pi/recyclingvpp"

    inference_program = "./run_inference.sh" if profile_application != "true" else "./run_inference_profile.sh"

    # Loop through client hostnames and open two iTerm2 tabs for each
    for index in range(0, len(client_hostnames)):
        # Prepare arguments for run_experiment.sh
        client = client_hostnames[index]
        index_expr = f"{index}"
        first_arg_expr = f"{index < len(client_hostnames) / 2}"
        second_arg_expr = "False"
        third_arg_expr = controller_hostname

        # Display the arguments
        print(f"Arguments for {client}: Index={index_expr}, Arg1={first_arg_expr}, Arg2={second_arg_expr}, Arg3={third_arg_expr}")

        # First tab: run_experiment.sh
        open_iterm2_tab(f'ssh {username}@{client} \'cd {recyclingvpp_directory} && ./run_experiment.sh {index_expr} {first_arg_expr} {second_arg_expr} {third_arg_expr}\'')

        # Second tab: run_inference.sh
        open_iterm2_tab(f'ssh {username}@{client} \'cd {recyclingvpp_directory} && {inference_program} {client} {controller_hostname}\'')

if __name__ == "__main__":
    main()
