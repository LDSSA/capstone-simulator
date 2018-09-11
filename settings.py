

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
            'format': ('[%(levelname)s] %(filename)s:%(lineno)d in '
                       '%(funcName)s %(message)s'),
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'DEBUF',
            'propagate': True
        },
    }
}

import logging.config
logging.config.dictConfig(LOGGING)

