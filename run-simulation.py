import datetime
import argparse
import time
from simulator import ObservationSimulator, TrueOutcomeSimulator

DATE_FORMAT = "%d-%m-%Y"


def datetime_type(date):
    try:
        return datetime.datetime.strptime(date, DATE_FORMAT)
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(date)
        raise argparse.ArgumentTypeError(msg)


parser = argparse.ArgumentParser(
    description='Set the end time of the simulator.')
parser.add_argument('-e', '--enddate', required=True, type=datetime_type)
parser.add_argument('-s', '--simulator', required=True,
                    choices=['observation', 'true-outcome'])

args = parser.parse_args()
end_time = time.mktime(args.enddate.timetuple())

if __name__ == '__main__':

    while True:
        if args.simulator == 'observation':
            s = ObservationSimulator(end_time=end_time)
        else:
            s = TrueOutcomeSimulator(end_time=end_time)
        start_t = time.time()
        _status_codes, _futures = s.send_needed()
        if _status_codes:
            print(_status_codes)
            print(f'round completed in {time.time() - start_t} seconds')
        time.sleep(1)
