import sys
import json
import argparse
import pandas as pd
from sklearn.metrics import roc_auc_score
from playhouse.shortcuts import model_to_dict

# import settings
import models

parser = argparse.ArgumentParser()
parser.add_argument(
    '-s', '--simulator_name', help='The simulator name', type=str,
    required=True,
)
parser.add_argument(
    '-o', '--output_filename', help='Where to write the scores to', type=str,
    required=True,
)

y_true = pd.concat(
    [
        pd.read_csv('datasets/y_test_1.csv'),
        pd.read_csv('datasets/y_test_2.csv')
    ]
).set_index(
    'id'
).true_outcome.sort_index()


def _parse_content(obs):
    if obs.response_exception or obs.response_timeout:
        return {1: 0, 0: 1}[y_true[obs.observation_id]]
    return json.loads(obs.response_content)['proba']


def _make_complete(observations):
    for _id in y_true.index.values:
        if _id not in observations:
            observations[_id] = {1: 0, 0: 1}[y_true[_id]]
    for _id in {9899, 4949}:
        observations.pop(_id, None)


def _validate(observations):
    diff = set(observations.keys()) - set(y_true.index.values)
    if diff:
        raise ValueError('Unexpected ids found {}'.format(diff))
    diff = set(y_true.index.values) - set(observations.keys())
    if diff:
        raise ValueError('Missing ids {}'.format(diff))


def _ping_console():
    sys.stdout.write('+')
    sys.stdout.flush()


def _score_student(student, simulator):
    _ping_console()
    observations = list(models.Observation.select().where(
        models.Observation.simulator == simulator,
        models.Observation.student == student,
        # models.Observation.response_status == 200
    ))
    observations = {
        obs.observation_id: _parse_content(obs)
        for obs in observations
    }
    _make_complete(observations)
    _validate(observations)
    # to make it a list and ensure that the order is correct
    y_score = [
        observations[_id] for _id in y_true.index.values
    ]
    return roc_auc_score(y_true, y_score)


def _score_students(simulator_name):
    simulator = models.Simulator.get(
        models.Simulator.name == simulator_name)
    return (
        (student, _score_student(student, simulator))
        for student in models.Student.select()
    )


def _score_and_write(simulator_name, output_filename):
    student_scores = pd.DataFrame([
        {**model_to_dict(student), 'score': score}
        for student, score in _score_students(simulator_name)
    ])
    student_scores = student_scores.drop('email', axis=1)
    student_scores.to_csv(output_filename, index=False)


if __name__ == '__main__':
    args = parser.parse_args()
    _score_and_write(args.simulator_name, args.output_filename)
