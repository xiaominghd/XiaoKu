# coding: utf-8
# Date 2021-03-11 10:44:21

import os
from datetime import date, datetime

def logging_conf(log_path):

    return {
        "loggers": {
            "data": {
                "level": "INFO",
                "propagate": False,
                "handlers": ["data", "console"]
            }
        },
        "disable_existing_loggers": False,
        "handlers": {
            "data": {
                "formatter": "simple",
                "backupCount": 20,
                "class": "logging.handlers.RotatingFileHandler",
                "maxBytes": 10485760,
                "filename": os.path.join(log_path, date.today().isoformat() + "_" + str(datetime.now().hour) + ".log"),
                "encoding": "utf-8"
            },
            "console": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout"
            }
        },
        "formatters": {
            "default": {
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "format": "%(asctime)s - %(levelname)s - %(module)s.%(name)s : %(message)s"
            },
            "simple": {
                "format": "%(asctime)s - %(levelname)s - %(message)s"
            },
            "mail": {
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "format": "%(asctime)s : %(message)s"
            }
        },
        "version": 1
    }
