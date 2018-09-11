#!/usr/bin/env python3

import argparse
import csv

import models

parser = argparse.ArgumentParser()
parser.add_argument('filename')


if __name__ == '__main__':
    args = parser.parse_args()

    with open(args.filename) as handler:
        reader = csv.DictReader(handler)
        for row in reader:
            models.Student.get_or_create(
                email=row['email'],
                defaults={
                    'name': f"{row['first_name']} f{row['last_name']}",
                    'app': row['app'],
                }
            )
