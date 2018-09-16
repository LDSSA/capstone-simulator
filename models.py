import peewee

import settings

engine = getattr(peewee, settings.DATABASE['ENGINE'])
params = ('user', 'password', 'host', 'port')
kwargs = {param: settings.DATABASE.get(param.upper()) for param in params
          if param.upper() in settings.DATABASE}
db = engine(settings.DATABASE['NAME'], **kwargs)


class Simulator(peewee.Model):
    name = peewee.CharField(index=True)
    start_time = peewee.IntegerField()  # Start ts for the simulator
    end_time = peewee.IntegerField()  # Timestamp by which the sim ends

    class Meta:
        database = db


class Student(peewee.Model):
    email = peewee.CharField(index=True)
    name = peewee.CharField()
    app = peewee.CharField(null=True)

    # End of last sent time-window
    last_window_end = peewee.IntegerField(null=True)

    class Meta:
        database = db


class Observation(peewee.Model):
    timestamp = peewee.IntegerField()
    simulator = peewee.ForeignKeyField(Simulator, backref='observations')
    student = peewee.ForeignKeyField(Student, backref='students')
    observation_id = peewee.IntegerField()

    response_time = peewee.FloatField(null=True)
    response_status = peewee.IntegerField(null=True)
    response_content = peewee.CharField(null=True)
    response_exception = peewee.CharField(null=True)
    response_timeout = peewee.BooleanField(default=False)

    class Meta:
        database = db


db.connect()
db.create_tables([Simulator, Student, Observation], safe=True)