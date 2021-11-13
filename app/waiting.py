import os
import datetime
import time
from setting import Settings

# get container start time
container_start = datetime.datetime.strptime(os.environ.get('START_TIME'), '%Y-%m-%dT%H:%M:%S')

# set up time limit
limit = datetime.timedelta(seconds=int(os.environ.get('REPEAT_TIME_PERIOD')))
run_time = datetime.datetime.now() - container_start

# compare the uptime time of the container and given limit
if run_time >= limit:
    # container is runnig longer time than given limit
    if Settings.get().debug >= 2: print("waiting - time limit reached, exiting")
else:
    # container is running shorter time than given limit
    waiting_time = (limit - run_time).total_seconds()
    if Settings.get().debug  >= 2: print("waiting - limit not reached, waiting", waiting_time)
    time.sleep(waiting_time)
