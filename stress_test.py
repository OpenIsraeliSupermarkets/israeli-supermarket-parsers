import time
import json
import datetime
import tempfile
import pstats
import cProfile
import io
from il_supermarket_scarper import ScarpingTask,ScraperFactory
from il_supermarket_parsers import ConvertingTask

def format_stats_as_json(profile, project_name):
    """get the stats from the profiler and format them as json"""
    stream = io.StringIO()
    ps = pstats.Stats(profile, stream=stream)
    ps.sort_stats(pstats.SortKey.CUMULATIVE)  # Sort by cumulative time
    ps.print_stats()

    # Convert the printed stats to a list of lines
    stats_output = stream.getvalue().splitlines()

    # Filter the lines to include only functions within the project
    project_stats = []
    for line in stats_output:
        if project_name in line:  # Filter for project-specific lines

            parts = line.split()
            if len(parts) >= 5:  # Basic sanity check for the parts
                function_data = {
                    "function": parts[-1],  # Function path
                    "ncalls": parts[0],  # Number of calls
                    "tottime": parts[1],
                    "tottime_per_call": parts[2],  # Time spent in function
                    "cumtime": parts[3],  # Cumulative time including subcalls
                    "cumtime_per_call": parts[4],  #
                }
                project_stats.append(function_data)

    return project_stats


if __name__ == "__main__":

   
    # ScarpingTask(
    #     enabled_scrapers=ScraperFactory.sample(1),
    #     dump_folder_name="dumps",
    #     multiprocessing=None,
    #     when_date=datetime.datetime(2025,1,10,0,0,0),
    # ).start()
    
    # execution_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # start_time = time.time()
    # pr = cProfile.Profile()
    # pr.enable()

    ConvertingTask(
        enabled_parsers=None,
        files_types=None,
        data_folder="dumps",
        multiprocessing=None,
        output_folder="outputs",
    ).start()

    # pr.disable()

    # end_time = time.time()
    # result = {
    #     "status": format_stats_as_json(pr, "israeli-supermarket-parsers"),
    #     "execution_time": execution_time,
    #     "start_time": start_time,
    #     "end_time": end_time,
    #     "time": end_time - start_time,
    # }

    # with open("stress_test_results.json", "w", encoding="utf-8") as f:
    #     json.dump(result, f)
