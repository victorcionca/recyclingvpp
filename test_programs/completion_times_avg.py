import json
import statistics as stat

if __name__ == "__main__":
    file = open('./1x2_completion_times.json', "r")
    data = json.load(file)
    file.close()

    one_by_two_times = list(data.values())

    one_by_two_times_stdev = stat.stdev(one_by_two_times)
    one_by_two_times_avg = stat.mean(one_by_two_times)

    
    file = open('./2x2_completion_times.json', "r")
    data = json.load(file)
    file.close()

    two_by_two_times = list(data.values())

    two_by_two_times_stdev = stat.stdev(two_by_two_times)
    two_by_two_times_avg = stat.mean(two_by_two_times)

    result = {
        "1x2_mean": one_by_two_times_avg,
        "1x2_stdev": one_by_two_times_stdev,
        "2x2_mean": two_by_two_times_avg,
        "2x2_stdev": two_by_two_times_stdev
    }

    file = open("./completion_times_avg.json", "w")
    res = json.dumps(result)
    file.write(res)
    file.close()


