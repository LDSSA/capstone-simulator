import time
import argparse
import json
import os
import datetime
from collections import Counter
import requests
from requests_futures.sessions import FuturesSession
import pandas as pd

DATE_FORMAT = "%d-%m-%Y"


def valid_date(date):
    try:
        return datetime.datetime.strptime(date, DATE_FORMAT)
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(date)
        raise argparse.ArgumentTypeError(msg)


parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('-s', '--startdate', required=True, type=valid_date)
parser.add_argument('-e', '--enddate', required=True, type=valid_date)


def _read_json(filename):
    with open(filename) as fh:
        return json.load(fh)


class Simulator(object):
    # unix timestamp
    start_time = None
    # unix timestamp
    end_time = None
    # unix timestamp
    cur_time = None
    # last time the send_needed function was run (unix timestamp)
    last_time = None
    # the state of all requests to be made to all servers
    state = None
    # an array of observations created from the test* csv files
    observations = None
    # a list of strings
    app_names = None
    # tuple of timestamps where if a deadline is within the range, try to send
    range_to_send = (None, None)

    def __init__(self, start_time, end_time):
        self.cur_time = time.mktime(datetime.datetime.utcnow().timetuple())
        self.start_time = start_time
        self.end_time = end_time
        self.load_observations()
        self.load_last_time()
        self.load_app_names()
        self.load_state()
        self.range_to_send = (
            min(self.last_time, self.cur_time - 3600),
            self.cur_time,
        )
        print('range is', self.range_to_send)

    def send_needed(self):
        to_send = self.get_to_send()
        session = FuturesSession(max_workers=50)
        futures = []
        success_count = 0
        print('going to try to send {}'.format(len(to_send)))
        for app_obs in to_send:
            future = session.post(
                f'https://{app_obs.app_name}.herokuapp.com/predict',
                json={
                    'id': app_obs.deadline.obs.id,
                    'observation': app_obs.deadline.obs.obs
                })
            futures.append((future, app_obs))
        print('sent {} requests, waiting for replies'.format(len(to_send)))
        status_codes = Counter()
        for future, state in futures:
            try:
                result = future.result()
            except requests.exceptions.ConnectionError as e:
                status_codes['disaster'] += 1
                continue
            status_codes[result.status_code] += 1
            success = 200 <= future.result().status_code < 300
            if success:
                try:
                    proba = result.json()['proba']
                    self.state[app_obs.app_name][app_obs.deadline.obs.id] = proba
                except Exception as e:
                    print(e)

                success_count += 1
        self.write_state()
        self.write_last_time()
        print(status_codes)
        return status_codes, futures

    def get_to_send(self):
        deadlines = [
            x for x in self.get_deadlines()
            if self.range_to_send[0] < x.deadline < self.range_to_send[1]
        ]
        to_send = []
        for app_name in self.app_names:
            to_send += [
                AppObservation(deadline, app_name)
                for deadline in deadlines
                if self.get_status(app_name, deadline.obs.id) is None
            ]
        return to_send

    def get_deadlines(self):
        interval = (
            (self.end_time - self.start_time) / len(self.observations))
        deadlines = []
        cur_deadline = self.start_time
        for obs in self.observations:
            deadlines.append(Deadline(cur_deadline, obs))
            cur_deadline += interval
        return deadlines

    def get_status(self, app_name, obs_id):
        return self.state[app_name].get(obs_id)

    def load_state(self):
        if not os.path.exists('state.json'):
            with open('state.json', 'w') as fh:
                fh.write(json.dumps({
                    app_name: {} for app_name in self.app_names
                }))
        self.state = _read_json('state.json')
        # now ensure that in case there are new app_names they get added
        for app_name in self.app_names:
            if app_name not in self.state:
                self.state[app_name] = {}

    def write_state(self):
        with open('state.json', 'w') as fh:
            fh.write(json.dumps(self.state))

    def write_last_time(self):
        with open('last_time.json', 'w') as fh:
            fh.write(str(self.last_time))

    def load_app_names(self):
        self.app_names = _read_json('app_names.json')

    def load_last_time(self):
        if not os.path.exists('last_time.json'):
            with open('last_time.json', 'w') as fh:
                fh.write(str(self.cur_time))
        self.last_time = _read_json('last_time.json')

    def load_observations(self):
        df = pd.concat([
            pd.read_csv('test_will_give_outcomes.csv'),
            pd.read_csv('test_no_give_outcomes.csv')
        ])
        observations = []
        for _, obs in df.iterrows():
            obs = obs.to_dict()
            _id = obs['id']
            del obs['id']
            del obs['target']
            observations.append(Observation(_id, obs))
        self.observations = observations[:-50]


class Deadline(object):
    # unix timestamp
    deadline = None
    # Observation object
    obs = None

    def __init__(self, deadline, obs):
        self.deadline = deadline
        self.obs = obs


class Observation(object):
    # integer id
    id = None
    # dictionary that can be send as observation payload
    obs = None

    def __init__(self, _id, obs):
        self.id = _id
        self.obs = obs


class AppObservation(object):
    # status is None if no request has been made yet
    # Deadline object
    deadline = None
    # string of app_name
    app_name = None

    def __init__(self, deadline, app_name):
        self.app_name = app_name
        self.deadline = deadline


if __name__ == '__main__':

    args = parser.parse_args()
    start = time.mktime(args.startdate.timetuple())
    end = time.mktime(args.enddate.timetuple())
    while True:
        s = Simulator(start_time=start, end_time=end)
        s.send_needed()
        time.sleep(1)
