import threading
import logging
import experiment_loop
import experiment_manager


def start_REST(logging):
    ThreadStart(logging, experiment_manager.run_server, "REST")
 # type: ignore

def start_experiment_loop(logging):
    ThreadStart(logging, experiment_loop.run_loop, "Experiment Loop")


def ThreadStart(logging, function, thread_name):
    logging.info(f"Main    : before creating {thread_name} thread")
    x = threading.Thread(target=function)
    logging.info(f"Main    : before running {thread_name} thread")
    x.start()
    logging.info(f"Main    : running {thread_name} thread")
    return


def main():
    logging.basicConfig(level=logging.INFO)
    start_REST(logging)
    start_experiment_loop(logging)
    return


if __name__ == "__main__":
    main()