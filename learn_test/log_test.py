import logging
import os
from logging.config import dictConfig

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, 'log')
log_dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(module)s:%(funcName)s:%(lineno)d] [%(levelname)s] %(message)s',
        },
    },
    'handlers': {
        'learn_handler':{
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'filename': os.path.join(LOG_DIR, 'learn.log'),
            'formatter': 'standard',
        },
        'err_handler':{
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'filename': os.path.join(LOG_DIR, 'err.log'),
            'formatter': 'standard',
        },
    },
    'loggers': {
        'learn_logger':{
        'handlers': ['learn_handler'],
        'level': 'DEBUG',
        'propagate': True,
        },
        'err_logger':{
        'handlers': ['err_handler'],
        'level': 'DEBUG',
        'propagate': True,
        },
    }

}
dictConfig(log_dict)
def fun_tes():
    logger = logging.getLogger('err_logger')
    logger.info('log_test : 日志开启')
    logger.error('error to process hhhhhhmyw')
fun_tes()
