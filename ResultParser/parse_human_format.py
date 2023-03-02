import sys
import json
import ResultsFormatter

log_directory = "/Users/jamiecotter/Documents/Work/PhD/recyclingvpp/ResultParser/result_logs/"


def main(logName: str):
    file = open(f"{log_directory}{logName}", "r")
    json_array = json.loads(file.read())
    file.close()

    json_array = ResultsFormatter.result_format(
        json_array=json_array, human_format=True)

    with open('./result_parsed.json', 'w') as f:
        json.dump(json_array, f, indent=4)


if __name__ == "__main__":
    log_name = sys.argv[1]
    main(log_name)
