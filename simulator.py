import time
import json
import os
import datetime
import copy
from collections import Counter
import requests
from requests_futures.sessions import FuturesSession
import pandas as pd


def _read_json(filename):
    with open(filename) as fh:
        state = json.load(fh)
    return state


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
    # interval in seconds in between successive requests
    interval = None

    # where to store the result of the version of the simulator
    state_filename = None
    # where to store the star time of the simulation
    start_time_filename = None
    # where to store the last time that the simulator ran
    last_time_filename = None

    def __init__(self, end_time):
        self.cur_time = time.mktime(datetime.datetime.utcnow().timetuple())
        self.end_time = end_time
        self._load_start_time()
        self._load_observations()
        self._load_last_time()
        self._load_app_names()
        self._load_state()
        self.range_to_send = (
            min(self.last_time, self.cur_time - 3600),
            self.cur_time,
        )
        self.interval = (
            (self.end_time - self.start_time) / len(self.observations))
        print('will send at interval {}'.format(self.interval))

    def send_needed(self):
        to_send = self._get_to_send()
        futures = self._send_futures(to_send)
        status_codes = self._process_replies(futures)
        self._write_state()
        self._write_last_time()
        return status_codes, futures

    def _send_futures(self, to_send):
        session = FuturesSession(max_workers=50)
        futures = []
        print('going to try to send {}'.format(len(to_send)))
        for app_obs in to_send:
            future = self._send_request(session, app_obs)
            futures.append((future, app_obs))
        print('sent {} requests, waiting for replies'.format(len(to_send)))
        return futures

    def _process_replies(self, futures):

        status_codes = Counter()
        for future, app_obs in futures:
            try:
                result = future.result()
            except requests.exceptions.ConnectionError as e:
                status_codes['disaster'] += 1
                continue
            status_codes[result.status_code] += 1
            success = 200 <= future.result().status_code < 300
            # -1 is a proba error code and this is what will be recorded
            # if a valid proba isn't returned
            reply = -1
            if success:
                try:
                    reply = self._process_result(result)
                except Exception as e:
                    print(e)
            self.state[app_obs.app_name][app_obs.deadline.obs.id] = reply

        return status_codes

    def _get_to_send(self):
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

        deadlines = []
        cur_deadline = self.start_time
        for obs in self.observations:
            deadlines.append(Deadline(cur_deadline, obs))
            cur_deadline += self.interval
        return deadlines

    def get_status(self, app_name, obs_id):
        return self.state[app_name].get(obs_id)

    def _load_state(self):
        if not os.path.exists(self.state_filename):
            with open(self.state_filename, 'w') as fh:
                fh.write(json.dumps({
                    app_name: {} for app_name in self.app_names
                }))
        self.state = _read_json(self.state_filename)
        for app_name in self.state:
            self.state[app_name] = dict(self.state[app_name])
        # now ensure that in case there are new app_names they get added
        for app_name in self.app_names:
            if app_name not in self.state:
                self.state[app_name] = {}

    def _write_state(self):
        with open(self.state_filename, 'w') as fh:
            towrite = copy.deepcopy(self.state)
            for app_name in towrite:
                towrite[app_name] = list(towrite[app_name].items())
            fh.write(json.dumps(towrite))

    def _write_last_time(self):
        with open(self.last_time_filename, 'w') as fh:
            fh.write(str(self.last_time))

    def _load_app_names(self):
        self.app_names = _read_json('app_names.json')

    def _load_last_time(self):
        if not os.path.exists(self.last_time_filename):
            with open(self.last_time_filename, 'w') as fh:
                fh.write(str(self.cur_time))
        self.last_time = _read_json(self.last_time_filename)

    def _load_observations(self):
        df = pd.concat([
            pd.read_csv('test_will_give_outcomes.csv'),
            pd.read_csv('test_no_give_outcomes.csv')
        ])
        observations = []
        for _, obs in df.iterrows():
            obs = obs.to_dict()
            _id, true_class = obs['id'], obs['target']
            del obs['id']
            del obs['target']
            observations.append(Observation(_id, obs, true_class))
        self.observations = observations[:-50]

    def _load_start_time(self):
        if not os.path.exists(self.start_time_filename):
            with open(self.start_time_filename, 'w') as fh:
                fh.write(str(self.cur_time))
        with open(self.start_time_filename) as fh:
            self.start_time = float(fh.read())


class ObservationSimulator(Simulator):
    state_filename = 'state.json'
    start_time_filename = 'start_time.json'
    last_time_filename = 'last_time.json'

    def _send_request(self, session, app_obs):
        return session.post(
            f'https://{app_obs.app_name}.herokuapp.com/predict',
            json={
                'id': app_obs.deadline.obs.id,
                'observation': app_obs.deadline.obs.obs
            })

    def _process_result(self, result):
        return result.json()['proba']


class TrueOutcomeSimulator(Simulator):
    state_filename = 'true_outcome_state.json'
    start_time_filename = 'true_outcome_start_time.json'
    last_time_filename = 'true_outcome_last_time.json'

    def _send_request(self, session, app_obs):
        return session.post(
            f'https://{app_obs.app_name}.herokuapp.com/update',
            json={
                'id': app_obs.deadline.obs.id,
                'true_class': app_obs.deadline.obs.true_class
            })

    def _process_result(self, result):
        return result.status_code

    def _load_observations(self):
        # override this because we only want to send true outcomes for
        # 500 observations
        super()._load_observations()
        self.observations = self.observations[:500]


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
    # 0 or 1 true class outcome
    true_class = None

    def __init__(self, _id, obs, true_class):
        self.id = _id
        self.obs = obs
        self.true_class = true_class


class AppObservation(object):
    # status is None if no request has been made yet
    # Deadline object
    deadline = None
    # string of app_name
    app_name = None

    def __init__(self, deadline, app_name):
        self.app_name = app_name
        self.deadline = deadline
