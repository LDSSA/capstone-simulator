

DATABASE = {
    'ENGINE': 'SqliteDatabase',
    'NAME': 'predictions.db',
}


# postgres example
# DATABASE = {
#     'ENGINE': 'PostgresqlDatabase',
#     'HOST': 'host',
#     'PORT': '5432',
#     'NAME': 'dbname',
#     'USER': 'username',
#     'PASSWORD': 'password',
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

