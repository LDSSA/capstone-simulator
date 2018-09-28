import json
import logging
import threading
import time

import pandas as pd
import peewee
import requests

import settings
import models


logger = logging.getLogger(__name__)


class Simulator(object):
    timeout = 30
    window = 30  # Time in seconds processed for each cycle
    endpoint = None
    filename = None

    def __init__(self, simulator_name, end_time=None):
        self.simulator_name = simulator_name

        self.students = models.Student.select()
        self.observations = self._load_observations()

        try:
            self.simulator = models.Simulator.get(
                models.Simulator.name == simulator_name)

            if not self.simulator.start_time:
                self.simulator.start_time = int(time.time())
                self.simulator.save()

            if end_time:
                self.simulator.end_time = end_time
                self.simulator.save()

        except peewee.DoesNotExist:
            if end_time is None:
                raise RuntimeError("end_time required")

            self.simulator = models.Simulator.create(
                name=simulator_name,
                start_time=int(time.time()),
                end_time=end_time,
            )

    def _load_observations(self):
        raise NotImplementedError()

    def _get_due_observations(self, student, observations):
        interval = ((self.simulator.end_time - self.simulator.start_time)
                    / len(observations))

        if student.last_window_end is None:
            student.last_window_end = self.simulator.start_time

        start_idx = int((student.last_window_end - self.simulator.start_time)
                        / interval)
        # end_idx excluded
        end_idx = int(
            (student.last_window_end + self.window - self.simulator.start_time)
            / interval)
        logger.debug("Indexes %s~%s", start_idx, end_idx)

        due = []
        for observation in observations[start_idx:end_idx]:
            # Check if this observation has been sent successfully
            exists = models.Observation.select().where(
                models.Observation.simulator == self.simulator,
                models.Observation.student == student,
                models.Observation.observation_id == observation['id'],
                models.Observation.response_status >= 200,
                models.Observation.response_status < 300,
                ).exists()
            if not exists:
                due.append(observation)

        return due

    def run(self):
        for student in self.students:
            if student.app:
                worker = threading.Thread(name="%s-%s" % (self.simulator.name,
                                                     student.email),
                                          target=self.run_student,
                                          args=(student, ))
                worker.start()

    def run_student(self, student):
        while True:
            start = time.time()

            observations = self._get_due_observations(student,
                                                      self.observations)
            if observations:
                logger.info("%s observations to send ids %s~%s",
                            len(observations),
                            observations[0]['id'],
                            observations[-1]['id'],
                            )

            for observation in observations:
                try:
                    self.send_one(student, observation)

                except requests.exceptions.Timeout:
                    logger.warning("Student timed out %s", student.email)
                    # Stop the block in case of timeouts
                    break

            now = int(time.time())
            window_end = student.last_window_end + self.window

            # Sending window observations took longer than the window
            if now > window_end:
                student.last_window_end = now
                student.save()
                logger.critical("Skipping values for student %s",
                                student.email)

            else:
                student.last_window_end = window_end
                student.save()

            logger.info("Runtime %s: %s",
                        student.email,
                        time.time() - start)

            if window_end >= self.simulator.end_time:
                logger.info("Student finished %s", student.email)
                break

            sleep_time = window_end - now
            if sleep_time < 0:
                sleep_time = 0

            logger.debug("Sleeping for %s", sleep_time)
            time.sleep(sleep_time)

    def send_one(self, student, observation):
        try:
            response = requests.post(
                self.endpoint.format(app_name=student.app),
                json=observation,
                timeout=self.timeout,
            )

        except requests.exceptions.Timeout as exc:
            models.Observation.create(
                timestamp=int(time.time()),
                simulator=self.simulator,
                student=student,
                observation_id=observation['id'],
                response_exception=str(exc),
                response_timeout=True,
            )
            raise

        except requests.exceptions.ConnectionError as exc:
            obj = models.Observation.create(
                timestamp=int(time.time()),
                simulator=self.simulator,
                student=student,
                observation_id=observation['id'],
                response_exception=str(exc),
            )
            return obj

        try:
            response.raise_for_status()

        except requests.exceptions.HTTPError as exc:
            logger.debug("Observation %s response status: %s",
                         observation['id'],
                         response.status_code)
            obj = models.Observation.create(
                timestamp=int(time.time()),
                simulator=self.simulator,
                student=student,
                observation_id=observation['id'],
                response_time=response.elapsed.total_seconds(),
                response_status=response.status_code,
                response_exception=str(exc),
            )
            return obj

        else:
            try:
                response.json()
                content = response.text

            except json.JSONDecodeError as exc:
                logger.debug("Observation %s response status: %s",
                             observation['id'],
                             response.status_code)
                logger.warning("JSON decode error %s %s",
                               student.email,
                               observation['id'])
                obj = models.Observation.create(
                    timestamp=int(time.time()),
                    simulator=self.simulator,
                    student=student,
                    observation_id=observation['id'],
                    response_time=response.elapsed.total_seconds(),
                    response_status=response.status_code,
                    response_exception=str(exc),
                )

            else:
                logger.debug("Observation %s response status: %s",
                             observation['id'],
                             response.status_code)
                obj = models.Observation.create(
                    timestamp=int(time.time()),
                    simulator=self.simulator,
                    student=student,
                    observation_id=observation['id'],
                    response_time=response.elapsed.total_seconds(),
                    response_status=response.status_code,
                    response_content=content,
                )

            return obj


class ObservationSimulator(Simulator):
    simulator_name = 'observation'
    endpoint = 'https://{app_name}.herokuapp.com/predict'
    filename = ['X_test_1.csv', 'X_test_2.csv']

    def __init__(self, *args, **kwargs):
        super().__init__(self.simulator_name, *args, **kwargs)

    def _load_observations(self):
        if isinstance(self.filename, (tuple, list)):
            df = pd.concat(
                [pd.read_csv(filename) for filename in self.filename])

        else:
            df = pd.read_csv(self.filename)

        observations = []
        for _, obs in df.iterrows():
            obs = obs.to_dict()
            _id = obs['id']
            del obs['id']
            observations.append({
                'id': _id,
                'observation': obs,
            })
        return observations


class TrueOutcomeSimulator(Simulator):
    simulator_name = 'true-outcome'
    endpoint = 'https://{app_name}.herokuapp.com/update'
    filename = 'y_test_1.csv'

    def __init__(self, *args, **kwargs):
        super().__init__(self.simulator_name, *args, **kwargs)

    def _load_observations(self):
        df = pd.read_csv(self.filename)
        observations = []
        for _, obs in df.iterrows():
            obs = obs.to_dict()
            observations.append({
                'id': obs['id'],
                'true_class': obs['true_outcome'],
            })
        return observations
