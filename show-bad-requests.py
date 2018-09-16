import sys
import numpy.random

import settings
import models


simulator = models.Simulator.get(
    models.Simulator.name == sys.argv[1])


students = models.Student.select()


for student in students:
    bads = list(models.Observation.select().where(
        models.Observation.simulator == simulator,
        models.Observation.student == student,
        models.Observation.response_status < 200,
        models.Observation.response_status >= 300,
        ))
    bads.extend(list(models.Observation.select().where(
        models.Observation.simulator == simulator,
        models.Observation.student == student,
        models.Observation.response_status.is_null(),
        )))

    if bads:
        print('========================================================')
        print(student.email)
        max_choices = min(len(bads), 10)
        random_bads = numpy.random.choices(bads, size=max_choices)

        for observation in random_bads:
            msg = f"[{observation.observation_id}] "
            if observation.response_status:
                msg += f"Status: {observation.response_status} "
            if observation.response_timeout:
                msg += f"Timeout: {observation.response_timeout} "
            if observation.response_time:
                msg += f"Time: {observation.response_time} "
            if observation.response_content:
                msg += f"Content: {observation.response_content} "
            if observation.response_exception:
                msg += f"Exception: {observation.response_exception} "

            print(msg)
        print('\n\n\n\n')
