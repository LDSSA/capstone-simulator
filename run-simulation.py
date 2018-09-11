#!/usr/bin/env python3

import datetime
import argparse
from simulator import (ObservationSimulator,
                       SecondObservationSimulator,
                       TrueOutcomeSimulator)

DATE_FORMAT = "%d-%m-%Y"


def datetime_type(date):
    try:
        return datetime.datetime.strptime(date, DATE_FORMAT)
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(date)
        raise argparse.ArgumentTypeError(msg)


parser = argparse.ArgumentParser(
    description='Set the end time of the simulator.')
parser.add_argument('-e', '--enddate', type=datetime_type)
parser.add_argument('-s', '--simulator', required=True,
                    choices=['observation', 'true-outcome'])


if __name__ == '__main__':
    args = parser.parse_args()
    end_time = int(args.enddate.timestamp())

    if args.simulator == 'observation':
        simulator = ObservationSimulator(end_time=end_time)
    else:
        simulator = TrueOutcomeSimulator(end_time=end_time)

    simulator.run()
