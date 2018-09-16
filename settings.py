

DATABASE = {
    'ENGINE': 'SqliteDatabase',
    'NAME': 'predictions.db',
}


#DATABASE = {
#    'ENGINE': 'PostgresqlDatabase',
#    'HOST': '',
#    'PORT': '',
#    'NAME': '',
#    'USER': '',
#    'PASSWORD': '',
#}


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
        },
        'file': {
            'formatter': 'standard',
            'class': 'logging.RotatingFileHandler',
            'filename': "my_log.log",
            'maxBytes': 2048,
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

