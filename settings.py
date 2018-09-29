

DATABASE = {
    'ENGINE': 'SqliteDatabase',
    'NAME': 'predictions.db',
}


# DATABASE = {
#     'ENGINE': 'PostgresqlDatabase',
#     'HOST': 'capstone.cl9uj9cucww7.eu-west-1.rds.amazonaws.com',
#     'PORT': '5432',
#     'NAME': 'capstone',
#     'USER': 'root',
#     'PASSWORD': '',
# }


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': ('[%(levelname)s] %(threadName)s %(filename)s:%(lineno)d in '
                       '%(funcName)s %(message)s'),
        },
    },
    'handlers': {
        'default': {
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'level': 'INFO',
        },
        'file': {
            'formatter': 'standard',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': "my_log.log",
            'maxBytes': 10485760,
            'backupCount': 10,
        }
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': True
        },
        'simulator': {
            'handlers': ['default', 'file'],
            'level': 'DEBUG',
            'propagate': False
        },
    }
}

import logging.config
logging.config.dictConfig(LOGGING)

