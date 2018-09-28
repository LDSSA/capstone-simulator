#!/usr/bin/env python3

import peewee

import models

if __name__ == '__main__':
    statuses = (
        models.Observation
        .select(
            models.Observation.student,
            models.Observation.response_status,
            peewee.fn.COUNT(models.Observation.student).alias('count')
        )
        .group_by(
            models.Observation.student,
            models.Observation.response_status,
        )
        .order_by(
            models.Observation.student,
            models.Observation.response_status,
        )
    )

    student = None
    for item in statuses:
        if student != item.student.email or student is None:
            print(f"# {item.student.email}")
            student = item.student.email
        print(f"    [{item.response_status}] {item.count}")



